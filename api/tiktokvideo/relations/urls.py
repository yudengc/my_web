from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = "relations"

router = DefaultRouter()

urlpatterns = [
    path(r'', include(router.urls)),

]