from rest_framework import mixins, viewsets

from account.models import CreatorAccount
from account.serializers import MyCreatorAccountSerializer
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

