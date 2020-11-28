import django_filters

from demand.models import VideoNeeded, HomePageVideo


class ManageVideoNeededFilter(django_filters.FilterSet):
    start_time = django_filters.DateTimeFilter(field_name='create_time', lookup_expr='gte')
    end_time = django_filters.DateTimeFilter(field_name='create_time', lookup_expr='lte')
    status = django_filters.NumberFilter(field_name='status')

    class Meta:
        model = VideoNeeded
        fields = ('start_time', 'end_time')


class ManageHomePageVideoFilter(django_filters.FilterSet):
    start_time = django_filters.DateTimeFilter(field_name='create_time', lookup_expr='gte')
    end_time = django_filters.DateTimeFilter(field_name='create_time', lookup_expr='lte')
    is_show = django_filters.BooleanFilter(field_name='is_show')
    category = django_filters.NumberFilter(field_name='category__id')

    class Meta:
        model = HomePageVideo
        fields = ('start_time', 'end_time', 'is_show', 'category')
