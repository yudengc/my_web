from django_filters import rest_framework
from rest_framework import viewsets, filters
from rest_framework.decorators import action

from libs.common.permission import ManagerPermission, SalesmanPermission
from relations.filter import MyRelationInfoFilter
from relations.models import InviteRelationManager
from relations.serializers import MyRelationSerializer, MyRecordsSerializer
from users.models import Users


class MyRelationInfoViewSet(viewsets.ReadOnlyModelViewSet):
    """我的邀请"""
    serializer_class = MyRelationSerializer
    permission_classes = (SalesmanPermission,)
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = MyRelationInfoFilter

    def get_queryset(self):
        self.queryset = InviteRelationManager.objects.filter(inviter=self.request.user,
                                                             invitee__identity=Users.BUSINESS)
        return super(MyRelationInfoViewSet, self).get_queryset()

    @action(methods=['get'], detail=False, serializer_class=MyRecordsSerializer)
    def records(self, request, **kwargs):
        """
        商家付费记录
        """
        return super().list(request, **kwargs)
