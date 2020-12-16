# -*- coding: utf-8 -*-
# @Time    : 2020/2/21 9:49 PM
# @Author  : HF
from rest_framework import serializers

from permissions.models import UserGroups, PermissionsBase
from users.models import Users


class UserGroupsSerializer(serializers.ModelSerializer):
    """
    权限组管理
    """

    class Meta:
        model = UserGroups
        fields = '__all__'


class RoleCreateOrUpdateSerializer(serializers.ModelSerializer):
    """
   新增权限组
    """

    class Meta:
        model = UserGroups
        fields = ('id', 'title', 'description',)


class ChildrenMenusReadSerializer(serializers.ModelSerializer):
    """
    子菜单权限详细列表
    """

    children = serializers.SerializerMethodField()
    key = serializers.SerializerMethodField()

    class Meta:
        model = PermissionsBase
        fields = ('id', 'path', 'name', 'pid', 'category', 'children', 'key')

    def __init__(self, *args, **kwargs, ):
        super().__init__(*args, **kwargs, )
        self.permissions = self.context["permissions"]

    def get_key(self, obj):
        return obj.id

    def get_children(self, obj):
        pers = PermissionsBase.objects.filter(
            is_active=True, pid=obj.id, id__in=self.permissions
        ).order_by('order_num').distinct()
        return ChildrenMenusReadSerializer(pers, many=True, context={'permissions': self.permissions}).data


class FeatureMenusReadSerializer(serializers.ModelSerializer):
    """
    父菜单列表
    """
    children = serializers.SerializerMethodField()
    key = serializers.SerializerMethodField()

    class Meta:
        model = PermissionsBase
        fields = ('id', 'path', 'name', 'category', 'children', 'key')

    def get_key(self, obj):
        return obj.id

    def get_children(self, obj):
        permissions = self.context['view'].permissions
        feas = PermissionsBase.objects.filter(
            is_active=True, pid=obj.id, id__in=permissions
        ).order_by('order_num').distinct()
        if feas:
            return ChildrenMenusReadSerializer(
                feas,
                many=True,
                context={'permissions': list(permissions.values_list('id', flat=True))}
            ).data
        return []


class ManagerSerializer(serializers.ModelSerializer):
    """
    后台管理人员
    """
    phone = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Users
        fields = '__all__'

    def get_phone(self, obj):
        return obj.auth_base.first().phone if obj.auth_base.first() else None
