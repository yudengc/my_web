from rest_framework import serializers

from config.models import CustomerService, GoodsCategory


class CustomerServiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerService
        exclude = ('date_created', 'date_updated')


class GoodsCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsCategory
        exclude = ('date_created', 'date_updated')


class ManageGoodsCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsCategory
        fields = '__all__'
