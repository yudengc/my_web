import django_filters

from application.models import VideoOrder


class VideoApplicationManagerFilter(django_filters.rest_framework.FilterSet):
    """
    后台申请订单filter
    """
    created_start_time = django_filters.DateTimeFilter(field_name='date_created__date', lookup_expr='gte')  # 开始时间
    created_end_time = django_filters.DateTimeFilter(field_name='date_created__date', lookup_expr='lte')  # 结束时间
    done_start_time = django_filters.DateTimeFilter(field_name='done_time__date', lookup_expr='lte')  # 结束时间
    done_end_time = django_filters.DateTimeFilter(field_name='done_time__date', lookup_expr='lte')  # 结束时间

    class Meta:
        model = VideoOrder
        fields = ['is_return', 'status', 'created_start_time', 'created_end_time', 'done_start_time', 'done_end_time']
