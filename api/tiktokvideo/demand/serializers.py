from qiniu import Auth
from rest_framework import serializers

from demand.models import VideoNeeded, HomePageVideo
from tiktokvideo.base import QINIU_SECRET_KEY, QINIU_ACCESS_KEY


class VideoNeededSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoNeeded
        fields = '__all__'


class ManageVideoNeededSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField(read_only=True)
    bus_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VideoNeeded
        fields = '__all__'

    def get_bus_name(self, obj):
        return obj.uid.user_business.bus_name

    def get_username(self, obj):
        return obj.uid.username


class ClientVideoNeededSerializer(serializers.ModelSerializer):
    video_num_at_least = serializers.SerializerMethodField(read_only=True)
    video_size = serializers.SerializerMethodField(read_only=True)
    clarity = serializers.SerializerMethodField(read_only=True)
    model_needed = serializers.SerializerMethodField(read_only=True)
    model_occur_rate = serializers.SerializerMethodField(read_only=True)
    sold_out = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VideoNeeded
        fields = (
            'id', 'title', 'is_return', 'video_num_at_least',
            'goods_channel', 'goods_link', 'goods_images',
            'video_size', 'clarity', 'model_needed',
            'model_occur_rate', 'model_age_range', 'goods_channel',
            'sold_out', 'goods_title'
        )

    def get_video_num_at_least(self, obj):
        if obj.order_num_remained == 0:
            return obj.order_video_slice[0].get('num')
        else:
            tmp = [i for i in obj.order_video_slice if i.get('remain') == 1]
            return tmp[0].get('num')

    def get_video_size(self, obj):
        return obj.get_video_size_display()

    def get_clarity(self, obj):
        return obj.get_clarity_display()

    def get_model_needed(self, obj):
        return obj.get_model_needed_display()

    def get_model_occur_rate(self, obj):
        return obj.get_model_occur_rate_display()

    def get_model_age_range(self, obj):
        return obj.get_model_age_range()

    def get_sold_out(self, obj):
        if obj.order_num_remained == 0:
            return True
        return False


class ClientVideoNeededDetailSerializer(serializers.ModelSerializer):
    video_size = serializers.SerializerMethodField(read_only=True)
    clarity = serializers.SerializerMethodField(read_only=True)
    model_needed = serializers.SerializerMethodField(read_only=True)
    model_occur_rate = serializers.SerializerMethodField(read_only=True)
    model_age_range = serializers.SerializerMethodField(read_only=True)
    model_figure = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VideoNeeded
        fields = (
            'id', 'title', 'order_num_remained', 'is_return', 'create_time',
            'order_video_slice', 'video_size', 'clarity', 'model_needed',
            'model_occur_rate', 'model_age_range', 'model_figure', 'desc',
            'example1', 'example2', 'example3', 'goods_link', 'goods_images',
            'goods_channel', 'attraction'
        )

    def get_video_size(self, obj):
        return obj.get_video_size_display()

    def get_clarity(self, obj):
        return obj.get_clarity_display()

    def get_model_needed(self, obj):
        return obj.get_model_needed_display()

    def get_model_occur_rate(self, obj):
        return obj.get_model_needed_display()

    def get_model_age_range(self, obj):
        return obj.get_model_age_range_display()

    def get_model_figure(self, obj):
        return obj.get_model_figure_display()


class HomePageVideoSerializer(serializers.ModelSerializer):
    video_download_link = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = HomePageVideo
        fields = '__all__'

    def get_video_download_link(self, obj):
        auth = Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)
        try:
            return auth.private_download_url(obj.video_link, expires=315360000) if obj.video else ''
        except:
            return ''
