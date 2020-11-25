from django.shortcuts import render

from rest_framework import viewsets

# Create your views here.
from demand.models import VideoNeeded
from demand.serializers import VideoNeededSerializer
from libs.common.permission import ManagerPermission


class VideoNeededViewSet(viewsets.ModelViewSet):
    permission_classes = ManagerPermission
    serializer_class = VideoNeededSerializer

    def get_queryset(self):
        self.queryset = VideoNeeded.objects.filter(uid=self.request.user)
        return self.queryset

