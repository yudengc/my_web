import django_filters

from application.models import VideoOrder


class VideoApplicationManagerFilter(django_filters.rest_framework.FilterSet):
    """
    后台申请订单filter
    """
    start_time = django_filters.DateTimeFilter(field_name='date_created', lookup_expr='gte')  # 开始时间
    end_time = django_filters.DateTimeFilter(field_name='date_created', lookup_expr='lte')  # 结束时间

    class Meta:
        model = VideoOrder
        fields = ['is_return', 'status']