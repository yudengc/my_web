from rest_framework import serializers

from application.models import VideoOrder
from demand.models import VideoNeeded


class VideoApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoOrder
        fields = (
            'user', 'demand', 'num_selected', 'receiver_name', 'receiver_phone', 'receiver_province', 'receiver_city',
            'receiver_district', 'receiver_location', 'creator_remark', 'reward'
        )


class VNeededSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoNeeded
        fields = (
            'id', 'title', 'goods_link', 'goods_images', 'goods_channel', 'is_return', 'video_size', 'clarity',
            'model_needed', 'model_occur_rate', 'model_age_range', 'model_figure'
        )


class VideoApplicationListSerializer(serializers.ModelSerializer):
    """我的订单"""
    demand = VNeededSerializer()

    class Meta:
        model = VideoOrder
        fields = (
            'id', 'status', 'date_created', 'num_selected', 'sample_count', 'demand'
        )


class VideoApplicationRetrieveSerializer(serializers.ModelSerializer):
    """我的订单详情"""
    demand = VNeededSerializer()
    return_sample = serializers.SerializerMethodField()

    class Meta:
        model = VideoOrder
        fields = (
            'id', 'status', 'date_created', 'num_selected', 'receiver_name', 'receiver_phone', 'receiver_province',
            'receiver_city', 'receiver_district', 'receiver_location', 'company', 'express', 'creator_remark',
            'check_time', 'send_time', 'done_time', 'close_time', 'date_created', 'demand', 'return_sample',
        )

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

