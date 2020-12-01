import logging
from datetime import datetime, timedelta

from django.db.models import Sum, F, FloatField
from rest_framework import serializers

from account.models import CreatorAccount
from application.models import VideoOrder
from libs.common.utils import get_last_year_month, get_first_and_now

logger = logging.getLogger()


class MyCreatorAccountSerializer(serializers.ModelSerializer):
    last_month = serializers.SerializerMethodField()
    last_month_reward = serializers.SerializerMethodField()
    this_month_reward = serializers.SerializerMethodField()

    class Meta:
        model = CreatorAccount
        fields = ('id', 'coin_balance', 'coin_freeze', 'coin_cash_out', 'last_month',
                  'last_month_reward', 'this_month_reward')

    def get_last_month(self, obj):
        return get_last_year_month()[1]

    def get_last_month_reward(self, obj):
        """上个月待结算松子（上个月未入账可得松子数）"""
        year, month = get_last_year_month()
        last_month_reward = VideoOrder.objects.filter(user=self.context['request'].user,
                                                      status=VideoOrder.DONE,
                                                      done_time__year=year,
                                                      done_time__month=month).aggregate(
            total=Sum(F('num_selected') * F('reward'), output_field=FloatField()))['total']
        return last_month_reward if last_month_reward else 0

    def get_this_month_reward(self, obj):
        """本月未入账待结算松子（本月到现在为止可得松子数）"""
        last_month_reward = VideoOrder.objects.filter(user=self.context['request'].user,
                                                      status=VideoOrder.DONE,
                                                      done_time__range=get_first_and_now()).aggregate(
            total=Sum(F('num_selected') * F('reward'), output_field=FloatField()))['total']
        return last_month_reward if last_month_reward else 0