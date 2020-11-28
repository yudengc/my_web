from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import LoginViewSet, UserBusinessViewSet, UserInfoViewSet, BusInfoOtherView, AddressViewSet, \
    UserCreatorViewSet, ManageAddressViewSet, UserInfoManagerViewSet

app_name = "users"
login_router = DefaultRouter()
login_router.register(r'login', LoginViewSet, basename='login')
login_router.register(r'user-business', UserBusinessViewSet, basename='user_business')
login_router.register(r'user-info', UserInfoViewSet, basename='user_info')
login_router.register(r'address', AddressViewSet, basename='address')
login_router.register(r'manage_address', ManageAddressViewSet, basename='address')
login_router.register(r'creator', UserCreatorViewSet, basename='user_creator')

manager_router = DefaultRouter()
manager_router.register(r'user-info', UserInfoManagerViewSet, basename='user_info_man')

urlpatterns = [
    path(r'', include(login_router.urls)),
    path(r'manager/', include(manager_router.urls)),
    path(r'bus-info-other/', BusInfoOtherView.as_view()),

]
