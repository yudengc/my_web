from django.shortcuts import render
from django_filters import rest_framework

from rest_framework import viewsets, status, filters

# Create your views here.
from rest_framework.decorators import action
from rest_framework.response import Response

from demand.models import VideoNeeded
from demand.serializers import VideoNeededSerializer
from libs.common.permission import ManagerPermission, AdminPermission
from libs.pagination import StandardResultsSetPagination
from libs.parser import JsonParser, Argument


class VideoNeededViewSet(viewsets.ModelViewSet):
    permission_classes = ManagerPermission
    serializer_class = VideoNeededSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = ('status',)

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
    serializer_class = VideoNeededSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('uid__username',)
    filter_fields = ('status',)

    def get_queryset(self):
        return VideoNeeded.objects.all()

    @action(methods=['post', ], detail=True, permission_classes=[ManagerPermission])
    def check(self, request, **kwargs):
        form, error = JsonParser(
            Argument('action', filter=lambda x: x in ['pass', 'reject'], help="请输入action(操作) e.pass/reject"),
            Argument('video_slice', type=list, handler=lambda x: [int(i) for i in x],
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
