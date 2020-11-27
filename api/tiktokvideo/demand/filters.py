import django_filters

from demand.models import VideoNeeded


class ManageVideoNeededFilter(django_filters.FilterSet):
    start_time = django_filters.DateTimeFilter(field_name='create_time', lookup_expr='gte')
    end_time = django_filters.DateTimeFilter(field_name='create_time', lookup_expr='lte')
    status = django_filters.NumberFilter(field_name='status')

    class Meta:
        model = VideoNeeded
        fields = ('start_time', 'end_time')
