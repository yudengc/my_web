import logging
from datetime import datetime, timedelta

from django.db.models import Sum, F, FloatField
from rest_framework import serializers

from account.models import CreatorAccount, CreatorBill, BalanceRecord
from application.models import VideoOrder
from libs.common.utils import get_last_year_month, get_first_and_now

logger = logging.getLogger()


class MyCreatorAccountSerializer(serializers.ModelSerializer):
    last_month = serializers.SerializerMethodField()
    last_year = serializers.SerializerMethodField()
    last_month_reward = serializers.SerializerMethodField()
    this_month_reward = serializers.SerializerMethodField()

    class Meta:
        model = CreatorAccount
        fields = ('id', 'coin_balance', 'coin_cash_out', 'last_month', 'last_year',
                  'last_month_reward', 'this_month_reward')

    def get_last_month(self, obj):
        # 上个月月份
        return get_last_year_month()[1]

    def get_last_year(self, obj):
        # 上个月年份
        return get_last_year_month()[0]

    def get_last_month_reward(self, obj):
        """上个月待结算松子（上个月未入账可得松子数）"""
        year, month = get_last_year_month()
        bill_obj = CreatorBill.objects.filter(uid=self.context['request'].user, bill_year=year, bill_month=month).first()
        if bill_obj:
            if bill_obj.status == CreatorBill.PENDING:
                last_month_reward = bill_obj.total
            else:
                last_month_reward = 0
        else:
            last_month_reward = VideoOrder.objects.filter(user=self.context['request'].user,
                                                          status=VideoOrder.DONE,
                                                          done_time__year=year,
                                                          done_time__month=month).aggregate(
                total=Sum(F('num_selected') * F('reward'), output_field=FloatField()))['total']
        return last_month_reward if last_month_reward else 0

    def get_this_month_reward(self, obj):
        """本月未入账待结算松子（本月到现在为止可得松子数）"""
        this_month_reward = VideoOrder.objects.filter(user=self.context['request'].user,
                                                      status=VideoOrder.DONE,
                                                      done_time__range=get_first_and_now()).aggregate(
            total=Sum(F('num_selected') * F('reward'), output_field=FloatField()))['total']
        return this_month_reward if this_month_reward else 0

    def to_representation(self, instance):
        data = super(MyCreatorAccountSerializer, self).to_representation(instance)
        data['coin_freeze'] = data['last_month_reward'] + data['this_month_reward']   # 待结算
        return data


class MyCreatorBillSerializer(serializers.ModelSerializer):

    class Meta:
        model = CreatorBill
        fields = ('id', 'bill_year', 'bill_month', 'total', 'status')


class MyBalanceRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = BalanceRecord
        fields = ('id', 'operation_type', 'amount', 'balance', 'date_created')


class CreatorBillManagerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='uid.username', read_only=True)
    nickname = serializers.CharField(source='uid.auth_base.nickname', read_only=True)
    avatar = serializers.CharField(source='uid.auth_base.avatars', read_only=True)
    order_count = serializers.SerializerMethodField()
    video_count = serializers.SerializerMethodField()

    class Meta:
        model = CreatorBill
        exclude = ('date_updated', 'uid')

    def get_order_count(self, obj):
        order_count = VideoOrder.objects.filter(user=obj.uid,
                                                status=VideoOrder.DONE,
                                                done_time__year=obj.bill_year,
                                                done_time__month=obj.bill_month).count()
        return order_count

    def get_video_count(self, obj):
        video_count = VideoOrder.objects.filter(user=obj.uid,
                                                status=VideoOrder.DONE,
                                                done_time__year=obj.bill_year,
                                                done_time__month=obj.bill_month).aggregate(
            total=Sum('num_selected'))['total']
        return video_count if video_count else 0


class CreatorBillUpdateManagerSerializer(serializers.ModelSerializer):

    class Meta:
        model = CreatorBill
        exclude = ('status', 'remark', 'check_time')


class CreatorBillDetailSerializer(serializers.ModelSerializer):
    """账单详情"""
    demand_title = serializers.SerializerMethodField()
    total_reward = serializers.SerializerMethodField()
    bus = serializers.SerializerMethodField()

    class Meta:
        model = VideoOrder
        fields = (
            'id', 'demand_title', 'status', 'bus', 'total_reward', 'num_selected', 'reward', 'date_created', 'done_time'
        )

    def get_total_reward(self, obj):
        # 订单可得松子
        return obj.reward * obj.num_selected

    def get_demand_title(self, obj):
        detail_json = obj.video_order_detail.demand_detail
        return detail_json.get('title') if detail_json else obj.demand.title

    def get_bus(self, obj):
        bus_user_obj = obj.demand.uid
        return {
            'username': bus_user_obj.username,
            'nickname': bus_user_obj.auth_base.nickname
        }
