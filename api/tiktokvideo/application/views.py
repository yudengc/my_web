import datetime
import json
import logging

from django.db.models import Sum
from django.db.transaction import atomic
from qiniu import Auth
from rest_framework import viewsets, status, mixins, filters, exceptions
from django_filters import rest_framework
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from application.filters import VideoApplicationManagerFilter
from application.models import VideoOrder, Video, VideoOrderDetail
from application.serializers import VideoApplicationCreateSerializer, VideoApplicationListSerializer, \
    VideoApplicationRetrieveSerializer, BusApplicationSerializer, VideoApplicationManagerListSerializer, \
    VideoApplicationManagerRetrieveSerializer, VideoOrderDetailSerializer
from demand.models import VideoNeeded
from libs.common.permission import CreatorPermission, AdminPermission, BusinessPermission, ManagerPermission
from libs.parser import Argument, JsonParser
from users.models import Address, Users, UserCreator

logger = logging.getLogger()


class VideoApplicationViewSet(mixins.CreateModelMixin,
                              mixins.RetrieveModelMixin,
                              mixins.UpdateModelMixin,
                              mixins.ListModelMixin,
                              GenericViewSet):
    permission_classes = (CreatorPermission,)
    queryset = VideoOrder.objects.all()
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = ('status',)

    def get_serializer_class(self):
        if self.action == 'create':
            self.serializer_class = VideoApplicationCreateSerializer
        elif self.action == 'list':
            self.serializer_class = VideoApplicationListSerializer
        elif self.action == 'retrieve':
            self.serializer_class = VideoApplicationRetrieveSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.action in ['list', 'retrieve']:
            self.queryset = self.queryset.filter(user=self.request.user).select_related('demand', 'video_order_detail')
        return super().get_queryset()

    def create(self, request, *args, **kwargs):
        user = request.user
        if not request.data['num_selected'] or not request.data['demand'] or not request.data['address']:
            return Response({'detail': '参数缺失！'}, status=status.HTTP_400_BAD_REQUEST)
        if VideoOrder.objects.filter(user=user, demand_id=request.data['demand']).exists():
            return Response({'detail': '你已经领取过该需求了哦'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.user_creator.is_signed:  # 非签约团队有视频数限制（5个）
            video_sum = VideoOrder.objects.filter(user=user).exclude(status=VideoOrder.DONE).aggregate(
                sum=Sum('num_selected'))['sum']  # 进行中的视频数
            if not video_sum:
                video_sum = 0
            if request.data['num_selected'] > 5 - video_sum:
                return Response({'detail': '可拍摄视频数不足'}, status=status.HTTP_400_BAD_REQUEST)

        need_obj = VideoNeeded.objects.get(id=request.data['demand'])
        order_video_slice = need_obj.order_video_slice
        # e. [{'num': 10, 'remain': 1}, {'num': 20, 'remain': 1}]
        request.data['is_return'] = need_obj.is_return
        request.data['user'] = user.uid
        request.data['reward'] = user.user_creator.contract_reward  # 每条视频的酬劳

        try:
            add_obj = Address.objects.get(id=request.data['address'])
        except Address.DoesNotExist:
            return Response({'detail': '所选地址不存在'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 判断可选的视频数是否被领了（怕在用户填信息时被其他用户领了）
        try:
            with atomic():
                # 订单过程中需维护VideoNeeded的3个字段: order_video_slice, order_num_remained, video_num_remained
                slice_idx = order_video_slice.index({'num': request.data['num_selected'], 'remain': 1})
                need_obj.order_video_slice[slice_idx]['remain'] = 0
                need_obj.order_num_remained -= 1
                need_obj.video_num_remained -= request.data['num_selected']
                need_obj.save()

                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                VideoOrderDetail.objects.create(video_order_id=serializer.data['id'],
                                                goods_title=need_obj.goods_title,
                                                goods_link=need_obj.goods_link,
                                                goods_channel=need_obj.goods_channel,
                                                goods_images=need_obj.goods_images,
                                                category=need_obj.category,
                                                receiver_name=add_obj.name,
                                                receiver_phone=add_obj.phone,
                                                receiver_province=add_obj.province,
                                                receiver_city=add_obj.city,
                                                receiver_district=add_obj.district,
                                                receiver_location=add_obj.location,
                                                return_receiver_name=need_obj.receiver_name,
                                                return_receiver_phone=need_obj.receiver_phone,
                                                return_receiver_province=need_obj.receiver_province,
                                                return_receiver_city=need_obj.receiver_city,
                                                return_receiver_district=need_obj.receiver_district,
                                                return_receiver_location=need_obj.receiver_location,
                                                )
        except ValueError:
            return Response({'detail': '哎呀呀，您选择的拍摄视频数已被选走，请重选选择'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.info(f'{user.username}创建订单失败了！！！！！！！！！')
            logger.info(e)
            return Response({'detail': '哎呀呀，领取失败了，请重试或联系管理员'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(methods=['put'], detail=True)
    def upload_video(self, request):
        """提交视频"""
        video_lis = request.data.get('video_url_arr')
        order_obj = self.get_object()
        if order_obj.status != VideoOrder.WAIT_COMMIT:
            logger.info(f'该订单状态不是待提交状态, 订单号:{order_obj.order_number}')
            return Response({'detail': '非待提交状态不能提交视频'}, status=status.HTTP_400_BAD_REQUEST)

        if order_obj.num_selected != len(video_lis):
            return Response({'detail': f'请上传{order_obj.num_selected}个视频'}, status=status.HTTP_400_BAD_REQUEST)
        id_lis = []

        for video_url in video_lis:
            obj = Video.objects.create(video_url=video_url)
            id_lis.append(obj.id)
        try:
            with atomic():
                order_obj.order_video.set(id_lis)
                order_obj.status = VideoOrder.WAIT_CHECK
                order_obj.save()
        except Exception as e:
            logger.info(f'创作者提交视频失败！！！！！！！！！！！！！！！！！！ 订单号:{order_obj.order_number}')
            logger.info(e)
            return Response({'detail': '提交失败，请再次尝试或联系客服'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': '提交成功'})

    @action(methods=['put'], detail=True)
    def input_logistics_info(self, request):
        """填写返样快递信息"""
        order_obj = self.get_object()
        return_company = request.data.get('return_company')
        return_express = request.data.get('return_express')
        if not return_company or not return_express:
            return Response({'detail': '请填写完整的快递信息'}, status=status.HTTP_400_BAD_REQUEST)
        if order_obj.status != VideoOrder.WAIT_RETURN:
            logger.info(f'该订单状态不是待返样状态, 订单号:{order_obj.order_number}')
            return Response({'detail': '该订单状态不是待返样状态'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with atomic():
                detail_obj = order_obj.video_order_detail
                detail_obj.return_company = return_company
                detail_obj.return_express = return_express
                detail_obj.save()

                order_obj.status = VideoOrder.DONE
                order_obj.save()
        except Exception as e:
            logger.info(f'创作者提交返样快递信息失败！！！！！！！！！！！！！！！！！！ 订单号:{order_obj.order_number}')
            logger.info(e)
            return Response({'detail': '提交失败，请再次尝试或联系客服。'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': '提交成功'})

    @action(methods=['get'], detail=False)
    def order_status_count(self, request):
        order_qs = VideoOrder.objects.filter(user=request.user)
        data = dict(wait_send=order_qs.filter(status=VideoOrder.WAIT_SEND).count(),
                    wait_commit=order_qs.filter(status=VideoOrder.WAIT_COMMIT).count(),
                    wait_check=order_qs.filter(status=VideoOrder.WAIT_CHECK).count(),
                    wait_return=order_qs.filter(status=VideoOrder.WAIT_RETURN).count())
        return Response(data)


class BusVideoOrderViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [BusinessPermission,]
    serializer_class = BusApplicationSerializer
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filters = ('status',)

    def get_queryset(self):
        return VideoOrder.objects.filter(demand__uid=self.request.user)

    # def get_serializer_class(self):
    #     if self.action in ['retrieve', ]:
    #         return VideoApplicationRetrieveSerializer
    #     else:
    #         return BusVideoOrderSerializer

    @action(methods=['post', ], detail=True, permission_classes=[ManagerPermission])
    def commit_express(self, request, **kwargs):
        form, error = JsonParser(
            Argument('express', type=str, help="请输入 express(快递单号)"),
            Argument('company', type=str, help="请输入 company(物流公司)"),
        ).parse(request.data)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        instance = self.get_object()
        if instance.demand.uid != self.request.user:
            return Response({"detail": "订单错误, 无法提交快递单号"}, status=status.HTTP_400_BAD_REQUEST)
        if instance.status != VideoOrder.WAIT_SEND:
            return Response({"detail": "订单不是待发货状态, 无法提交快递单号"}, status=status.HTTP_400_BAD_REQUEST)
        instance.express = form.express
        instance.company = form.company
        instance.status = VideoOrder.WAIT_CHECK
        instance.send_time = datetime.datetime.now()
        instance.save()
        return Response({"detail": "已提交成功"}, status=status.HTTP_200_OK)

    @action(methods=['get', ], detail=False, permission_classes=[ManagerPermission])
    def video_order_status(self, request, **kwargs):
        data = dict(wait_send=VideoOrder.objects.filter(demand__uid=request.user, status=0).count(),
                    wait_commit=VideoOrder.objects.filter(demand__uid=request.user, status=1).count(),
                    wait_return=VideoOrder.objects.filter(demand__uid=request.user, status=4).count(),
                    done=VideoOrder.objects.filter(demand__uid=request.user, status=5).count())
        return Response(data, status=status.HTTP_200_OK)


class VideoApplicationManagerViewSet(mixins.CreateModelMixin,
                                     mixins.RetrieveModelMixin,
                                     mixins.UpdateModelMixin,
                                     mixins.ListModelMixin,
                                     GenericViewSet):
    """需求订单后台管理"""
    permission_classes = (CreatorPermission,)
    queryset = VideoOrder.objects.all()
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = VideoApplicationManagerFilter
    search_fields = ('demand__title', 'demand__uid__username', 'demand__uid__user_business__bus_name',
                     'user__auth_base__nickname', 'user__username')

    def get_serializer_class(self):
        if self.action == 'list':
            self.serializer_class = VideoApplicationManagerListSerializer
        elif self.action == 'retrieve':
            self.serializer_class = VideoApplicationManagerRetrieveSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.action == 'retrieve':
            self.queryset = VideoOrder.objects.select_related('video_order_detail')
        return super().get_queryset()

    def create(self, request, *args, **kwargs):
        """批量创建订单"""
        data = request.data
        # try:
        #     add_obj = Address.objects.get(id=data.get('address'))
        # except Address.DoesNotExist:
        #     return Response({'detail': '所选地址不存在'}, status=status.HTTP_400_BAD_REQUEST)

        contract_reward = data.get('contract_reward', None)  # 单个视频交付松子币
        if contract_reward is None:
            try:
                contract_reward = UserCreator.objects.get(uid__uid=data.get('user')).contract_reward
            except UserCreator.DoesNotExist:
                contract_reward = 0

        success = len(data.get('demand_lis'))
        fail = 0
        fail_reason = ''
        # 数据格式：demand_lis: [{"demand": 1, "num_selected": 5}, {"demand": 2, "num_selected": 10}]
        for dic in data.get('demand_lis'):
            need_obj = VideoNeeded.objects.get(id=dic['demand'])
            if VideoOrder.objects.filter(user__uid=data.get('user'),
                                         demand=need_obj).exists():
                fail += 1
                success -= 1
                fail_reason += f"该用户已经存在需求标题为（{need_obj.title}）的订单。\n"
                logger.info(f"{data.get('user')}的用户已经领取过id为：{dic['demand']}的订单")
                continue
            try:
                with atomic():
                    slice_idx = need_obj.order_video_slice.index({'num': dic['num_selected'], 'remain': 1})
                    need_obj.order_video_slice[slice_idx]['remain'] = 0
                    need_obj.order_num_remained -= 1
                    need_obj.video_num_remained -= dic['num_selected']
                    need_obj.save()
                    order_obj = VideoOrder.objects.create(status=VideoOrder.WAIT_SEND,
                                                          user_id=data.get('user'),
                                                          demand=need_obj,
                                                          num_selected=dic['num_selected'],
                                                          sample_count=data.get('sample_count'),
                                                          is_return=need_obj.is_return,
                                                          reward=contract_reward,
                                                          creator_remark=data.get('creator_remark'),
                                                          system_remark='后台系统派单'
                                                          )
                    VideoOrderDetail.objects.create(video_order=order_obj,
                                                    goods_title=need_obj.goods_title,
                                                    goods_link=need_obj.goods_link,
                                                    goods_channel=need_obj.goods_channel,
                                                    goods_images=need_obj.goods_images,
                                                    category=need_obj.category,
                                                    receiver_name=request.data.get('receiver_name'),
                                                    receiver_phone=request.data.get('receiver_phone'),
                                                    receiver_location=request.data.get('receiver_location'),
                                                    return_receiver_name=need_obj.receiver_name,
                                                    return_receiver_phone=need_obj.receiver_phone,
                                                    # return_receiver_province=need_obj.receiver_province,
                                                    # return_receiver_city=need_obj.receiver_city,
                                                    # return_receiver_district=need_obj.receiver_district,
                                                    return_receiver_location=need_obj.receiver_province +
                                                    need_obj.receiver_city + need_obj.receiver_district +
                                                    need_obj.receiver_location,
                                                    )
            except ValueError:
                fail += 1
                success -= 1
                fail_reason += f'({need_obj.title})选择的拍摄数{dic["num_selected"]}已被领取了。\n'
                continue
            except Exception as e:
                fail += 1
                success -= 1
                fail_reason += f'({need_obj.title})创建失败。\n'
                logger.info('批量创建订单失败')
                logger.info(e)
                print(e)
                continue
        msg = f'添加成功:{success}个\n添加失败:{fail}个\n'
        if fail_reason:
            fail_reason = '失败原因：' + fail_reason
            msg += fail_reason
        return Response({'detail': msg}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        demand_id = request.data.get('demand')
        creator_id = request.data.get('creator')
        reward = request.data.get('reward')
        address_id = request.data.get('address')
        order_status = request.data.get('status')
        creator_remark = request.data.get('creator_remark')
        company = request.data.get('company')
        express = request.data.get('express')
        video_id_lis = request.data.get('video')
        remark = request.data.get('remark')
        form, error = JsonParser(
            Argument('demand', help="请选择需求!!"),
            Argument('creator', help="请选择创作者!!"),
            Argument('reward', help="请输入单视频交付金额!!"),
            Argument('address', help="请选择收货信息!!"),
            Argument('status', help="请选择订单状态!!"),
        ).parse(request.data)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        if creator_remark is None:
            return Response({"detail": 'creator_remark缺失'}, status=status.HTTP_400_BAD_REQUEST)
        if company is None:
            return Response({"detail": 'company缺失'}, status=status.HTTP_400_BAD_REQUEST)
        if express is None:
            return Response({"detail": 'express缺失'}, status=status.HTTP_400_BAD_REQUEST)
        if video_id_lis is None:
            return Response({"detail": 'video_lis缺失'}, status=status.HTTP_400_BAD_REQUEST)
        if remark is None:
            return Response({"detail": 'remark缺失'}, status=status.HTTP_400_BAD_REQUEST)

        instance = self.get_object()
        try:
            with atomic():
                detail_obj = instance.video_order_detail
                instance.reward = reward
                instance.status = order_status
                instance.creator_remark = creator_remark
                instance.remark = remark
                if instance.user.id != creator_id:
                    instance.user = Users.objects.get(id=creator_id)
                if instance.demand.id != demand_id:
                    need_obj = VideoNeeded.objects.get(id=demand_id)
                    instance.demand = need_obj
                    detail_obj.goods_title = need_obj.goods_title
                    detail_obj.goods_link = need_obj.goods_link
                    detail_obj.goods_channel = need_obj.goods_channel
                    detail_obj.goods_images = need_obj.goods_images
                    detail_obj.category = need_obj.category
                    detail_obj.return_receiver_name = need_obj.receiver_name
                    detail_obj.return_receiver_phone = need_obj.receiver_phone
                    detail_obj.return_receiver_province = need_obj.receiver_province
                    detail_obj.return_receiver_city = need_obj.receiver_city
                    detail_obj.return_receiver_district = need_obj.receiver_district
                    detail_obj.return_receiver_location = need_obj.receiver_location
                add_obj = Address.objects.get(id=address_id)
                detail_obj.receiver_name = add_obj.name
                detail_obj.receiver_phone = add_obj.phone
                detail_obj.receiver_province = add_obj.province
                detail_obj.receiver_city = add_obj.city
                detail_obj.receiver_district = add_obj.district
                detail_obj.receiver_location = add_obj.location
                instance.save()
                detail_obj.save()
                instance.order_video.set(video_id_lis)
        except Exception as e:
            logger.info('后台订单编辑失败')
            logger.info(e)
            print(e)
            return Response({'detail': '修改失败'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': '修改成功'})


class VideoCountView(APIView):
    """正在拍摄视频数和可拍摄视频数"""
    permission_classes = (CreatorPermission,)

    def get(self, request):
        try:
            obj = UserCreator.objects.get(uid=request.user)
        except UserCreator.DoesNotExist:
            obj = UserCreator.objects.create(uid=request.user)
        total = VideoOrder.objects.exclude(status=VideoOrder.DONE).aggregate(sum=Sum('num_selected'))['sum']
        if not total:
            total = 0
        return Response({'ongoing': total, 'Remaining': 5-total if not obj.is_signed else '不限制'})


class VideoOrderDetailViewSet(viewsets.ReadOnlyModelViewSet):
    """客户端订单统计明细"""
    permission_classes = [CreatorPermission]
    serializer_class = VideoOrderDetailSerializer
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)

    def get_queryset(self):
        if self.action == 'list':
            month = self.request.query_params.get('month')
            year = self.request.query_params.get('year')
            if not month:
                raise exceptions.ParseError('缺少month')
            if not year:
                raise exceptions.ParseError('缺少year')
            self.queryset = VideoOrder.objects.filter(user=self.request.user,
                                                      done_time__month=month,
                                                      done_time__year=year).order_by('-done_time')
        else:
            self.queryset = VideoOrder.objects.all()
        return super().get_queryset()

