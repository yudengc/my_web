from rest_framework import serializers

from users.models import Users


class UsersLoginSerializer(serializers.ModelSerializer):
    """
    登陆
    """

    class Meta:
        model = Users
        fields = (
            'uid',
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }


