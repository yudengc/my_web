from django.urls import path, include
from rest_framework.routers import DefaultRouter

from users.views import LoginViewSet

app_name = "users"
login_router = DefaultRouter()
login_router.register(r'login', LoginViewSet, basename='login')


urlpatterns = [
    path(r'', include(login_router.urls)),
]
