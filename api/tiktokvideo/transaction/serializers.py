from rest_framework import serializers

from relations.models import InviteRelationManager
from transaction.models import Package, UserPackageRelation, OrderInfo, UserPackageRecord
from users.models import UserBusiness
from users.serializers import BusinessInfoManagerSerializer


class PackageCommonSerializer(serializers.ModelSerializer):
    """
    套餐包订单用的套餐记录序列化器
    """
    class Meta:
        model = Package
        fields = '__all__'


class PackageSerializer(serializers.ModelSerializer):
    """
    套餐包
    """

    class Meta:
        model = Package
        exclude = ('uid', 'date_updated', 'status', 'date_created')


class MyPackageSerializer(serializers.ModelSerializer):
    """
    个人套餐包详情
    """
    expiration_time = serializers.SerializerMethodField()

    class Meta:
        model = UserPackageRecord
        exclude = ('package_id', 'date_updated', 'buy_video_num', 'video_num', 'status')

    def get_expiration_time(self, obj):
        r_obj = UserPackageRelation.objects.filter(package_id=obj.package_id, uid=self.context['request'].user).first()
        if r_obj:
            return r_obj.expiration_time
        return None


# class PackageRecordSerializer(serializers.ModelSerializer):
#     """
#     套餐包订单详情
#     """
#     order = serializers.SerializerMethodField()
#
#     class Meta:
#         model = UserPackageRelation
#         fields = ('order',)
#
#     def get_order(self, obj):
#         data_dic = {}
#         order_obj = obj.order
#         data_dic['id'] = order_obj.id
#         data_dic['package_title'] = obj.package.package_title
#         data_dic['amount'] = order_obj.amount
#         data_dic['order_num'] = order_obj.out_trade_no
#         data_dic['date_payed'] = order_obj.date_payed
#         return data_dic
#
#     def to_representation(self, instance):
#         return super().to_representation(instance).get('order')


class OrderInfoSerializer(serializers.ModelSerializer):
    package_title = serializers.SerializerMethodField()

    class Meta:
        model = OrderInfo
        fields = ('id', 'amount', 'out_trade_no', 'date_payed', 'package_title')

    def get_package_title(self, obj):
        return Package.objects.get(id=obj.parm_id).package_title


class PackageManagerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Package
        exclude = ('date_updated', 'uid')


# class UserPackageRelationManagerSerializer(serializers.ModelSerializer):
#     username = serializers.CharField(source='uid.username')
#     nickname = serializers.CharField(source='uid.auth_base.nickname')
#     package_title = serializers.CharField(source='package.package_title')
#     package_amount = serializers.CharField(source='package.package_amount')
#     salesman = serializers.SerializerMethodField()
#     bus_info = serializers.SerializerMethodField()
#
#     class Meta:
#         model = UserPackageRelation
#         fields = ('id', 'username', 'nickname', 'package_title', 'package_amount', 'status', 'date_created',
#                   'salesman', 'bus_info')
#
#     def get_salesman(self, obj):
#         r_obj = InviteRelationManager.objects.filter(invitee=obj.uid).first()
#         if r_obj:
#             salesman = r_obj.salesman
#             if salesman:
#                 return {'salesman_username': salesman.username, 'salesman_name': salesman.salesman_name}
#             return {'salesman_username': None, 'salesman_name': None}
#         else:
#             return {'salesman_username': None, 'salesman_name': None}
#
#     def get_bus_info(self, obj):
#         bus_obj = UserBusiness.objects.filter(uid=obj.uid).first()
#         if bus_obj:
#             return BusinessInfoManagerSerializer(bus_obj).data
#         else:
#             return None


class UserPackageRecordManagerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='uid.username')
    nickname = serializers.CharField(source='uid.auth_base.nickname')
    salesman = serializers.SerializerMethodField()
    bus_info = serializers.SerializerMethodField()

    class Meta:
        model = UserPackageRecord
        fields = ('id', 'username', 'nickname', 'package_title', 'package_amount', 'status', 'date_created',
                  'salesman', 'bus_info')

    def get_salesman(self, obj):
        r_obj = InviteRelationManager.objects.filter(invitee=obj.uid).first()
        if r_obj:
            salesman = r_obj.salesman
            if salesman:
                return {'salesman_username': salesman.username, 'salesman_name': salesman.salesman_name}
            return {'salesman_username': None, 'salesman_name': None}
        else:
            return {'salesman_username': None, 'salesman_name': None}

    def get_bus_info(self, obj):
        bus_obj = UserBusiness.objects.filter(uid=obj.uid).first()
        if bus_obj:
            return BusinessInfoManagerSerializer(bus_obj).data
        else:
            return None


# class UserPackageRelationManagerUpdateSerializer(serializers.ModelSerializer):
#
#     class Meta:
#         model = UserPackageRelation
#         fields = ('status', )


class UserPackageRecordManagerUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserPackageRecord
        fields = ('status', )
