import django_filters

from users.models import Team, Users


class TeamFilter(django_filters.FilterSet):
    start_time = django_filters.DateTimeFilter(field_name='date_created', lookup_expr='gte')
    end_time = django_filters.DateTimeFilter(field_name='date_created', lookup_expr='lte')

    class Meta:
        model = Team
        fields = ('start_time', 'end_time')


class UserInfoManagerFilter(django_filters.FilterSet):
    start_time = django_filters.DateTimeFilter(field_name='date_created', lookup_expr='gte')
    end_time = django_filters.DateTimeFilter(field_name='date_created', lookup_expr='lte')

    class Meta:
        model = Users
        fields = ('status', 'identity', 'start_time', 'end_time')
