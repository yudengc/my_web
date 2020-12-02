from rest_framework import serializers

from application.models import Video
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


class VideoCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Video
        fields = ('video_url', 'cover')
