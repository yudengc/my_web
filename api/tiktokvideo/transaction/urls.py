# -*- coding: utf-8 -*-
"""
@Time    : 2020/10/26 4:13 下午
@Author  : LuckyTom
@File    : urls.py
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from transaction.views import WeChatPayViewSet, WeChatPayBackViewSet, PayCancelViewSet, PackageViewSet, \
    MyPackageViewSet, OrderInfoViewSet, PackageManagerViewSet, UserPackageRelationManagerViewSet

app_name = "transaction"
router = DefaultRouter()
router.register(r'package', PackageViewSet, basename='package')
router.register(r'my-package', MyPackageViewSet, basename='my_package')
router.register(r'order-info', OrderInfoViewSet, basename='order_info')

manager_router = DefaultRouter()
manager_router.register(r'package', PackageManagerViewSet, basename='package')
manager_router.register(r'package-user', UserPackageRelationManagerViewSet, basename='package_user')

urlpatterns = [
    path(r'', include(router.urls)),
    path(r'manager/', include(manager_router.urls)),
    path(r'wechat/pay/', WeChatPayViewSet.as_view()),
    path(r'wechat/back/', WeChatPayBackViewSet.as_view()),
    path(r'pay/cancel/', PayCancelViewSet.as_view()),
]
