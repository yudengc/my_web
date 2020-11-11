from django.urls import path, include
from rest_framework.routers import DefaultRouter


app_name = "users"
login_router = DefaultRouter()
# login_router.register(r'login', LoginViewSet, basename='login')
# login_router.register(r'info', UserInfoViewSet, basename='info')

urlpatterns = [
    path(r'', include(login_router.urls)),
]
