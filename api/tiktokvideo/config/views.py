from rest_framework import viewsets

from config.models import CustomerService
from config.serializers import CustomerServiceSerializer
from libs.common.permission import ManagerPermission, SalesmanPermission, AllowAny


class CustomerServiceViewSet(viewsets.ModelViewSet):
    """客服"""
    permission_classes = (SalesmanPermission,)
    queryset = CustomerService.objects.all()
    serializer_class = CustomerServiceSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = (AllowAny, )
        return super().get_permissions()

