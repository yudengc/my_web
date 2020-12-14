from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from account.views import MyCreatorAccountViewSet, MyCreatorBillViewSet, MyBalanceRecordViewSet, CreatorBillViewSet
from application.views import BusVideoOrderViewSet, VideoApplicationViewSet, VideoApplicationManagerViewSet, \
    VideoCountView, VideoOrderDetailViewSet

app_name = "account"

creator_router = DefaultRouter()
creator_router.register(r'my-account', MyCreatorAccountViewSet, basename='account')
creator_router.register(r'bill', MyCreatorBillViewSet, basename='bill')
creator_router.register(r'balance-record', MyBalanceRecordViewSet, basename='balance-record')


manager_router = DefaultRouter()
manager_router.register(r'bill', CreatorBillViewSet, basename='bill')

urlpatterns = [
    # path('admin/', admin.site.urls),
    path(r'creator/', include(creator_router.urls)),
    path(r'manager/', include(manager_router.urls)),

]
