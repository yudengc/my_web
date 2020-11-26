import json
import logging

from django.db.models import Sum
from rest_framework import viewsets, status
from rest_framework.response import Response

from application.models import VideoOrder
from application.serializers import VideoApplicationCreateSerializer
from demand.models import VideoNeeded
from libs.common.permission import CreatorPermission

logger = logging.getLogger()


class VideoApplicationViewSet(viewsets.ModelViewSet):
    permission_classes = CreatorPermission
    serializer_class = VideoApplicationSerializer
    queryset = VideoOrder.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            self.serializer_class = VideoApplicationCreateSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        user = request.user
        request.data['user'] = user.uid
        if not user.user_creator.is_signed:  # 非签约团队有视频数限制（5个）
            video_sum = VideoOrder.objects.filter(user=user).exclude(status=VideoOrder.DONE).aggregate(
                sum=Sum('num_selected'))['sum']  # 进行中的视频数
            if request.data['num_selected'] > 5 - video_sum:
                return Response({'detail': '可拍摄视频数不足'}, status=status.HTTP_400_BAD_REQUEST)

        need_obj = VideoNeeded.objects.get(id=request.data['demand'])
        order_video_slice = need_obj.order_video_slice
        for index, i in enumerate(need_obj.order_video_slice):
            dic = json.loads(i)
            request.data['num_selected']
            if index + 1 == len(order_video_slice):
                return Response({'detail': '抱歉，您选择的拍摄视频数已被领完，请重选选择'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)
