from django_filters import rest_framework
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from libs.common.permission import ManagerPermission, SalesmanPermission, AdminPermission
from relations.filter import MyRelationInfoFilter
from relations.models import InviteRelationManager
from relations.serializers import MyRelationSerializer, MyRecordsSerializer, MyRelationInfoManagerSerializer
from transaction.models import OrderInfo
from users.models import Users


class MyRelationInfoViewSet(viewsets.ReadOnlyModelViewSet):
    """我的邀请"""
    serializer_class = MyRelationSerializer
    permission_classes = (SalesmanPermission,)
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = MyRelationInfoFilter

    def get_queryset(self):
        self.queryset = InviteRelationManager.objects.filter(salesman=self.request.user,
                                                             invitee__identity=Users.BUSINESS).order_by('-date_created')
        return super(MyRelationInfoViewSet, self).get_queryset()

    @action(methods=['get'], detail=False, serializer_class=MyRecordsSerializer)
    def records(self, request, **kwargs):
        """
        商家付费记录
        """
        values_list = self.filter_queryset(self.get_queryset()).values_list('invitee__uid')
        uid_lis = [i[0] for i in values_list]
        queryset = OrderInfo.objects.filter(uid__uid__in=uid_lis,
                                            status=OrderInfo.SUCCESS,
                                            tran_type=OrderInfo.PACKAGE).all()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class MyRelationInfoManagerViewSet(viewsets.ReadOnlyModelViewSet):
    """邀请关系记录后台"""
    queryset = InviteRelationManager.objects.select_related('invitee', 'inviter', 'salesman')
    serializer_class = MyRelationInfoManagerSerializer
    permission_classes = (AdminPermission,)
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('invitee__username', 'invitee__auth_base__nickname',
                     'inviter__username', 'inviter__auth_base__nickname', )


