from rest_framework import serializers

from transaction.models import UserPackageRelation
from users.models import Users, Team, UserBusiness


class UsersLoginSerializer(serializers.ModelSerializer):
    """
    登陆
    """

    class Meta:
        model = Users
        fields = ('username', 'iCode',)
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


class UserBusinessSerializer(serializers.ModelSerializer):
    """
    商家信息
    """

    class Meta:
        model = UserBusiness
        exclude = ('date_updated', 'uid', 'date_created')


class UserBusinessCreateSerializer(serializers.ModelSerializer):
    """
    商家信息
    """

    class Meta:
        model = UserBusiness
        exclude = ('date_updated', 'uid', 'date_created')

    def create(self, validated_data):
        validated_data['uid'] = self.context['request'].user
        return super().create(validated_data)


class UserInfoSerializer(serializers.ModelSerializer):
    """
    用户页
    """
    user_business = serializers.SerializerMethodField()
    package_info = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ('username', 'identity', 'user_business', 'package_info')

    def get_user_business(self, obj):
        bus_obj = UserBusiness.objects.filter(uid=obj).first()
        if bus_obj:
            return dict(id=bus_obj.id, bus_name=bus_obj.bus_name, name_abb=bus_obj.name_abb)
        return None

    def get_package_info(self, obj):
        r_ps = UserPackageRelation.objects.filter(uid=obj).order_by('-date_created')
        if r_ps.exists():
            r_obj = r_ps[0]
            return dict(package_title=r_obj.package.package_title, expiration_time=r_obj.package.expiration_time)
        return None

