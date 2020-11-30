from rest_framework import mixins, viewsets

from account.models import CreatorAccount
from account.serializers import MyCreatorAccountSerializer
from libs.common.permission import ManagerPermission, CreatorPermission


class MyCreatorAccountViewSet(viewsets.ReadOnlyModelViewSet):
    """我的账户"""
    permission_classes = (CreatorPermission,)
    serializer_class = MyCreatorAccountSerializer

    def get_queryset(self):
        self.queryset = CreatorAccount.objects.filter(uid=self.request.user)
        return super().get_queryset()

