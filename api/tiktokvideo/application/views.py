import json
import logging

from django.db.models import Sum
from django.db.transaction import atomic
from rest_framework import viewsets, status, mixins, filters
from django_filters import rest_framework
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from application.models import VideoOrder, Video
from application.serializers import VideoApplicationCreateSerializer, VideoApplicationListSerializer, \
    VideoApplicationRetrieveSerializer, BusVideoOrderSerializer
from demand.models import VideoNeeded
from libs.common.permission import CreatorPermission, AdminPermission, BusinessPermission, ManagerPermission
from libs.parser import Argument, JsonParser

logger = logging.getLogger()


class VideoApplicationViewSet(mixins.CreateModelMixin,
                              mixins.RetrieveModelMixin,
                              mixins.UpdateModelMixin,
                              mixins.ListModelMixin,
                              GenericViewSet):
    permission_classes = (CreatorPermission,)
    queryset = VideoOrder.objects.all()

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
            self.queryset = self.queryset.select_related('demand')
        return super().get_queryset()

    def create(self, request, *args, **kwargs):
        user = request.user
        request.data['user'] = user.uid
        if not user.user_creator.is_signed:  # 非签约团队有视频数限制（5个）
            video_sum = VideoOrder.objects.filter(user=user).exclude(status=VideoOrder.DONE).aggregate(
                sum=Sum('num_selected'))['sum']  # 进行中的视频数
            if request.data['num_selected'] > 5 - video_sum:
                return Response({'detail': '可拍摄视频数不足'}, status=status.HTTP_400_BAD_REQUEST)

        # 乐观🔒判断可选的视频数是否被领了（怕在用户填信息时被其他用户领了）
        need_obj = VideoNeeded.objects.get(id=request.data['demand'])
        order_video_slice = need_obj.order_video_slice
        # e. [{'num': 10, 'remain': 1}, {'num': 20, 'remain': 1}]
        request.data['goods_link'] = need_obj.goods_link
        request.data['goods_images'] = need_obj.goods_images
        request.data['goods_channel'] = need_obj.goods_channel
        request.data['is_return'] = need_obj.is_return
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with atomic():
            try:
                # 订单过程中需维护VideoNeeded的3个字段: order_video_slice, order_num_remained, video_num_remained
                slice_idx = order_video_slice.index({'num': request.data['num_selected'], 'remain': 1})
                need_obj.order_video_slice[slice_idx]['remain'] = 0
                need_obj.order_num_remained -= 1
                need_obj.video_num_remained -= request.data['num_selected']
                need_obj.save()
            except ValueError:
                return Response({'detail': '哎呀，您选择的拍摄视频数已被选走，请重选选择'}, status=status.HTTP_400_BAD_REQUEST)

            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(methods=['put'], detail=True)
    def upload_video(self, request):
        """提交视频"""
        video_lis = request.data.get('video_lis')
        order_obj = self.get_object()
        lis = []
        for video_url in video_lis:
            lis.append(Video(video_url=video_url, order=order_obj))
        Video.objects.bulk_create(lis)
        return Response({'detail': '提交成功'})

    @action(methods=['get'], detail=False)
    def order_status_count(self, request):
        order_qs = VideoOrder.objects.filter(user=request.user)
        data = dict(wait_send=order_qs.filter(status=VideoOrder.WAIT_SEND).count,
                    wait_commit=order_qs.filter(status=VideoOrder.WAIT_COMMIT).count,
                    wait_check=order_qs.filter(status=VideoOrder.WAIT_CHECK).count,
                    wait_return=order_qs.filter(status=VideoOrder.WAIT_RETURN).count)
        return Response(data)


class BusVideoOrderViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AdminPermission, BusinessPermission]
    serializer_class = VideoApplicationRetrieveSerializer
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filters = ('status',)

    def get_queryset(self):
        return VideoOrder.objects.filter(demand__uid=self.request.user)

    # def get_serializer_class(self):
    #     if self.action in ['retrieve', ]:
    #         return VideoApplicationRetrieveSerializer
    #     else:
    #         return BusVideoOrderSerializer

    @action(methods=['post', ], detail=True, permission_classes=[AdminPermission])
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
        instance.express = form.express
        instance.company = form.company
        instance.save()
        return Response({"detail": "已提交成功"}, status=status.HTTP_200_OK)

    @action(methods=['post', ], detail=False, permission_classes=[ManagerPermission])
    def video_order_status(self, request, **kwargs):
        data = dict(wait_send=VideoOrder.objects.filter(demand__uid=request.user, status=0).count(),
                    wait_commit=VideoOrder.objects.filter(demand__uid=request.user, status=1).count(),
                    wait_return=VideoOrder.objects.filter(demand__uid=request.user, status=4).count(),
                    done=VideoOrder.objects.filter(demand__uid=request.user, status=5).count())
        return Response(data, status=status.HTTP_200_OK)
