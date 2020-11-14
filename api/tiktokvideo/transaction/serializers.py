from rest_framework import serializers

from transaction.models import Package, UserPackageRelation


class PackageSerializer(serializers.ModelSerializer):
    """
    套餐包
    """

    class Meta:
        model = Package
        exclude = ('uid', 'date_updated')


class PackageDetailSerializer(serializers.ModelSerializer):
    """
    个人套餐包详情
    """
    package = PackageSerializer()

    class Meta:
        model = UserPackageRelation
        exclude = ('uid', 'date_updated',)
