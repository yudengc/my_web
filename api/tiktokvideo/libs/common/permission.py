# -*- coding: utf-8 -*-


from rest_framework import permissions

from users.models import Users


def is_user(request):
    """
    是否用户
    :param request:
    :return:
    """
    return request.user.is_authenticated and isinstance(request.user, Users)


class DenyAnyManger(permissions.BasePermission):
    """禁止权限"""

    def has_permission(self, request, view):
        return False


class AllowAny(permissions.BasePermission):
    """开放权限"""

    def has_permission(self, request, view):
        print(">>>>>>开放权限")
        return True


class ManagerPermission(permissions.BasePermission):
    """用户基本权限"""

    def has_permission(self, request, view):
        print(">>>>>>>基本权限")
        return is_user(request)
