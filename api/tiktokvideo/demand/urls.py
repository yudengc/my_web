from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from demand.views import VideoNeededViewSet

app_name = "demand"

router = DefaultRouter()
router.register(r'video', VideoNeededViewSet, basename='video')
# router.register(r'customer-service', CustomerServiceViewSet, basename='login')


urlpatterns = [
    # path('admin/', admin.site.urls),
    path(r'', include(router.urls)),
]
