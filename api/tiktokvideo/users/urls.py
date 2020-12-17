from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import LoginViewSet, UserBusinessViewSet, UserInfoViewSet, BusInfoOtherView, AddressViewSet, \
    UserCreatorViewSet, ManageAddressViewSet, UserInfoManagerViewSet, UserCreatorInfoManagerViewSet, \
    UserBusinessInfoManagerViewSet, BusinessInfoManagerViewSet, TeamManagerViewSet, TeamUsersManagerViewSet, \
    TeamLeaderManagerViewSet, ScriptTypeViewSet, CelebrityStyleViewSet, PublicWeChat, ManagerUserViewSet, \
    BusStatisticalView, UserBusinessDeliveryManagerViewSet

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
manager_router.register(r'user-creator', UserCreatorInfoManagerViewSet, basename='user_creator')
manager_router.register(r'user-bus', UserBusinessInfoManagerViewSet, basename='user_bus')
manager_router.register(r'bus-info', BusinessInfoManagerViewSet, basename='bus_info')
manager_router.register(r'team', TeamManagerViewSet, basename='team')
manager_router.register(r'team-users', TeamUsersManagerViewSet, basename='team_users')
manager_router.register(r'team-leader', TeamLeaderManagerViewSet, basename='team_leader')
manager_router.register(r'celebrity-style', CelebrityStyleViewSet, basename='celebrity_style')
manager_router.register(r'script-type', ScriptTypeViewSet, basename='script_type')
manager_router.register(r'manager-user', ManagerUserViewSet, basename='manager_user')
manager_router.register(r'bus-delivery', UserBusinessDeliveryManagerViewSet, basename='manager_user')


urlpatterns = [
    path(r'', include(login_router.urls)),
    path(r'manager/', include(manager_router.urls)),
    path(r'bus-info-other/', BusInfoOtherView.as_view()),
    path(r'manager/bus-statistical/', BusStatisticalView.as_view()),

    # 公众号相关
    path(r'wechat-public/', PublicWeChat.as_view()),
    path(r'wechat-public/<str:_action>/', PublicWeChat.as_view()),
]
