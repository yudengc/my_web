import logging
import threading
import xml.etree.ElementTree as et
from datetime import datetime
from decimal import Decimal

from django.db.transaction import atomic
from django.http import HttpResponse
from django_filters import rest_framework
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, filters, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from transaction.filter import UserPackageRelationManagerFilter
from transaction.serializers import PackageSerializer, MyPackageSerializer, OrderInfoSerializer, \
    PackageManagerSerializer, \
    PackageCommonSerializer, UserPackageRecordManagerSerializer, UserPackageRecordManagerUpdateSerializer
from transaction.tasks import update_order_status
from transaction.models import OrderInfo, UserPackageRelation, UserPackageRecord
from libs.common.pay import WeChatPay
from libs.common.permission import ManagerPermission, AllowAny, SalesmanPermission, AdminPermission
from libs.common.utils import get_ip
from transaction.models import Package
from users.models import Users

logger = logging.getLogger()


class WeChatPayViewSet(APIView):
    """微信支付"""
    permission_classes = (ManagerPermission,)

    def post(self, request):
        if request.user.status == Users.FROZEN:
            return Response({'detail': '账户被冻结，请联系客服处理', 'code': 444}, status=status.HTTP_400_BAD_REQUEST)
        request_data = request.data
        t_type = request_data.get('type', '0')  # 0:购买套餐
        p_id = request_data.get('p_id', None)   # 购买的商品对应的id
        if not p_id:
            return Response({"detail": "缺少参数配置ID"}, status=status.HTTP_400_BAD_REQUEST)
        if t_type in ['0', 0]:
            package_qs = Package.objects.filter(id=p_id)
            if not package_qs.exists():
                return Response({"detail": '该套餐不存在'}, status=status.HTTP_400_BAD_REQUEST)
            money = package_qs.first().package_amount
            order = OrderInfo.create_order(request.user, money, t_type, p_id)
            order.pkg_value = dict(PackageCommonSerializer(package_qs, many=True).data[0])
            order.save()
        else:
            return Response({"detail": 't_type错误'}, status=status.HTTP_400_BAD_REQUEST)

        # 获取客户端ip
        client_ip = get_ip(request)
        attach = str(request.user.uid) + '_' + str(p_id)  # 自定义参数，回调要用

        money = int(money * Decimal('100'))  # 微信单位是分(int)
        data = WeChatPay().pay(money, client_ip, order.out_trade_no, request.user.openid, attach)
        # print(data)
        if data:
            return Response(data, status=status.HTTP_200_OK)
        return Response({"detail": "请求支付失败"}, status=status.HTTP_400_BAD_REQUEST)


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
                update_order_status.delay(out_trade_no, datetime.now(), attach)
                # threading.Thread(target=update_order_status,
                #                  args=(out_trade_no, datetime.now(), attach)).start()
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
    queryset = Package.objects.filter(status=Package.PUBLISHED).order_by('package_amount')
    serializer_class = PackageSerializer

    def list(self, request, *args, **kwargs):
        # 不需要分页
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# class MyPackageViewSet(viewsets.ModelViewSet):
#     """我的套餐"""
#     permission_classes = (ManagerPermission,)
#     serializer_class = MyPackageSerializer
#
#     def get_queryset(self):
#         self.queryset = UserPackageRelation.objects.filter(uid=self.request.user).select_related('package')
#         return super().get_queryset()


class MyPackageViewSet(viewsets.ModelViewSet):
    """我的套餐"""
    permission_classes = (ManagerPermission,)
    serializer_class = MyPackageSerializer

    def get_queryset(self):
        self.queryset = UserPackageRecord.objects.filter(uid=self.request.user)
        return super().get_queryset()


class OrderInfoViewSet(viewsets.ReadOnlyModelViewSet):
    """我的购买记录"""
    permission_classes = (ManagerPermission,)
    serializer_class = OrderInfoSerializer

    def get_queryset(self):
        self.queryset = OrderInfo.objects.filter(uid=self.request.user, status=OrderInfo.SUCCESS)
        return super().get_queryset()


class PackageManagerViewSet(mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            GenericViewSet):
    """商家套餐后台"""
    permission_classes = (AdminPermission,)
    serializer_class = PackageManagerSerializer
    queryset = Package.objects.all()
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = ('status', )
    search_fields = ('package_title',)


# class UserPackageRelationManagerViewSet(mixins.RetrieveModelMixin,
#                                         mixins.UpdateModelMixin,
#                                         mixins.ListModelMixin,
#                                         GenericViewSet):
#     """套餐购买记录后台"""
#     permission_classes = (AdminPermission,)
#     serializer_class = UserPackageRelationManagerSerializer
#     queryset = UserPackageRelation.objects.all()
#     filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
#     filter_class = UserPackageRelationManagerFilter
#     search_fields = ('uid__username', 'uid__auth_base__nickname', 'uid__user_salesman__salesman__username',
#                      'uid__user_salesman__salesman__salesman_name')
#
#     def get_serializer_class(self):
#         if self.action in ['update', 'partial_update']:
#             self.serializer_class = UserPackageRelationManagerUpdateSerializer
#         return super().get_serializer_class()


class UserPackageRecordManagerViewSet(mixins.RetrieveModelMixin,
                                      mixins.UpdateModelMixin,
                                      mixins.ListModelMixin,
                                      GenericViewSet):
    """套餐购买记录后台"""
    permission_classes = (AdminPermission,)
    serializer_class = UserPackageRecordManagerSerializer
    queryset = UserPackageRecord.objects.all()
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = UserPackageRelationManagerFilter
    search_fields = ('uid__username', 'uid__auth_base__nickname', 'uid__user_salesman__salesman__username',
                     'uid__user_salesman__salesman__salesman_name')

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            self.serializer_class = UserPackageRecordManagerUpdateSerializer
        return super().get_serializer_class()


class AView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        u_qs = UserPackageRelation.objects.all()
        for u_obj in u_qs:
            package_obj = u_obj.package
            if not UserPackageRecord.objects.filter(package_id=package_obj.id, uid=u_obj.uid).exists():
                UserPackageRecord.objects.create(uid=u_obj.uid,
                                                 package_id=package_obj.id,
                                                 package_title=package_obj.package_title,
                                                 package_amount=package_obj.package_amount,
                                                 buy_video_num=package_obj.buy_video_num,
                                                 video_num=package_obj.video_num,
                                                 package_content=package_obj.package_content,
                                                 expiration=package_obj.expiration,
                                                 date_created=u_obj.date_created)
        return Response('ok')
