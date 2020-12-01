import subprocess

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from config.models import CustomerService, GoodsCategory
from config.serializers import CustomerServiceSerializer, GoodsCategorySerializer, ManageGoodsCategorySerializer
from libs.common.permission import ManagerPermission, SalesmanPermission, AllowAny, AdminPermission, is_admin
from libs.services import get_qi_niu_token


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

    def get_serializer_class(self):
        if is_admin(self.request):
            return ManageGoodsCategorySerializer
        return super().get_serializer_class()

    def destroy(self, request, *args, **kwargs):
        s = """find */migrations/ -name '*.py'|xargs -i grep -E 'config.GoodsCategory' {} -B 1|grep -E '^[ 
                \t]*name=|config.GoodsCategory' """
        related_name_list = subprocess.getoutput(s).replace(' ', '').split('\n')
        # relate_name: 字段名
        result_dict = {}
        flag = 0
        for i in related_name_list:
            if i.startswith('name'):
                name = i.split('=')[1].replace('\'', '').split(',')[0]
                flag = 1
                continue
            else:
                if flag == 1:
                    related_name = i.split('related_name=')[1].replace('\'', '').split(',')[0]
                    result_dict[related_name] = name
                    flag = 0
                else:
                    _name = i.replace('(', '').replace('\'', '').split(',')[0]
                    related_name = i.replace('(', '').replace('\'', '').split('related_name=')[1].split(',')[0]
                    result_dict[related_name] = _name

        instance = self.get_object()
        for related_name in result_dict:
            if getattr(instance, related_name).all().exists():
                return Response({"detail": "该商品类目已关联其他项目数据, 不可删除"}, status=status.HTTP_400_BAD_REQUEST)
        super().perform_destroy(instance)
        return super().destroy(request, *args, **kwargs)


class QiNiuTokenView(APIView):
    """
    获取七牛云token
    """
    permission_classes = [ManagerPermission]

    def post(self, request):
        return Response(
            {
                "token": get_qi_niu_token(),
                'expires': 3600,
            }
        )
