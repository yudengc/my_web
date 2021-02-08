"""tiktokvideo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve

from tiktokvideo.base import MEDIA_ROOT

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^media/(?P<path>.*)$', serve, {"document_root": MEDIA_ROOT}),
    path(r'api/v1/users/', include('users.urls', namespace='users')),
    path(r'api/v1/config/', include('config.urls', namespace='config')),
    path(r'api/v1/relation/', include('relations.urls', namespace='relations')),
    path(r'api/v1/transaction/', include('transaction.urls', namespace='transaction')),
    path(r'api/v1/demand/', include('demand.urls', namespace='demand')),
    path(r'api/v1/application/', include('application.urls', namespace='application')),
    path(r'api/v1/account/', include('account.urls', namespace='account')),
    path(r'api/v1/permissions/', include('permissions.urls', namespace='permissions')),
]

admin.site.site_header = "松鼠短视频运营管理后台"
admin.site.site_title = "松鼠短视频运营管理后台"
admin.site.index_title = "松鼠短视频运营管理后台"
