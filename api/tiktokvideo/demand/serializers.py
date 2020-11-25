from rest_framework import serializers

from demand.models import VideoNeeded


class VideoNeededSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoNeeded
        fields = '__all__'


