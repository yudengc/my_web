from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from config.views import CustomerServiceViewSet, GoodsCategoryViewSet, QiNiuTokenView, VideoViewSet, VersionView

app_name = "config"

router = DefaultRouter()
router.register(r'customer-service', CustomerServiceViewSet, basename='login')
router.register(r'goods-category', GoodsCategoryViewSet, basename='category')
router.register(r'upload-video', VideoViewSet, basename='upload_video')


urlpatterns = [
    path('admin/', admin.site.urls),
    path(r'', include(router.urls)),
    path(r'approve/', QiNiuTokenView.as_view()),
    path(r'version/', VersionView.as_view()),
]
