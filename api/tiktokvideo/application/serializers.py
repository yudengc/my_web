from rest_framework import serializers

from application.models import VideoOrder
from demand.models import VideoNeeded


class VideoApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoOrder
        fields = (
            'user', 'demand', 'num_selected', 'receiver_name', 'receiver_phone', 'receiver_province', 'receiver_city',
            'receiver_district', 'receiver_location', 'creator_remark', 'reward', 'goods_title', 'goods_link',
            'goods_images', 'goods_channel', 'is_return'
        )


class VNeededSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoNeeded
        fields = (
            'id', 'title', 'video_size', 'clarity', 'model_needed', 'model_occur_rate',
            'model_age_range', 'model_figure'
        )


class VideoApplicationListSerializer(serializers.ModelSerializer):
    """我的订单"""
    demand = VNeededSerializer()
    total_reward = serializers.SerializerMethodField()

    class Meta:
        model = VideoOrder
        fields = (
            'id', 'status', 'date_created', 'num_selected', 'sample_count', 'is_return',
            'goods_link', 'goods_images', 'goods_channel', 'goods_title', 'total_reward', 'demand',
        )

    def get_total_reward(self, obj):
        # 订单可得松子
        return obj.reward * obj.num_selected


class VideoApplicationRetrieveSerializer(serializers.ModelSerializer):
    """我的订单详情"""
    demand = VNeededSerializer()
    return_sample = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = VideoOrder
        fields = (
            'id', 'status', 'date_created', 'num_selected', 'is_return', 'goods_link', 'goods_images', 'goods_channel',
            'goods_title', 'receiver_name', 'receiver_phone', 'location', 'company', 'express', 'creator_remark',
            'check_time', 'send_time', 'done_time', 'close_time', 'date_created', 'demand', 'return_sample',
        )

    def get_location(self, obj):
        tmp = [obj.receiver_province, obj.receiver_city, obj.receiver_district, obj.receiver_location]
        return ''.join([i for i in tmp if i])

    def get_return_sample(self, obj):
        # 返样信息
        demand_obj = obj.demand
        if obj.is_return and obj.status == VideoOrder.WAIT_RETURN:
            location = demand_obj.receiver_province + demand_obj.receiver_city + \
                       demand_obj.receiver_district + demand_obj.receiver_location
            return dict(receiver_name=demand_obj.receiver_name,
                        receiver_phone=demand_obj.receiver_phone,
                        location=location,
                        return_company=obj.return_company,
                        return_express=obj.return_express)
        return None


class BusApplicationSerializer(VideoApplicationRetrieveSerializer):
    video_download = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VideoOrder
        fields = '__all__'

    def get_video_download(self, obj):
        return obj.order_video.all()


class VideoApplicationManagerListSerializer(VideoApplicationRetrieveSerializer):
    title = serializers.CharField(source='demand.title', read_only=True)
    bus_username = serializers.CharField(source='demand.uid.username', read_only=True)
    bus_name = serializers.SerializerMethodField()
    creator_username = serializers.CharField(source='user.username')
    creator_nickname = serializers.CharField(source='user.auth_base.nickname')
    is_signed = serializers.BooleanField(source='user.user_creator.is_signed')

    class Meta:
        model = VideoOrder
        fields = ('id', 'title', 'bus_username', 'bus_name', 'status', 'creator_username', 'creator_nickname',
                  'is_signed', 'reward', 'is_return', 'date_created', 'done_time')

    def get_bus_name(self, obj):
        user_business = obj.demand.uid.user_business
        return user_business.bus_name if user_business else None


class VideoApplicationManagerRetrieveSerializer(VideoApplicationRetrieveSerializer):
    title = serializers.CharField(source='demand.title', read_only=True)
    bus_username = serializers.CharField(source='demand.uid.username', read_only=True)
    bus_name = serializers.SerializerMethodField()
    creator_username = serializers.CharField(source='user.username')
    creator_nickname = serializers.CharField(source='user.auth_base.nickname')
    is_signed = serializers.BooleanField(source='user.user_creator.is_signed')
    location = serializers.SerializerMethodField()
    creator_receiver_name = serializers.CharField(source='demand.receiver_name')

    class Meta:
        model = VideoOrder
        fields = ('id', 'title', 'bus_username', 'bus_name', 'num_selected', 'goods_title', 'goods_link',
                  'goods_images', 'goods_channel', 'is_return', 'receiver_name', 'receiver_phone', 'location',
                  'creator_nickname', 'creator_username', 'reward', 'is_signed',
                  'creator_receiver_name',
                  'date_created', 'done_time', 'status', )

    def get_location(self, obj):
        return obj.receiver_province + obj.receiver_city + obj.receiver_district + obj.receiver_location

    def get_bus_name(self, obj):
        user_business = obj.demand.uid.user_business
        return user_business.bus_name if user_business else None