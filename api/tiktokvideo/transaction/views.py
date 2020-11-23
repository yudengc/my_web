import logging
import threading
import xml.etree.ElementTree as et
from datetime import datetime
from decimal import Decimal

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from transaction.serializers import PackageSerializer, PackageRecordSerializer, MyPackageSerializer
from transaction.tasks import update_order_status
from transaction.models import OrderInfo, UserPackageRelation
from libs.common.pay import WeChatPay
from libs.common.permission import ManagerPermission, AllowAny, SalesmanPermission
from libs.common.utils import get_ip
from transaction.models import Package

logger = logging.getLogger()


class WeChatPayViewSet(APIView):
    """微信支付"""
    permission_classes = (ManagerPermission,)

    def post(self, request):
        request_data = request.data
        t_type = request_data.get('type', '0')  # 0:购买套餐
        p_id = request_data.get('p_id', None)   # 购买的商品对应的id
        if not p_id:
            return Response({"detail": "缺少参数配置ID"}, status=status.HTTP_400_BAD_REQUEST)
        if t_type in ['0', 0]:
            package_ps = Package.objects.filter(id=p_id)
            if not package_ps.exists():
                return Response({"detail": '该套餐不存在'}, status=status.HTTP_400_BAD_REQUEST)
            money = package_ps.first().package_amount
        else:
            return Response({"detail": 't_type错误'}, status=status.HTTP_400_BAD_REQUEST)

        order = OrderInfo.create_order(request.user, money, t_type, p_id)
        # 获取客户端ip
        client_ip = get_ip(request)
        attach = str(request.user.uid) + '_' + str(p_id)  # 自定义参数，回调要用

        data = WeChatPay().pay(Decimal(str(money)) * Decimal('0.01'),
                               client_ip, order.out_trade_no, request.user.openid, attach)
        # print(data)
        if data:
            return Response(data, status=status.HTTP_200_OK)
        return Response("请求支付失败", status=status.HTTP_400_BAD_REQUEST)


class WeChatPayBackViewSet(APIView):
    """微信支付回调"""

    permission_classes = (AllowAny,)

    def post(self, request):
        _xml = request.body
        # 拿到微信发送的xml请求 即微信支付后的回调内容
        xml = str(_xml, encoding="utf-8")
        return_dict = {}
        tree = et.fromstring(xml)
        # xml 解析
        return_code = tree.find("return_code").text
        logger.info(f'微信支付回调结果{return_code}')
        attach = tree.find("attach").text
        try:
            if return_code == 'FAIL':
                # 官方发出错误
                return_dict['message'] = '支付失败'
            elif return_code == 'SUCCESS':
                # 订单号 out_trade_no
                out_trade_no = tree.find("out_trade_no").text
                # 修改订单状态
                # update_order_status.delay(out_trade_no, datetime.now(), attach)
                threading.Thread(target=update_order_status,
                                 args=(out_trade_no, datetime.now(), attach)).start()
                return HttpResponse(
                    '<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>')
        except Exception as e:
            return HttpResponse(return_dict)


class PayCancelViewSet(APIView):
    permission_classes = (ManagerPermission,)

    def put(self, request):
        """用户取消支付"""
        order_number = request.data.get('order_number')
        OrderInfo.objects.filter(out_trade_no=order_number, status=0).update(status=2)
        return Response(status=status.HTTP_201_CREATED)


class PackageViewSet(viewsets.ReadOnlyModelViewSet):
    """套餐客户端"""
    permission_classes = (ManagerPermission,)
    queryset = Package.objects.filter(status=Package.PUBLISHED, expiration_time__gte=datetime.now())
    serializer_class = PackageSerializer

    def list(self, request, *args, **kwargs):
        # 不需要分页
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class MyPackageViewSet(viewsets.ModelViewSet):
    """我的套餐"""
    permission_classes = (ManagerPermission,)
    serializer_class = MyPackageSerializer

    def get_queryset(self):
        self.queryset = UserPackageRelation.objects.filter(uid=self.request.user).select_related('package')
        return super().get_queryset()

    @action(methods=['get'], detail=False, serializer_class=PackageRecordSerializer)
    def records(self, request, *args, **kwargs):
        # 套餐购买记录
        return super().list(request, *args, **kwargs)



