from rest_framework import serializers

from demand.models import VideoNeeded


class VideoNeededSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoNeeded
        fields = '__all__'


class ManageVideoNeededSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField(read_only=True)
    goods_images = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VideoNeeded
        fields = '__all__'
