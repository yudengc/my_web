from rest_framework import serializers

from relations.models import InviteRelationManager
from transaction.models import UserPackageRelation
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


class MyRecordsSerializer(serializers.ModelSerializer):
    """
    商家付费记录
    """
    invitee = serializers.SerializerMethodField()

    class Meta:
        model = InviteRelationManager
        fields = ('invitee', )

    def get_invitee(self, obj):
        lis = []
        for i in UserPackageRelation.objects.filter(uid=obj.invitee).select_related('order', 'package').all():
            order = i.order
            lis.append({'out_trade_no': order.out_trade_no,
                        'date_payed': order.date_payed,
                        'amount': order.amount,
                        'bus_name': obj.invitee.user_business.bus_name,
                        'username': obj.invitee.username,
                        'package_title': i.package.package_title})
        return lis

    def to_representation(self, instance):
        return super(MyRecordsSerializer, self).to_representation(instance).get('invitee')

