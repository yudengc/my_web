from rest_framework import viewsets

from config.models import CustomerService, GoodsCategory
from config.serializers import CustomerServiceSerializer, GoodsCategorySerializer
from libs.common.permission import ManagerPermission, SalesmanPermission, AllowAny, AdminPermission


class CustomerServiceViewSet(viewsets.ModelViewSet):
    """客服"""
    permission_classes = (SalesmanPermission,)
    queryset = CustomerService.objects.all()
    serializer_class = CustomerServiceSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = (AllowAny, )
        return super().get_permissions()


class GoodsCategoryViewSet(viewsets.ModelViewSet):
    """
    商品品类
    """
    permission_classes = (AdminPermission,)
    queryset = GoodsCategory.objects.all()
    serializer_class = GoodsCategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = (ManagerPermission,)
        return super().get_permissions()

