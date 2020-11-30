from rest_framework import viewsets

from config.models import CustomerService, GoodsCategory
from config.serializers import CustomerServiceSerializer, GoodsCategorySerializer, ManageGoodsCategorySerializer
from libs.common.permission import ManagerPermission, SalesmanPermission, AllowAny, AdminPermission, is_admin


class CustomerServiceViewSet(viewsets.ModelViewSet):
    """客服"""
    permission_classes = (AdminPermission,)
    queryset = CustomerService.objects.order_by('-date_created')
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

    def get_serializer_class(self):
        if is_admin(self.request):
            return ManageGoodsCategorySerializer
        return super().get_serializer_class()



