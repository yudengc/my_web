# -*- coding: utf-8 -*-
# @Time    : 2020/2/21 9:49 PM
# @Author  : HF

from django.urls import path, include
from rest_framework.routers import DefaultRouter

import permissions.views

app_name = "permissions"

role_router = DefaultRouter()
role_router.register(r'', permissions.views.GroupsViewSet, basename='role')

fea_mod_router = DefaultRouter()
# fea_mod_router.register(r'', rbac.views.FeatureModuleViewSet)
fea_mod_router.register(r'', permissions.views.FeatureMenusViewSet, basename='fea')

manager_router = DefaultRouter()
manager_router.register(r'', permissions.views.ManagerViewSet, basename='manager')

urlpatterns = [
    path(r'groups/', include(role_router.urls)),
    path(r'feature-module/', include(fea_mod_router.urls)),
    path(r'manager/', include(manager_router.urls)),
]
