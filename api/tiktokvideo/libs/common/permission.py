# -*- coding: utf-8 -*-
from functools import wraps
from typing import Union

from rest_framework import permissions, exceptions, status
from rest_framework.request import Request

from users.models import Users


def is_user(request):
    """
    是否用户
    :param request:
    :return:
    """
    return request.user.is_authenticated and isinstance(request.user, Users)


def is_super_admin(request: Request) -> bool:
    return request.user.is_authenticated and isinstance(request.user, Users) \
           and request.user.sys_role in [Users.SUPER_ADMIN]


def is_admin(request: Request) -> bool:
    return request.user.is_authenticated and isinstance(request.user, Users) \
           and request.user.sys_role in [Users.ADMIN, Users.SUPER_ADMIN]


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


class SalesmanPermission(permissions.BasePermission):
    """业务员基本权限"""

    def has_permission(self, request, view):
        if is_super_admin(request):
            return True
        return request.user.is_authenticated and isinstance(request.user, Users) \
               and request.user.identity in [Users.SALESMAN, Users.SUPERVISOR]


class BusinessPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if is_super_admin(request):
            return True
        return request.user.is_authenticated and isinstance(request.user, Users) \
               and request.user.identity == Users.BUSINESS


class AdminPermission(permissions.BasePermission):
    """后台管理员权限"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and isinstance(request.user, Users) \
               and request.user.sys_role in [Users.ADMIN, Users.SUPER_ADMIN]


class CreatorPermission(permissions.BasePermission):
    """创作者基本权限"""

    def has_permission(self, request, view):
        if is_super_admin(request):
            return True
        return request.user.is_authenticated and isinstance(request.user, Users) \
               and request.user.identity == Users.CREATOR


def custom_check_permission(permission_group: Union[list, tuple], union: bool = True):
    """
    Args:
        permission_group: 权限组
        union:  是否联合(True全部满足才ok， False满足一个ok)
    Returns:
        bool
    """
    if not isinstance(permission_group, list) and not isinstance(permission_group, tuple):
        raise ValueError("权限组给我一个列表或者元组")

    for per in permission_group:
        if not issubclass(per, permissions.BasePermission):
            raise ValueError("权限组错误~")

    def deco_func(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) < 2:
                raise exceptions.APIException(detail="请求错误, 参数缺失",
                                              code=status.HTTP_500_INTERNAL_SERVER_ERROR)
            instance = args[0]
            request = args[1]
            if not isinstance(request, Request):
                raise exceptions.APIException(detail="请求错误, 无法获取request",
                                              code=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if union is True:
                for _per in permission_group:
                    if not _per().has_permission(request, instance):
                        raise exceptions.AuthenticationFailed()
            else:
                permit = False
                for _per in permission_group:
                    if _per().has_permission(request, instance):
                        permit = True
                        break
                if not permit:
                    raise exceptions.AuthenticationFailed()

            return func(*args, **kwargs)

        return wrapper

    return deco_func
