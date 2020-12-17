from datetime import datetime

from django.db.transaction import atomic
from django_filters import rest_framework
from rest_framework import mixins, viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from account.filter import CreatorBillFilter
from account.models import CreatorAccount, CreatorBill, BalanceRecord
from account.serializers import MyCreatorAccountSerializer, MyCreatorBillSerializer, MyBalanceRecordSerializer, \
    CreatorBillManagerSerializer, CreatorBillUpdateManagerSerializer, CreatorBillDetailSerializer
from application.models import VideoOrder
from libs.common.permission import ManagerPermission, CreatorPermission, AdminPermission


class MyCreatorAccountViewSet(viewsets.ReadOnlyModelViewSet):
    """
        我的账户
        结算逻辑：
        当月未入账待结算金币实时计算，
        上个月待结算金额在本月8号前实时计算，8号后统计上个月待结算金币并生成账单数据（因为有可能因为上月末已完成的订单因为商家不满意，
        后台会把已完成改成其他状态，所以给一个星期的缓冲期再统计上月待结算金币）
    """
    permission_classes = (CreatorPermission,)
    serializer_class = MyCreatorAccountSerializer

    def get_queryset(self):
        self.queryset = CreatorAccount.objects.filter(uid=self.request.user)
        if not self.queryset.exists():
            account_obj = CreatorAccount.objects.create(uid=self.request.user)
            self.queryset = CreatorAccount.objects.filter(id=account_obj.id)
        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data[0])


class MyCreatorBillViewSet(viewsets.ReadOnlyModelViewSet):
    """
    我的历史统计账单
    """
    permission_classes = (CreatorPermission,)
    serializer_class = MyCreatorBillSerializer
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = ('bill_year',)

    def get_queryset(self):
        self.queryset = CreatorBill.objects.filter(uid=self.request.user).order_by('-date_created')
        return super().get_queryset()


class MyBalanceRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    我的历史统计账单
    """
    permission_classes = (CreatorPermission,)
    serializer_class = MyBalanceRecordSerializer

    def get_queryset(self):
        self.queryset = BalanceRecord.objects.filter(uid=self.request.user)
        return super().get_queryset()


class CreatorBillViewSet(mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.ListModelMixin,
                         GenericViewSet):
    """
    账单后台管理
    """
    permission_classes = (AdminPermission,)
    serializer_class = CreatorBillManagerSerializer
    queryset = CreatorBill.objects.exclude(total=0).order_by('-id')
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = CreatorBillFilter
    search_fields = ('=uid__username', 'uid__auth_base__nickname')

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            self.serializer_class = CreatorBillUpdateManagerSerializer
        return super().get_serializer_class()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance.status == CreatorBill.DONE:
            return Response({'detail': '请不要重复审核账单'}, status=status.HTTP_400_BAD_REQUEST)
        if request.data.get('status') == CreatorBill.DONE:
            request.data['check_time'] = datetime.now()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        with atomic():
            self.perform_update(serializer)
            if serializer.data.get('status') == CreatorBill.DONE:
                account_obj = CreatorAccount.objects.get(uid=instance.uid)
                BalanceRecord.objects.create(uid=instance.uid,
                                             operation_type=BalanceRecord.SETTLEMENT,
                                             amount=instance.total,
                                             balance=account_obj.coin_balance + instance.total)
                account_obj.coin_balance += instance.total
                account_obj.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    @action(methods=['get'], detail=True)
    def bill_detail(self, request, **kwargs):
        """
        账单详情
        """
        instance = self.get_object()
        order_qs = VideoOrder.objects.filter(user=instance.uid,
                                             status=VideoOrder.DONE,
                                             done_time__year=instance.bill_year,
                                             done_time__month=instance.bill_month).\
            select_related('video_order_detail', 'demand__uid')
        page = self.paginate_queryset(order_qs)
        if page is not None:
            serializer = CreatorBillDetailSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CreatorBillDetailSerializer(order_qs, many=True)
        return Response(serializer.data)
