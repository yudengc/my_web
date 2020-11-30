import logging
from datetime import datetime, timedelta

from rest_framework import serializers

from account.models import CreatorAccount
from application.models import VideoOrder
from libs.common.utils import get_last_year_month

logger = logging.getLogger()


class MyCreatorAccountSerializer(serializers.ModelSerializer):
    last_month = serializers.SerializerMethodField()
    pending_settlement = serializers.SerializerMethodField()

    class Meta:
        model = CreatorAccount
        fields = ('id', 'coin_balance', 'coin_freeze', 'coin_cash_out', 'last_month', 'pending_settlement')

    def get_last_month(self, obj):
        return get_last_year_month()[1]

    def get_pending_settlement(self, obj):
        """上个月待结算松子"""
        year, month = get_last_year_month()
        VideoOrder.objects.filter()
        return

