from rest_framework import serializers

from users.models import Users, Team


class UsersLoginSerializer(serializers.ModelSerializer):
    """
    登陆
    """

    class Meta:
        model = Users
        fields = (
            'username',
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }


class TeamSerializer(serializers.ModelSerializer):
    """
    团队
    """
    leader = serializers.CharField(source='leader.username')

    class Meta:
        model = Team
        exclude = ('date_updated', )
