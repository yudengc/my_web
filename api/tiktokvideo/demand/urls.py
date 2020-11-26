from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from demand.views import VideoNeededViewSet, ManageVideoNeededViewSet, test, ClientVideoNeededViewSet

app_name = "demand"

client_router = DefaultRouter()
client_router.register(r'video', ClientVideoNeededViewSet, basename='video')


bus_router = DefaultRouter()
bus_router.register(r'video', VideoNeededViewSet, basename='video')


manager_router = DefaultRouter()
manager_router.register(r'video', ManageVideoNeededViewSet, basename='video')

urlpatterns = [
    # path('admin/', admin.site.urls),
    path(r'client/', include(client_router.urls)),
    path(r'bus/', include(bus_router.urls)),
    path(r'manager/', include(manager_router.urls)),
    path(r'test/', test.as_view()),
]
