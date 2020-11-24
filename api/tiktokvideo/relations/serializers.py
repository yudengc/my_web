from rest_framework import serializers

from relations.models import InviteRelationManager
from transaction.models import UserPackageRelation, OrderInfo, Package
from users.models import Users, UserBusiness


class BusinessInfoSerializer(serializers.ModelSerializer):
    bus_name = serializers.SerializerMethodField()
    has_package = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ('id', 'username', 'date_created', 'bus_name', 'has_package')

    def get_bus_name(self, obj):
        bus_obj = UserBusiness.objects.filter(uid=obj).first()
        return bus_obj.bus_name if bus_obj else ''

    def get_has_package(self, obj):
        return UserPackageRelation.objects.filter(uid=obj).exists()


class MyRelationSerializer(serializers.ModelSerializer):
    """
    我的邀请
    """
    invitee = BusinessInfoSerializer()

    class Meta:
        model = InviteRelationManager
        fields = ('invitee', 'status')

    def to_representation(self, instance):
        data = super(MyRelationSerializer, self).to_representation(instance).get('invitee')
        data['status'] = super(MyRelationSerializer, self).to_representation(instance).get('status')
        return data


# class MyRecordsSerializer(serializers.ModelSerializer):
#     """
#     商家付费记录
#     """
#     invitee = serializers.SerializerMethodField()
#
#     class Meta:
#         model = InviteRelationManager
#         fields = ('invitee', )
#
#     def get_invitee(self, obj):
#         lis = []
#         invitee = obj.invitee
#         for order in OrderInfo.objects.filter(uid=invitee, status=OrderInfo.SUCCESS, tran_type=OrderInfo.PACKAGE).all():
#             lis.append({'out_trade_no': order.out_trade_no,
#                         'date_payed': order.date_payed,
#                         'amount': order.amount,
#                         'bus_name': invitee.user_business.bus_name,
#                         'username': invitee.username,
#                         'package_title': Package.objects.get(id=order.parm_id).package_title})
#         return lis
#
#     def to_representation(self, instance):
#         return super(MyRecordsSerializer, self).to_representation(instance).get('invitee')


class MyRecordsSerializer(serializers.ModelSerializer):
    """
    商家付费记录
    """
    bus_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    package_title = serializers.SerializerMethodField()

    class Meta:
        model = OrderInfo
        fields = ('id', 'out_trade_no', 'date_payed', 'amount', 'bus_name', 'username', 'package_title')

    def get_bus_name(self, obj):
        return obj.uid.user_business.bus_name

    def get_username(self, obj):
        return obj.uid.username

    def get_package_title(self, obj):
        return Package.objects.get(id=obj.parm_id).package_title
