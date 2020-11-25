from django.shortcuts import render

from rest_framework import viewsets

# Create your views here.
from demand.serializers import VideoNeededSerializer
from libs.common.permission import ManagerPermission


class VideoNeededViewSet(viewsets.ModelViewSet):
    permission_classes = ManagerPermission
    serializer_class = VideoNeededSerializer

    def get_queryset(self):
        pass

