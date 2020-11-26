import datetime
import logging
import traceback

from django.db.models import F
from django.shortcuts import render
from django_filters import rest_framework
from django_redis import get_redis_connection
from redis import StrictRedis

from rest_framework import viewsets, status, filters

# Create your views here.
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from config.models import GoodsCategory
from demand.models import VideoNeeded
from demand.serializers import VideoNeededSerializer, ClientVideoNeededSerializer
from libs.common.permission import ManagerPermission, AdminPermission, AllowAny
from libs.pagination import StandardResultsSetPagination
from libs.parser import JsonParser, Argument
from libs.services import check_link_and_get_data, CheckLinkError, CheckLinkRequestError
from users.models import Address

logger = logging.getLogger()
conn = get_redis_connection('default')  # type: StrictRedis


class VideoNeededViewSet(viewsets.ModelViewSet):
    permission_classes = ManagerPermission
    serializer_class = VideoNeededSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = ('status',)

    def get_queryset(self):
        self.queryset = VideoNeeded.objects.filter(uid=self.request.user)
        return self.queryset

    def update(self, request, *args, **kwargs):
        return Response({"detail": "请使用patch"}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.uid != self.request.user:
            return Response({"detail": "找不到这个订单"}, status=status.HTTP_400_BAD_REQUEST)
        if instance.status != VideoNeeded.TO_PUBLISH:
            return Response({"detail": "不是待发布的订单"}, status=status.HTTP_400_BAD_REQUEST)
        form, error = JsonParser(
            Argument('category', help='请输入 category(商品品类id)', type=int,
                     required=False,
                     filter=lambda x: GoodsCategory.objects.filter(id=x).exists(),
                     handler=lambda x: GoodsCategory.objects.get(id=x).title),
            Argument('address', type=int, help='请输入 address(收货地址)',
                     required=False,
                     filter=lambda x: Address.objects.filter(id=x, uid=request.user).exists(),
                     handler=lambda x: Address.objects.get(id=x)),
            Argument('status', required=False, filter=lambda x: x is None, help="修改的时候不能改状态, 要调用接口")
        ).parse(request.data, clear=True)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        if 'category' in form:
            request.data['category'] = form.category
        if 'address' in form:
            request.data['receiver_name'] = form.address.name
            request.data['receiver_phone'] = form.address.phone
            request.data['receiver_province'] = form.address.province
            request.data['receiver_city'] = form.address.city
            request.data['receiver_district'] = form.address.district
            request.data['receiver_location'] = form.address.location
            request.data.pop('address')
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        form, error = JsonParser(
            Argument('title', help='请输入 title(标题)'),
            Argument('industries', help='请输入 industries(行业)'),
            Argument('attraction', help='请输入 attraction(商品卖点)'),
            Argument('num_needed', help='请输入 num_needed(拍摄视频数)'),
            Argument('is_return', type=bool, help='请输入 is_return(是否返样)'),
            Argument('video_size', type=int, help='请输入 video_size(尺寸)'),
            Argument('clarity', type=int, help='请输入 clarity(清晰度'),
            Argument('model_needed', type=int, help='请输入 model_needed(模特出镜)'),
            Argument('model_occur_rate', type=int, help='请输入 model_occur_rate(模特出境比例)'),
            Argument('model_age_range', type=int, help='请输入 model_age_range(模特年龄)'),
            Argument('model_figure', type=int, help='请输入 model_figure(模特身材)'),
            Argument('desc', type=str, required=False, help='请输入 desc(其他说明)'),
            Argument('example1', type=str, required=False, help='请输入 example1(参考视频1)'),
            Argument('example2', type=str, required=False, help='请输入 example2(参考视频2)'),
            Argument('example3', type=str, required=False, help='请输入 example3(参考视频3)'),
            # Argument('goods_images', help='请输入 goods_images(商品商品主图)'),
            Argument('action', type=int, help='请输入 action(发布操作 0/1)'),
            Argument('goods_link', help='请输入 goods_link(商品链接)', handler=lambda x: x.strip()),
            Argument('category', help='请输入 category(商品品类id)', type=int,
                     filter=lambda x: GoodsCategory.objects.filter(id=x).exists()),
            Argument('address', type=int, help='请输入 address(收货地址)',
                     required=lambda x: x.get('is_return') is True,
                     filter=lambda x: Address.objects.filter(id=x, uid=request.user).exists(),
                     handler=lambda x: Address.objects.get(id=x)),
        ).parse(request.data, clear=True)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

        hash_key = form.goods_link.__hash__()
        link_key = f'check_link_{hash_key}'
        if not conn.exists(link_key):
            return Response({"detail": "该商品链接没有经过校验, 请先校验！"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            images_key = f'images_{hash_key}'
            channel_key = f'channel_{hash_key}'
            form['goods_images'] = conn.get(images_key).decode('utf-8')
            form['goods_channel'] = conn.get(channel_key).decode('utf-8')

        if 'address' in form:
            form['receiver_name'] = form.address.name
            form['receiver_phone'] = form.address.phone
            form['receiver_province'] = form.address.province
            form['receiver_city'] = form.address.city
            form['receiver_district'] = form.address.district
            form['receiver_location'] = form.address.location
            form.pop('address')
        if form.action == 0:
            form['status'] = VideoNeeded.TO_PUBLISH
        elif form.action == 1:
            form['status'] = VideoNeeded.TO_CHECK
            form['publish_time'] = datetime.datetime.now()
        form.pop('action')
        form['num_remained'] = form.num_needed
        conn.delete(link_key)
        instance = VideoNeeded.objects.create(**form)
        serializer = self.get_serializer(instance)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.uid != self.request.user:
            return Response({"detail": "找不到这个订单"}, status=status.HTTP_400_BAD_REQUEST)
        if instance.status != VideoNeeded.TO_PUBLISH:
            return Response({"detail": "不是待发布的订单"}, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

    @action(methods=['post', ], detail=True, permission_classes=[ManagerPermission])
    def publish(self, request, **kwargs):
        instance = self.get_object()
        if instance.uid != self.request.user:
            return Response({"detail": "找不到这个订单"}, status=status.HTTP_400_BAD_REQUEST)
        form, error = JsonParser(
            Argument('action', type=int, filter=lambda x: x in [0, 1], help="action: 发布0/下架1")
        ).parse(request.data)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        if form.action == 0:
            if instance.status != VideoNeeded.TO_PUBLISH:
                return Response({"detail": "不是待发布的订单"}, status=status.HTTP_400_BAD_REQUEST)
            instance.status = VideoNeeded.TO_CHECK
            instance.publish_time = datetime.datetime.now()
            instance.save()
            return Response({"detail": "以发布, 待审核中"}, status=status.HTTP_200_OK)
        else:
            if instance.status not in [VideoNeeded.TO_CHECK, VideoNeeded.ON_GOING]:
                return Response({"detail": "不需要下架的订单"}, status=status.HTTP_400_BAD_REQUEST)
            instance.status = VideoNeeded.TO_PUBLISH
            instance.non_publish_time = datetime.datetime.now()
            instance.save()
            return Response({"detail": "已经下架"}, status=status.HTTP_200_OK)

    @action(methods=['post', ], detail=True, permission_classes=[ManagerPermission])
    def check_link(self, request, **kwargs):
        form, error = JsonParser(
            Argument('goods_link', help='请输入 goods_link(商品链接)', handler=lambda x: x.strip()),
        )
        try:
            data = check_link_and_get_data(form.goods_link)
            if data == 444:
                return Response({'detail': '抱歉，该商品不是淘宝联盟商品'}, status=status.HTTP_400_BAD_REQUEST)
            hash_key = form.goods_link.__hash__()
            link_key = f'check_link_{hash_key}'
            images_key = f'images_{hash_key}'
            channel_key = f'channel_{hash_key}'
            channel_value = data.get('chanel', None)
            images_value = data.get('itempic', None)
            if not images_value or not channel_value:
                logger.info(data)
                return Response({"detail": "抱歉, 无法获取该商品来源以及图片, 校验不通过"}, status=status.HTTP_400_BAD_REQUEST)
            conn.set(link_key, 'link_ok')
            conn.set(images_key, images_value)
            conn.set(channel_key, channel_value)
            return Response(data, status=status.HTTP_200_OK)
        except CheckLinkError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except CheckLinkRequestError as e:
            return Response({'detail': str(e), 'code': 123}, status=status.HTTP_400_BAD_REQUEST)
        except:
            logger.info(traceback.format_exc())
            return Response({"detail": "校验接口报错了，请联系技术人员解决"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ManageVideoNeededViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = AdminPermission
    serializer_class = VideoNeededSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('uid__username',)
    filter_fields = ('status',)

    def get_queryset(self):
        return VideoNeeded.objects.all()

    @action(methods=['post', ], detail=True, permission_classes=[AdminPermission])
    def check(self, request, **kwargs):
        form, error = JsonParser(
            Argument('action', filter=lambda x: x in ['pass', 'reject'], help="请输入action(操作) e.pass/reject"),
            Argument('video_slice', type=list,
                     handler=lambda x: sorted([{int(i): 1} for i in x], key=lambda i: list(i.keys())[0]),
                     required=lambda rst: rst.get('action') == 'pass', help="请输入slice(视频切片数组) e.[10, 10, 20]"),
            Argument('slice_num', type=int, required=lambda rst: rst.get('action') == 'pass',
                     help="请输入slice_num(切片数) e. 10"),
            Argument('reject_reason', required=lambda rst: rst.get('action') == 'reject', help="请输入拒绝理由"),
        ).parse(request.data)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        instance = self.get_object()
        if instance.status != VideoNeeded.TO_CHECK:
            return Response({"detail": "订单状态不是待审核状态, 无法操作"}, status=status.HTTP_400_BAD_REQUEST)
        if form.action == 'reject':
            instance.status = VideoNeeded.TO_PUBLISH
            reject_reason = f"{form.reject_reason}\n需求已改成未发布, 可重新编辑发布,再次审核."
            instance.reject_reason = reject_reason
            instance.save()
            return Response({"detail": "已拒绝"}, status=status.HTTP_200_OK)
        else:
            if len(form.video_slice) != form.slice_num:
                return Response({"detail": "视频分片个数和订单总分片数不一致"}, status=status.HTTP_400_BAD_REQUEST)
            instance.status = VideoNeeded.ON_GOING
            instance.video_slice = form.video_slice
            instance.slice_num = form.slice_num
            instance.save()
            return Response({"detail": "已审核通过, 需求将展示于可申请的需求列表中"}, status=status.HTTP_200_OK)


class ClientVideoNeededViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = AdminPermission
    serializer_class = ClientVideoNeededSerializer
    queryset = VideoNeeded.objects.filter(status=VideoNeeded.ON_GOING)
    pagination_class = StandardResultsSetPagination
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title',)
    filter_fields = ('status', 'category', 'is_return',)

    def get_queryset(self):
        self.queryset = self.queryset.order_by('-create_time')
        recommend = self.request.query_params.get('recommend', None)
        # if str(recommend) == '1':
        #     self.queryset = VideoNeeded.objects.annotate(
        #         remained_order=F('slice_num')-F('applied_num')
        #     ).filter(rema)
        return self.queryset


class test(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = check_link_and_get_data(request.data.get('goods_link').strip())
        return Response(data, status=status.HTTP_200_OK)
