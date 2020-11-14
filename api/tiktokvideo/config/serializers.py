from rest_framework import serializers

from config.models import CustomerService


class CustomerServiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerService
        exclude = ('date_updated', 'date_updated')


