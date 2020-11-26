from rest_framework import serializers

from demand.models import VideoNeeded


class VideoNeededSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoNeeded
        fields = '__all__'


class ManageVideoNeededSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VideoNeeded
        fields = '__all__'

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
            'model_occur_rate'
        )

    def get_video_num_at_least(self, obj):
        return list(obj.video_slice[0].keys())[0]

    def get_video_size(self, obj):
        return obj.get_video_size_display()

    def get_clarity(self, obj):
        return obj.get_clarity_display()

    def get_model_needed(self, obj):
        return obj.get_model_needed_display()

    def get_model_occur_rate(self, obj):
        return obj.get_model_needed_display_display()

    def get_sold_out(self, obj):
        if obj.num_remained == 0:
            return True
        return False
