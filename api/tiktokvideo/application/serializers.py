from rest_framework import serializers

from application.models import VideoOrder


class VideoApplicationCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = VideoOrder
        fields = (
            'user', 'demand', 'num_selected', 'receiver_name', 'receiver_phone', 'receiver_province', 'receiver_city',
            'receiver_district', 'receiver_location', 'creator_remark',
        )

