import json
import logging

from django.db.models import Sum
from django_filters import rest_framework
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from application.models import VideoOrder
from application.serializers import VideoApplicationCreateSerializer, BusVideoOrderSerializer
from demand.models import VideoNeeded
from libs.common.permission import CreatorPermission, AdminPermission, BusinessPermission

logger = logging.getLogger()


#
# class VideoApplicationViewSet(viewsets.ModelViewSet):
#     permission_classes = CreatorPermission
#     serializer_class = VideoApplicationSerializer
#     queryset = VideoOrder.objects.all()
#
#     def get_serializer_class(self):
#         if self.action == 'create':
#             self.serializer_class = VideoApplicationCreateSerializer
#         return super().get_serializer_class()
#
#     def create(self, request, *args, **kwargs):
#         user = request.user
#         request.data['user'] = user.uid
#         if not user.user_creator.is_signed:  # 非签约团队有视频数限制（5个）
#             video_sum = VideoOrder.objects.filter(user=user).exclude(status=VideoOrder.DONE).aggregate(
#                 sum=Sum('num_selected'))['sum']  # 进行中的视频数
#             if request.data['num_selected'] > 5 - video_sum:
#                 return Response({'detail': '可拍摄视频数不足'}, status=status.HTTP_400_BAD_REQUEST)
#
#         need_obj = VideoNeeded.objects.get(id=request.data['demand'])
#         order_video_slice = need_obj.order_video_slice
#         for index, i in enumerate(need_obj.order_video_slice):
#             dic = json.loads(i)
#             request.data['num_selected']
#             if index + 1 == len(order_video_slice):
#                 return Response({'detail': '抱歉，您选择的拍摄视频数已被领完，请重选选择'}, status=status.HTTP_400_BAD_REQUEST)
#
#         return super().create(request, *args, **kwargs)


class BusVideoOrderViewSet(viewsets.ModelViewSet):
    permission_classes = [AdminPermission, BusinessPermission]
    serializer_class = BusVideoOrderSerializer
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filters = ('status',)

    def get_queryset(self):
        return VideoOrder.objects.filter(demand__uid=self.request.user)

    @action(methods=['post', ], detail=True, permission_classes=[AdminPermission])
    def commit_express(self, request, **kwargs):
        instance = self.get_object()
