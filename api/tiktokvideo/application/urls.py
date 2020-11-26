from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = "application"

router = DefaultRouter()


urlpatterns = [
    # path('admin/', admin.site.urls),
    path(r'', include(router.urls)),


]
