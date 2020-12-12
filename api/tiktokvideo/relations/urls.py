from django.urls import path, include
from rest_framework.routers import DefaultRouter

from relations.views import MyRelationInfoViewSet, MyRelationInfoManagerViewSet

app_name = "relations"

router = DefaultRouter()
router.register(r'my-relation', MyRelationInfoViewSet, basename='my_relation')

manager_router = DefaultRouter()
manager_router.register(r'relation', MyRelationInfoManagerViewSet, basename='relation')


urlpatterns = [
    path(r'', include(router.urls)),
    path(r'manager/', include(manager_router.urls)),

]
