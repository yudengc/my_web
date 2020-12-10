import django_filters

from transaction.models import UserPackageRelation, UserPackageRecord


class UserPackageRelationManagerFilter(django_filters.FilterSet):
    start_time = django_filters.DateTimeFilter(field_name='date_created__date', lookup_expr='gte')
    end_time = django_filters.DateTimeFilter(field_name='date_created__date', lookup_expr='lte')

    class Meta:
        model = UserPackageRecord
        fields = ('start_time', 'end_time', 'status')




