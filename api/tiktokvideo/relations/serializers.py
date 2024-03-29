from rest_framework import serializers

from relations.models import InviteRelationManager
from transaction.models import UserPackageRelation, OrderInfo, Package, UserPackageRecord
from users.models import Users, UserBusiness


class BusinessInfoSerializer(serializers.ModelSerializer):
    bus_name = serializers.SerializerMethodField()
    has_package = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ('id', 'username', 'date_created', 'bus_name', 'has_package', 'status')

    def get_bus_name(self, obj):
        # 改成微信昵称，返回字段不变
        return obj.auth_base.nickname if obj.auth_base else ''

    def get_has_package(self, obj):
        # return UserPackageRelation.objects.filter(uid=obj).exists()
        return UserPackageRecord.objects.filter(uid=obj).exists()

    def get_status(self, obj):
        if UserPackageRecord.objects.filter(uid=obj, status=UserPackageRecord.PROCESSED).exists():
            return UserPackageRecord.PROCESSED
        else:
            return UserPackageRecord.UNTREATED
        # if UserPackageRelation.objects.filter(uid=obj, status=UserPackageRelation.PROCESSED).exists():
        #     return UserPackageRelation.PROCESSED
        # else:
        #     return UserPackageRelation.UNTREATED


class MyRelationSerializer(serializers.ModelSerializer):
    """
    我的邀请
    """
    invitee = BusinessInfoSerializer()

    class Meta:
        model = InviteRelationManager
        fields = ('invitee',)

    def to_representation(self, instance):
        return super(MyRelationSerializer, self).to_representation(instance).get('invitee')


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
        # 改成微信昵称，返回字段不变
        return obj.uid.auth_base.nickname if obj.uid.auth_base else ''

    def get_username(self, obj):
        return obj.uid.username

    def get_package_title(self, obj):
        return Package.objects.get(id=obj.parm_id).package_title


class MyRelationInfoManagerSerializer(serializers.ModelSerializer):
    """
    我的邀请
    """
    invitee_username = serializers.CharField(source='invitee.username')
    invitee_nickname = serializers.CharField(source='invitee.auth_base.nickname')
    inviter_username = serializers.CharField(source='inviter.username')
    inviter_nickname = serializers.CharField(source='inviter.auth_base.nickname')
    salesman_username = serializers.SerializerMethodField()
    salesman_name = serializers.SerializerMethodField()

    class Meta:
        model = InviteRelationManager
        fields = ('invitee_username', 'invitee_nickname', 'inviter_username', 'inviter_nickname',
                  'salesman_username', 'salesman_name', 'date_created')

    def get_salesman_username(self, obj):
        return obj.salesman.username if obj.salesman else None

    def get_salesman_name(self, obj):
        return obj.salesman.salesman_name if obj.salesman else None
