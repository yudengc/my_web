import django_filters

from relations.models import InviteRelationManager
from transaction.models import UserPackageRelation


class MyRelationInfoFilter(django_filters.FilterSet):
    start_time = django_filters.DateTimeFilter(field_name='invitee__date_created__date', lookup_expr='gte')
    end_time = django_filters.DateTimeFilter(field_name='invitee__date_created__date', lookup_expr='lte')
    has_package = django_filters.BooleanFilter(method='get_has_package')  # 是否购买套餐

    class Meta:
        model = InviteRelationManager
        fields = ('start_time', 'end_time')

    def get_has_package(self, queryset, name, value):
        for qs in queryset:
            invitee = qs.invitee
            if UserPackageRelation.objects.filter(uid=invitee).exists() != value:
                queryset = queryset.exclude(id=qs.id)
        return queryset
