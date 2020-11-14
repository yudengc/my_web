import django_filters

from relations.models import InviteRelationManager


class MyRelationInfoFilter(django_filters.FilterSet):
    start_time = django_filters.DateTimeFilter(field_name='invitee__date_created', lookup_expr='gte')
    end_time = django_filters.DateTimeFilter(field_name='invitee__date_created', lookup_expr='lte')

    class Meta:
        model = InviteRelationManager
        fields = ('start_time', 'end_time')
