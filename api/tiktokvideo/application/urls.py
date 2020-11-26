from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from application.views import BusVideoOrderViewSet

app_name = "application"

router = DefaultRouter()


bus_router = DefaultRouter()
bus_router.register(r'video', BusVideoOrderViewSet, basename='video')


urlpatterns = [
    # path('admin/', admin.site.urls),
    path(r'', include(router.urls)),
    path(r'bus/', include(bus_router.urls)),


]
