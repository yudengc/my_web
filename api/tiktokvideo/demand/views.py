from django.shortcuts import render

from rest_framework import viewsets, status

# Create your views here.
from rest_framework.decorators import action
from rest_framework.response import Response

from demand.models import VideoNeeded
from demand.serializers import VideoNeededSerializer
from libs.common.permission import ManagerPermission, AdminPermission


class VideoNeededViewSet(viewsets.ModelViewSet):
    permission_classes = ManagerPermission
    serializer_class = VideoNeededSerializer

    def get_queryset(self):
        self.queryset = VideoNeeded.objects.filter(uid=self.request.user)
        return self.queryset

    @action(methods=['post', ], detail=True, permission_classes=[ManagerPermission])
    def publish(self, request, **kwargs):
        return Response({"detail": "以发布, 待审核中"}, status=status.HTTP_200_OK)

    @action(methods=['post', ], detail=True, permission_classes=[ManagerPermission])
    def non_publish(self, request, **kwargs):
        return Response({"detail": "以成功下架, 可以重新编辑并上架"}, status=status.HTTP_200_OK)


class ManageVideoNeededViewSet(viewsets.ModelViewSet):
    permission_classes = AdminPermission
