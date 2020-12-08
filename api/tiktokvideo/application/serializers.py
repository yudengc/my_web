import logging
import traceback

from qiniu import Auth
from rest_framework import serializers

from application.models import VideoOrder, VideoOrderDetail, Video
from demand.models import VideoNeeded
from tiktokvideo.base import QINIU_ACCESS_KEY, QINIU_SECRET_KEY

logger = logging.getLogger()


class VideoApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoOrder
        fields = (
            'id', 'user', 'demand', 'num_selected', 'creator_remark', 'reward', 'is_return'
        )
        # fields = (
        #     'user', 'demand', 'num_selected', 'receiver_name', 'receiver_phone', 'receiver_province', 'receiver_city',
        #     'receiver_district', 'receiver_location', 'creator_remark', 'reward', 'goods_title', 'goods_link',
        #     'goods_images', 'goods_channel', 'is_return'
        # )


class VNeededSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoNeeded
        fields = (
            'id', 'title', 'video_size', 'clarity', 'model_needed', 'model_occur_rate',
            'model_age_range', 'model_figure'
        )


class VideoApplicationDetailSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.title')

    class Meta:
        model = VideoOrderDetail
        fields = (
            'goods_link', 'goods_images', 'goods_channel', 'goods_title', 'category'
        )


class VideoApplicationListSerializer(serializers.ModelSerializer):
    """我的订单"""
    demand = VNeededSerializer()
    total_reward = serializers.SerializerMethodField()
    video_order_detail = VideoApplicationDetailSerializer()

    class Meta:
        model = VideoOrder
        fields = (
            'id', 'status', 'date_created', 'num_selected', 'sample_count', 'is_return',
            'total_reward', 'video_order_detail', 'demand',
        )

    def get_total_reward(self, obj):
        # 订单可得松子
        return obj.reward * obj.num_selected


class VideoApplicationDetailRetrieveSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.title')
    # location = serializers.SerializerMethodField()

    class Meta:
        model = VideoOrderDetail
        fields = (
            'goods_link', 'goods_images', 'goods_channel', 'goods_title', 'category', 'receiver_name', 'receiver_phone',
            'receiver_location', 'company', 'express',
        )

    # def get_location(self, obj):
    #     tmp = [obj.receiver_province, obj.receiver_city, obj.receiver_district, obj.receiver_location]
    #     return ''.join([i for i in tmp if i])


class VideoApplicationRetrieveSerializer(serializers.ModelSerializer):
    """我的订单详情"""
    demand = VNeededSerializer()
    return_sample = serializers.SerializerMethodField()
    video_order_detail = VideoApplicationDetailRetrieveSerializer()

    class Meta:
        model = VideoOrder
        fields = (
            'id', 'status', 'date_created', 'num_selected', 'is_return', 'creator_remark', 'check_time', 'send_time',
            'done_time', 'close_time', 'date_created', 'demand', 'video_order_detail', 'return_sample',
        )

    def get_return_sample(self, obj):
        # 返样信息
        if obj.is_return and obj.status == VideoOrder.WAIT_RETURN:
            # location = obj.return_receiver_province + obj.return_receiver_city + \
            #            obj.return_receiver_district + obj.return_receiver_location
            return dict(return_receiver_name=obj.return_receiver_name,
                        return_receiver_phone=obj.return_receiver_phone,
                        return_location=obj.return_receiver_location,
                        return_company=obj.return_company,
                        return_express=obj.return_express)
        return None


class BusApplicationSerializer(VideoApplicationRetrieveSerializer):
    video_download = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VideoOrder
        fields = '__all__'

    def get_video_download(self, obj):
        auth = Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)
        tmp = obj.order_video.values_list('video_url', 'id')
        ok_lst = []
        for i in tmp:
            try:
                ok_lst.append({'id': i[1],
                               'video_url': auth.private_download_url(i[0]),
                               'cover': auth.private_download_url(i[0] + '?vframe/jpg/offset/1')})
            except:
                logger.info(traceback.format_exc())
        return ok_lst


class VideoApplicationManagerListSerializer(serializers.ModelSerializer):
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


class VideoOrderDetailManagerSerializer(serializers.ModelSerializer):
    # location = serializers.SerializerMethodField()
    # return_location = serializers.SerializerMethodField()
    category = serializers.CharField(source='category.title')

    class Meta:
        model = VideoOrderDetail
        fields = (
            'receiver_name', 'receiver_phone', 'receiver_location', 'return_receiver_name', 'return_receiver_phone',
            'return_receiver_location', 'goods_title', 'goods_link', 'goods_images', 'goods_channel', 'category',
            'company', 'express'
        )

    # def get_location(self, obj):
    #     tmp = [obj.receiver_province, obj.receiver_city, obj.receiver_district, obj.receiver_location]
    #     return ''.join([i for i in tmp if i])

    # def get_return_location(self, obj):
    #     tmp = [obj.return_receiver_province, obj.return_receiver_city,
    #            obj.return_receiver_district, obj.return_receiver_location]
    #     return ''.join([i for i in tmp if i])


class VideoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Video
        fields = ('video_url', )


class VideoApplicationManagerRetrieveSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='demand.title', read_only=True)
    demand_id = serializers.IntegerField(source='demand.id', read_only=True)
    bus_username = serializers.CharField(source='demand.uid.username', read_only=True)
    bus_name = serializers.SerializerMethodField()
    creator_username = serializers.CharField(source='user.username')
    creator_id = serializers.CharField(source='user.id')
    creator_nickname = serializers.CharField(source='user.auth_base.nickname')
    is_signed = serializers.BooleanField(source='user.user_creator.is_signed')
    video_order_detail = VideoOrderDetailManagerSerializer()
    order_video = serializers.SerializerMethodField()

    class Meta:
        model = VideoOrder
        fields = ('id', 'title', 'bus_username', 'bus_name', 'num_selected', 'sample_count', 'demand_id', 'creator_id',
                  'is_return', 'creator_nickname', 'creator_username', 'reward', 'is_signed',
                  'status', 'creator_remark', 'system_remark', 'remark',
                  'date_created', 'check_time', 'send_time', 'done_time', 'video_order_detail', 'order_video')

    def get_bus_name(self, obj):
        user_business = obj.demand.uid.user_business
        return user_business.bus_name if user_business else None

    def get_order_video(self, obj):
        auth = Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)
        tmp = obj.order_video.values_list('video_url', 'id')
        ok_lst = []
        for i in tmp:
            try:
                ok_lst.append({'id': i[1],
                               'video_url': auth.private_download_url(i[0]),
                               'cover': auth.private_download_url(i[0] + '?vframe/jpg/offset/1')})
            except:
                logger.info(traceback.format_exc())
        return ok_lst


class VideoOrderDetailSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()

    class Meta:
        model = VideoOrder
        fields = ('id', 'order_number', 'done_time', 'total')

    def get_total(self, obj):
        return obj.num_selected * obj.reward


