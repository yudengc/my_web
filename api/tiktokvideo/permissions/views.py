from django_filters import rest_framework
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from libs.common.permission import ManagerPermission, AdminPermission, is_super_admin
from libs.pagination import StandardResultsSetPagination
from permissions.models import UserGroups, PermissionsBase
from users.models import Users
from .serializers import (UserGroupsSerializer, FeatureMenusReadSerializer, RoleCreateOrUpdateSerializer,
                          ManagerSerializer)


class GroupsViewSet(viewsets.ModelViewSet):
    """
    用户组管理
    """
    permission_classes = (AdminPermission,)
    queryset = UserGroups.objects.prefetch_related('feature_modules').all()
    serializer_class = UserGroupsSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            self.serializer_class = RoleCreateOrUpdateSerializer
        return super(GroupsViewSet, self).get_serializer_class()


class FeatureMenusViewSet(viewsets.ReadOnlyModelViewSet):
    """
    菜单/权限列表
    """
    permission_classes = (AdminPermission,)
    serializer_class = FeatureMenusReadSerializer
    pagination_class = None

    def get_queryset(self):
        this_man = self.request.user
        self.permissions = PermissionsBase.objects.all()
        self.queryset = PermissionsBase.objects.filter(pid=None).order_by('order_num')
        if not is_super_admin(self.request):
            self.queryset = self.queryset.filter(is_active=True)
            self.permissions = PermissionsBase.objects.none()
            if this_man.permission_group:
               self.permissions = this_man.permission_group.feature_modules.all()
        return self.queryset.filter(id__in=self.permissions)


class ManagerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    后台管理人员权限管理
    """

    permission_classes = (AdminPermission,)
    serializer_class = ManagerSerializer
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter,)
    filter_fields = ("permission_group",)
    search_fields = ('username',)

    def get_queryset(self):
        return Users.objects.filter(sys_role__in=[Users.SUPER_ADMIN, Users.ADMIN])

