from django.urls import path, include
from rest_framework.routers import DefaultRouter

from relations.views import MyRelationInfoViewSet

app_name = "relations"

router = DefaultRouter()
router.register(r'my-relation', MyRelationInfoViewSet, basename='my_relation')

urlpatterns = [
    path(r'', include(router.urls)),

]
