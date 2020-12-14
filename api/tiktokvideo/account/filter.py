import django_filters

from account.models import CreatorBill


class CreatorBillFilter(django_filters.FilterSet):
    check_time_start = django_filters.DateTimeFilter(field_name='check_time__date', lookup_expr='gte')
    check_time_end = django_filters.DateTimeFilter(field_name='check_time__date', lookup_expr='lte')

    class Meta:
        model = CreatorBill
        fields = ('bill_year', 'bill_month', 'status', 'check_time_start', 'check_time_end')




