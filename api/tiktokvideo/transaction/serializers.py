from rest_framework import serializers

from transaction.models import Package, UserPackageRelation


class PackageSerializer(serializers.ModelSerializer):
    """
    套餐包
    """

    class Meta:
        model = Package
        exclude = ('uid', 'date_updated', 'deleted', 'status', 'date_created')


class MyPackageSerializer(serializers.ModelSerializer):
    """
    个人套餐包详情
    """
    package = PackageSerializer()

    class Meta:
        model = UserPackageRelation
        exclude = ('uid', 'date_updated', 'deleted', 'order', 'id')


class PackageRecordSerializer(serializers.ModelSerializer):
    """
    套餐包订单详情
    """
    order = serializers.SerializerMethodField()

    class Meta:
        model = UserPackageRelation
        fields = ('order',)

    def get_order(self, obj):
        data_dic = {}
        order_obj = obj.order
        data_dic['id'] = order_obj.id
        data_dic['package_title'] = obj.package.package_title
        data_dic['amount'] = order_obj.amount
        data_dic['order_num'] = order_obj.out_trade_no
        data_dic['date_payed'] = order_obj.date_payed
        return data_dic

    def to_representation(self, instance):
        return super().to_representation(instance).get('order')
