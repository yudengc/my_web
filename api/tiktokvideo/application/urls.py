from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from application.views import BusVideoOrderViewSet, VideoApplicationViewSet, VideoApplicationManagerViewSet

app_name = "application"

creator_router = DefaultRouter()
creator_router.register(r'video', VideoApplicationViewSet, basename='video')


bus_router = DefaultRouter()
bus_router.register(r'video', BusVideoOrderViewSet, basename='video')


manager_router = DefaultRouter()
manager_router.register(r'video', VideoApplicationManagerViewSet, basename='video_man')

urlpatterns = [
    # path('admin/', admin.site.urls),
    path(r'creator/', include(creator_router.urls)),
    path(r'bus/', include(bus_router.urls)),
    path(r'manager/', include(manager_router.urls)),

]
