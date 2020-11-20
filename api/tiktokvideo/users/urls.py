from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import LoginViewSet, UserBusinessViewSet, UserInfoViewSet

app_name = "users"
login_router = DefaultRouter()
login_router.register(r'login', LoginViewSet, basename='login')
login_router.register(r'user-business', UserBusinessViewSet, basename='user_business')
login_router.register(r'user-info', UserInfoViewSet, basename='user_info')


urlpatterns = [
    path(r'', include(login_router.urls)),
]
