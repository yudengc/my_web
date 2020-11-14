from django.urls import path, include
from rest_framework.routers import DefaultRouter

from config.views import CustomerServiceViewSet

app_name = "config"

router = DefaultRouter()
router.register(r'customer-service', CustomerServiceViewSet, basename='login')


urlpatterns = [
    path(r'', include(router.urls)),


]
