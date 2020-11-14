# -*- coding: utf-8 -*-
"""
@Time    : 2020/10/26 4:13 下午
@Author  : LuckyTom
@File    : urls.py
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from transaction.views import WeChatPayViewSet, WeChatPayBackViewSet, PayCancelViewSet

app_name = "transaction"
router = DefaultRouter()


urlpatterns = [
    path(r'', include(router.urls)),
    path(r'wechat/pay/', WeChatPayViewSet.as_view()),
    path(r'wechat/back/', WeChatPayBackViewSet.as_view()),
    path(r'pay/cancel/', PayCancelViewSet.as_view()),
]
