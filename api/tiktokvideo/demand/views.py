import datetime
import json
import logging
import time
import traceback

from django.db.transaction import atomic
from django_filters import rest_framework
from django_redis import get_redis_connection
from redis import StrictRedis

from rest_framework import viewsets, status, filters, exceptions

# Create your views here.
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from config.models import GoodsCategory
from demand.filters import ManageVideoNeededFilter, ManageHomePageVideoFilter
from demand.models import VideoNeeded, HomePageVideo
from demand.serializers import VideoNeededSerializer, ClientVideoNeededSerializer, ClientVideoNeededDetailSerializer, \
    HomePageVideoSerializer, ManageVideoNeededSerializer
from flow_limiter.services import FlowLimiter
from libs.common.permission import ManagerPermission, AdminPermission, AllowAny
from libs.pagination import StandardResultsSetPagination
from libs.parser import JsonParser, Argument
from libs.services import check_link_and_get_data, CheckLinkError, CheckLinkRequestError
from transaction.models import UserPackageRelation
from users.models import Address

logger = logging.getLogger()
conn = get_redis_connection('default')  # type: StrictRedis


class VideoNeededViewSet(viewsets.ModelViewSet):
    permission_classes = [ManagerPermission]
    serializer_class = VideoNeededSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = ('status',)

    def get_queryset(self):
        self.queryset = VideoNeeded.objects.filter(uid=self.request.user)
        return self.queryset

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.uid != self.request.user:
            return Response({"detail": "找不到这个订单"}, status=status.HTTP_400_BAD_REQUEST)
        form, error = JsonParser(
            Argument('category', help='请输入 category(商品品类id)', type=int,
                     required=False,
                     filter=lambda x: GoodsCategory.objects.filter(id=x).exists()),
            Argument('address', type=int, help='请输入 address(收货地址)',
                     required=False,
                     filter=lambda x: Address.objects.filter(id=x, uid=request.user).exists(),
                     handler=lambda x: Address.objects.get(id=x)),
            Argument('goods_link', required=False, help='请输入 goods_link(商品链接)', handler=lambda x: x.strip()),
            Argument('video_num_remained', required=False, type=int, help="请输入 video_num_remained(整型)"),
            Argument('status', required=False, filter=lambda x: x in [u'', '', None], help="修改的时候不能改状态, 要调用接口"),
            Argument('receiver_name', required=False, filter=lambda x: x in [u'', '', None], help="修改地址传address"),
            Argument('receiver_phone', required=False, filter=lambda x: x in [u'', '', None], help="修改地址传address"),
            Argument('receiver_province', required=False, filter=lambda x: x in [u'', '', None], help="修改地址传address"),
            Argument('receiver_city', required=False, filter=lambda x: x in [u'', '', None], help="修改地址传address"),
            Argument('receiver_district', required=False, filter=lambda x: x in [u'', '', None], help="修改地址传address"),
            Argument('receiver_location', required=False, filter=lambda x: x in [u'', '', None], help="修改地址传address"),
        ).parse(request.data, clear=True)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        if 'video_num_needed' in request.data:
            request.data.pop('video_num_needed')  # 不能改总数, 默认还是原来的
        if 'address' in form:
            request.data['receiver_name'] = form.address.name
            request.data['receiver_phone'] = form.address.phone
            request.data['receiver_province'] = form.address.province
            request.data['receiver_city'] = form.address.city
            request.data['receiver_district'] = form.address.district
            request.data['receiver_location'] = form.address.location
            request.data.pop('address')

        # init key
        title_key, channel_key, images_key = [''] * 3
        if 'goods_link' in form:
            hash_key = hash(form.goods_link)
            original_hash_key = hash(instance.goods_link)
            if hash_key != original_hash_key:
                form['goods_title'], form['goods_images'], form['goods_channel'] = self.validate_goods_data(
                    form.goods_link)

        with atomic():
            reduce = 0
            flag = 0
            if 'video_num_remained' in form:
                reduce = instance.video_num_remained - form.video_num_remained
                if reduce < 0:
                    return Response({"detail": "修改剩余数不能大于现在的哦"}, status=status.HTTP_400_BAD_REQUEST)
                instance.video_num_needed -= reduce
                instance.save()
            if instance.status in [VideoNeeded.TO_CHECK, VideoNeeded.ON_GOING]:
                # 进行中/审核中的需求编辑后要重新 待审核
                user_business = self.request.user.user_business
                user_business.remain_video_num += reduce
                user_business.save()
                flag = 1
                request.data['status'] = VideoNeeded.TO_CHECK
                request.data['non_publish_time'] = datetime.datetime.now()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            if 'goods_link' in form:
                conn.delete(title_key, channel_key, images_key)
            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}
            if flag == 1:
                return Response({"detail": "修改成功, 已重新发起审核, 待运营审核通过后即可上线"}, status=status.HTTP_200_OK)
            return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        return Response({"detail": "请使用put"}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        form, error = JsonParser(
            Argument('title', help='请输入 title(标题)'),
            Argument('industries', help='请输入 industries(行业)'),
            Argument('attraction', help='请输入 attraction(商品卖点)'),
            Argument('video_num_needed', type=int, help='请输入 video_num_needed(拍摄视频数)'),
            Argument('is_return', type=bool, help='请输入 is_return(是否返样)'),
            Argument('video_size', type=int, help='请输入 video_size(尺寸)'),
            Argument('clarity', type=int, help='请输入 clarity(清晰度'),
            Argument('model_needed', required=False, type=int, help='请输入 model_needed(模特出镜)'),
            Argument('model_occur_rate', required=False, type=int, help='请输入 model_occur_rate(模特出境比例)'),
            Argument('model_age_range', required=False, type=int, help='请输入 model_age_range(模特年龄)'),
            Argument('model_figure', required=False, type=int, help='请输入 model_figure(模特身材)'),
            Argument('desc', type=str, required=False, help='请输入 desc(其他说明)'),
            Argument('example1', type=str, required=False, help='请输入 example1(参考视频1)'),
            Argument('example2', type=str, required=False, help='请输入 example2(参考视频2)'),
            Argument('example3', type=str, required=False, help='请输入 example3(参考视频3)'),
            # Argument('goods_images', help='请输入 goods_images(商品商品主图)'),
            Argument('action', type=int, help='请输入 action(发布操作 0保存/1发布)'),
            Argument('goods_link', help='请输入 goods_link(商品链接)', handler=lambda x: x.strip()),
            Argument('category', help='请输入 category(商品品类id)', type=int,
                     filter=lambda x: GoodsCategory.objects.filter(id=x).exists(),
                     handler=lambda x: GoodsCategory.objects.get(id=x)),
            Argument('address', type=int, help='请输入 address(收货地址)',
                     required=lambda x: x.get('is_return') is True,
                     filter=lambda x: Address.objects.filter(id=x, uid=request.user).exists(),
                     handler=lambda x: Address.objects.get(id=x)),
        ).parse(request.data, clear=True)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

        form['goods_title'], form['goods_images'], form['goods_channel'] = self.validate_goods_data(form.goods_link)

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
        form['video_num_remained'] = form.video_num_needed

        with atomic():
            if form.status == VideoNeeded.TO_CHECK:
                order_qs = UserPackageRelation.objects.filter(uid=self.request.user,
                                                              expiration_time__gte=datetime.datetime.now())
                if not order_qs.exists():
                    return Response({"detail": "您未购买套餐或套餐已过期", "err_code": 222},
                                    status=status.HTTP_206_PARTIAL_CONTENT)
                user_business = self.request.user.user_business
                if user_business.remain_video_num < form.video_num_needed:
                    return Response({"detail": "您账户中可使用的剩余视频数不足", "err_code": 111},
                                    status=status.HTTP_206_PARTIAL_CONTENT)
                user_business.remain_video_num -= form.video_num_needed
                user_business.save()
            instance = VideoNeeded.objects.create(uid=self.request.user, **form)
            serializer = self.get_serializer(instance)
            headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "不能删除"}, status=status.HTTP_400_BAD_REQUEST)
        # instance = self.get_object()
        # if instance.uid != self.request.user:
        #     return Response({"detail": "找不到这个订单"}, status=status.HTTP_400_BAD_REQUEST)
        # if instance.status != VideoNeeded.TO_PUBLISH:
        #     return Response({"detail": "不是待发布的订单"}, status=status.HTTP_400_BAD_REQUEST)
        # return super().destroy(request, *args, **kwargs)

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

        with atomic():
            user_business = self.request.user.user_business
            if form.action == 0:
                if instance.status != VideoNeeded.TO_PUBLISH:
                    return Response({"detail": "不是待发布的订单"}, status=status.HTTP_400_BAD_REQUEST)
                order_qs = UserPackageRelation.objects.filter(uid=self.request.user,
                                                              expiration_time__gte=datetime.datetime.now())
                if not order_qs.exists():
                    return Response({"detail": "您未购买套餐", "err_code": 222},
                                    status=status.HTTP_206_PARTIAL_CONTENT)
                if user_business.remain_video_num < instance.video_num_needed:
                    return Response({"detail": "您账户中可使用的剩余视频数不足", "err_code": 111},
                                    status=status.HTTP_206_PARTIAL_CONTENT)
                user_business.remain_video_num -= instance.video_num_remained
                user_business.save()
                instance.status = VideoNeeded.TO_CHECK
                instance.publish_time = datetime.datetime.now()
                instance.save()
                return Response({"detail": "以发布, 待审核中"}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "下架已经不用这个接口咯, 直接编辑的话会重新变成审核状态的"}, status=status.HTTP_400_BAD_REQUEST)
                # if instance.status not in [VideoNeeded.TO_CHECK, VideoNeeded.ON_GOING]:
                #     return Response({"detail": "不需要下架的订单"}, status=status.HTTP_400_BAD_REQUEST)
                # # 余量补回, 剩余量可能会被商家更改过
                # user_business.remain_video_num += instance.video_num_remained
                # user_business.save()
                # instance.status = VideoNeeded.TO_PUBLISH
                # instance.non_publish_time = datetime.datetime.now()
                # instance.save()
                # return Response({"detail": "已经下架"}, status=status.HTTP_200_OK)

    @action(methods=['post', ], detail=False, permission_classes=[ManagerPermission])
    def check_link(self, request, **kwargs):
        form, error = JsonParser(
            Argument('goods_link', help='请输入 goods_link(商品链接)', handler=lambda x: x.strip()),
        ).parse(request.data)
        hash_key = hash(form.goods_link)
        validate_key = f"validate_{hash_key}_{self.request.user.id}"
        conn.set(validate_key, 'ing', 60)
        logger.info(validate_key + ':ing')

        data_cache = f"goods_data_{hash_key}"
        images_key = f'images_{hash_key}_{self.request.user.id}'
        channel_key = f'channel_{hash_key}_{self.request.user.id}'
        title_key = f'title_{hash_key}_{self.request.user.id}'
        if conn.exists(data_cache):
            data = json.loads(conn.get(data_cache).decode('utf-8'))
            channel_value = data.get('channel', None)
            images_value = data.get('itempic', None)
            title_value = data.get('itemtitle', None)
            if channel_value is not None and images_value is not None and title_value is not None:
                conn.set(images_key, images_value, 3600)
                conn.set(channel_key, channel_value, 3600)
                conn.set(title_key, title_value, 3600)
                logger.info(validate_key + ':using cache')
                conn.set(validate_key, 'done', 3600)
                return Response(data, status=status.HTTP_200_OK)

        try:
            # 因为前端没有等待当前的接口完成就去调用创建接口, 所以这里要处理一下
            data = check_link_and_get_data(form.goods_link)
            if data == 444:
                return Response({'detail': '抱歉，该商品不是淘宝联盟商品'}, status=status.HTTP_400_BAD_REQUEST)
            channel_value = data.get('channel', None)
            images_value = data.get('itempic', None)
            title_value = data.get('itemtitle', None)
            if images_value is None or channel_value is None or title_value is None:
                logger.info(data)
                conn.set(validate_key, 'err', 60)
                return Response({"detail": "抱歉, 无法获取该商品来源以及图片, 校验不通过"}, status=status.HTTP_400_BAD_REQUEST)
            conn.set(images_key, images_value, 3600)
            conn.set(channel_key, channel_value, 3600)
            conn.set(title_key, title_value, 3600)
            logger.info(validate_key + ':done')
            conn.set(validate_key, 'done', 3600)
            conn.set(data_cache, json.dumps(data), 3600)
            return Response(data, status=status.HTTP_200_OK)
        except CheckLinkError as e:
            conn.set(validate_key, 'err', 60)
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except CheckLinkRequestError as e:
            conn.set(validate_key, 'err', 60)
            return Response({'detail': str(e), 'code': 123}, status=status.HTTP_400_BAD_REQUEST)
        except:
            conn.set(validate_key, 'err', 5)
            logger.info(traceback.format_exc())
            return Response({"detail": "校验接口报错了，请联系技术人员解决"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['get', ], detail=False, permission_classes=[ManagerPermission])
    def video_needed_status(self, request, **kwargs):
        data = {
            'video_remain_num': self.request.user.user_business.remain_video_num,
            'to_check': VideoNeeded.objects.filter(uid=request.user, status=VideoNeeded.TO_CHECK).count(),
            'on_going': VideoNeeded.objects.filter(uid=request.user, status=VideoNeeded.ON_GOING).count(),
            'to_publish': VideoNeeded.objects.filter(uid=request.user, status=VideoNeeded.TO_PUBLISH).count()
        }
        return Response(data, status=status.HTTP_200_OK)

    def validate_goods_data(self, goods_link):
        hash_key = hash(goods_link)
        validate_key = f"validate_{hash_key}_{self.request.user.id}"
        images_key = f'images_{hash_key}_{self.request.user.id}'
        channel_key = f'channel_{hash_key}_{self.request.user.id}'
        title_key = f'title_{hash_key}_{self.request.user.id}'
        logger.info(validate_key + ':checking')
        if not conn.exists(validate_key):
            raise exceptions.APIException(detail="该商品链接没有经过校验, 请先校验！", code=status.HTTP_400_BAD_REQUEST)
        else:
            time_remained = conn.ttl(validate_key)
            while time_remained > 0:
                validate_status = conn.get(validate_key).decode('utf-8')
                if validate_status == 'done':
                    goods_images = conn.get(images_key).decode('utf-8')
                    goods_channel = conn.get(channel_key).decode('utf-8')
                    goods_title = conn.get(title_key).decode('utf-8')
                    return goods_title, goods_images, goods_channel
                elif validate_status == 'err':
                    logger.info(validate_key + ':err')
                    raise exceptions.APIException(detail="该商品链接校验有误, 无法创建需求!", code=status.HTTP_400_BAD_REQUEST)
                elif validate_status == 'ing':
                    logger.info(validate_key + ':waiting')
                    time.sleep(0.1)
                    time_remained = conn.ttl(validate_key)
            else:
                # 超时了还是没有完成
                logger.info(validate_key + ':timeout')
                raise exceptions.APIException(detail="商品检测超时, 无法创建需求", code=status.HTTP_400_BAD_REQUEST)


class ManageVideoNeededViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AdminPermission]
    serializer_class = ManageVideoNeededSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('=uid__username', 'title')
    filter_class = ManageVideoNeededFilter

    # filter_fields = ('status', 'is_return', )

    def get_queryset(self):
        return VideoNeeded.objects.all()

    @action(methods=['post', ], detail=True, permission_classes=[AdminPermission])
    def check(self, request, **kwargs):
        form, error = JsonParser(
            Argument('action', filter=lambda x: x in ['pass', 'reject'], help="请输入action(操作) e.pass/reject"),
            Argument('order_video_slice', type=list,
                     filter=lambda x: len([i for i in x if int(i) > 0]) == len(x),
                     handler=lambda x: sorted([{'num': int(i), 'remain': 1} for i in x], key=lambda i: i.get('num')),
                     required=lambda rst: rst.get('action') == 'pass',
                     help="请输入 order_video_slice(视频切片数组) e.[10, 10, 20]"),
            Argument('order_slice_num', type=int, required=lambda rst: rst.get('action') == 'pass',
                     help="请输入 order_slice_num(切片数) e. 10"),
            Argument('reject_reason', required=lambda rst: rst.get('action') == 'reject'),
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
            user_business = instance.uid.user_business
            user_business.remain_video_num += instance.video_num_remained
            user_business.save()
            instance.check_time = datetime.datetime.now()
            instance.save()
            return Response({"detail": "已拒绝"}, status=status.HTTP_200_OK)
        else:
            if len(form.order_video_slice) != form.order_slice_num:
                return Response({"detail": "视频分片个数和订单总分片数不一致"}, status=status.HTTP_400_BAD_REQUEST)
            original_slice = [int(i) for i in request.data.get("order_video_slice")]
            if sum(original_slice) != instance.video_num_remained:
                return Response({"detail": "分片视频总数不等于需求的视频总数哦！"}, status=status.HTTP_400_BAD_REQUEST)
            new_order_video_slice = [i for i in instance.order_video_slice if i.get('remain') == 0]
            new_order_video_slice.extend(form.order_video_slice)
            instance.order_video_slice = sorted(new_order_video_slice, key=lambda i: i.get('num'))
            instance.status = VideoNeeded.ON_GOING
            instance.order_slice_num = len(new_order_video_slice)
            instance.order_num_remained = len([i for i in new_order_video_slice if i.get('remain') == 1])
            instance.check_time = datetime.datetime.now()
            instance.save()
            return Response({"detail": "已审核通过, 需求将展示于可申请的需求列表中"}, status=status.HTTP_200_OK)


class ClientVideoNeededViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [ManagerPermission]
    serializer_class = ClientVideoNeededSerializer
    queryset = VideoNeeded.objects.filter(status=VideoNeeded.ON_GOING)
    pagination_class = StandardResultsSetPagination
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title',)
    filter_fields = ('status', 'category', 'is_return',)

    def get_serializer_class(self):
        if self.action in ['list', ]:
            return ClientVideoNeededSerializer
        else:
            return ClientVideoNeededDetailSerializer

    def get_queryset(self):
        self.queryset = self.queryset.order_by('-create_time')
        recommend = self.request.query_params.get('recommend', None)
        if str(recommend) == '1':
            self.queryset = self.queryset.filter(order_num_remained__gt=0).order_by(
                '-create_time', 'order_num_remained'
            )
        return self.queryset


class ManageVideoHomePageViewSet(viewsets.ModelViewSet):
    permission_classes = [AdminPermission]
    serializer_class = HomePageVideoSerializer
    queryset = HomePageVideo.objects.all()
    pagination_class = StandardResultsSetPagination
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title',)
    filter_class = ManageHomePageVideoFilter

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        self.request.data['creator'] = self.request.user.uid
        return super().create(request, *args, **kwargs)
    # filter_fields = ('status', 'category', 'is_return',)


class BusVideoHomePageViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny, ]
    queryset = HomePageVideo.objects.filter(is_show=True).order_by('?')
    pagination_class = StandardResultsSetPagination
    serializer_class = HomePageVideoSerializer
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = ('video_size', 'clarity', 'model_needed', 'model_occur_rate',
                     'model_age_range', 'model_figure', 'category')


class test(APIView):
    permission_classes = [AllowAny]

    # @FlowLimiter.limited_decorator(limited="10/day;")
    def post(self, request):
        # data = check_link_and_get_data(request.data.get('goods_link').strip())
        hash_key = hash('askjhngkjadhfghiughkjfgnkjn234hiu2h98ry298y4234asdva')
        conn_key = f'validate_{hash_key}'
        conn.set(conn_key, 1)
        return Response('ok')

    def get(self, request):
        # hash_key = hash('askjhngkjadhfghiughkjfgnkjn234hiu2h98ry298y4234asdva')
        # conn_key = f'validate_{hash_key}'
        # if not conn.exists(conn_key):
        #     return Response(1, status=status.HTTP_400_BAD_REQUEST)
        # else:
        #     conn.delete(conn_key)
        #     return Response(0, status=status.HTTP_200_OK)
        a = time.time()
        # u_lis = []
        for v in HomePageVideo.objects.all():
            import random
            v.like = random.randint(5000, 50000)
            v.comment = random.randint(1000, 20000)
            v.share_num = random.randint(1000, 8888)
            v.save()
            # u_lis.append(v)
        # HomePageVideo.objects.bulk_update(u_lis, ['like', 'comment', 'share_num'])
        print(time.time() - a)
        return Response('ok', status=status.HTTP_200_OK)
