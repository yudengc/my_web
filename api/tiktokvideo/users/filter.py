import django_filters

from transaction.models import UserPackageRelation
from users.models import Team, Users, UserCreator


class TeamFilter(django_filters.FilterSet):
    start_time = django_filters.DateTimeFilter(field_name='date_created__date', lookup_expr='gte')
    end_time = django_filters.DateTimeFilter(field_name='date_created__date', lookup_expr='lte')

    class Meta:
        model = Team
        fields = ('start_time', 'end_time')


class UserInfoManagerFilter(django_filters.FilterSet):
    start_time = django_filters.DateTimeFilter(field_name='date_created__date', lookup_expr='gte')
    end_time = django_filters.DateTimeFilter(field_name='date_created__date', lookup_expr='lte')

    class Meta:
        model = Users
        fields = ('status', 'identity', 'start_time', 'end_time')


class UserCreatorInfoManagerFilter(django_filters.FilterSet):
    start_time = django_filters.DateTimeFilter(field_name='date_created__date', lookup_expr='gte')
    end_time = django_filters.DateTimeFilter(field_name='date_created__date', lookup_expr='lte')

    class Meta:
        model = UserCreator
        fields = ('status', 'is_signed', 'start_time', 'end_time')


class UserBusinessInfoManagerFilter(django_filters.FilterSet):
    start_time = django_filters.DateTimeFilter(field_name='date_created__date', lookup_expr='gte')
    end_time = django_filters.DateTimeFilter(field_name='date_created__date', lookup_expr='lte')
    has_package = django_filters.BooleanFilter(method='get_has_package')  # 是否购买套餐

    class Meta:
        model = Users
        fields = ('status', 'start_time', 'end_time', 'has_package')

    def get_has_package(self, queryset, name, value):
        for qs in queryset:
            if UserPackageRelation.objects.filter(uid=qs).exists() != value:
                queryset = queryset.exclude(id=qs.id)
        return queryset


class TeamUsersManagerTeamFilter(django_filters.FilterSet):
    team = django_filters.NumberFilter(field_name='team__id', lookup_expr='exact')

    class Meta:
        model = Users
        fields = ('team', )
