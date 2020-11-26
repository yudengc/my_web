from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from demand.views import VideoNeededViewSet, ManageVideoNeededViewSet

app_name = "demand"

router = DefaultRouter()
router.register(r'video', VideoNeededViewSet, basename='video')
# router.register(r'customer-service', CustomerServiceViewSet, basename='login')
manager_router = DefaultRouter()
manager_router.register(r'video', ManageVideoNeededViewSet, basename='video')

urlpatterns = [
    # path('admin/', admin.site.urls),
    path(r'', include(router.urls)),
    path(r'manager/', include(router.urls)),
]
