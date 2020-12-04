from django_filters import rest_framework
from rest_framework import mixins, viewsets, filters
from rest_framework.response import Response

from account.models import CreatorAccount, CreatorBill, BalanceRecord
from account.serializers import MyCreatorAccountSerializer, MyCreatorBillSerializer, MyBalanceRecordSerializer
from libs.common.permission import ManagerPermission, CreatorPermission


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
