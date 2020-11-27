from rest_framework import serializers

from transaction.models import UserPackageRelation
from users.models import Users, Team, UserBusiness, Address, UserCreator


class UsersLoginSerializer(serializers.ModelSerializer):
    """
    登陆
    """
    remain_video_num = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Users
        fields = ('username', 'iCode', 'identity', 'remain_video_num')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def get_remain_video_num(self, obj):
        try:
            return obj.user_business.remain_video_num
        except UserBusiness.DoesNotExist:
            return 0


class TeamSerializer(serializers.ModelSerializer):
    """
    团队
    """
    leader = serializers.CharField(source='leader.username')

    class Meta:
        model = Team
        exclude = ('date_updated',)


class UserBusinessSerializer(serializers.ModelSerializer):
    """
    商家信息
    """

    class Meta:
        model = UserBusiness
        exclude = ('date_updated', 'uid', 'date_created')


class UserBusinessCreateSerializer(serializers.ModelSerializer):
    """
    商家信息create
    """

    class Meta:
        model = UserBusiness
        exclude = ('date_updated', 'uid', 'date_created', 'id')

    def create(self, validated_data):
        validated_data['uid'] = self.context['request'].user
        return super().create(validated_data)


class UserInfoSerializer(serializers.ModelSerializer):
    """
    商家，业务员用户页
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
            return dict(package_title=r_obj.package.package_title, expiration_time=r_obj.expiration_time)
        return None


class CreatorUserInfoSerializer(serializers.ModelSerializer):
    """
    创作者用户页
    """
    creator_id = serializers.IntegerField(source='user_creator.id')
    status = serializers.IntegerField(source='user_creator.status')
    remark = serializers.CharField(source='user_creator.remark')
    nickname = serializers.CharField(source='auth_base.nickname')
    avatars = serializers.CharField(source='auth_base.avatars')
    creator_account = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ('creator_id', 'username', 'identity', 'status', 'remark', 'nickname', 'avatars', 'creator_account')

    def get_creator_account(self, obj):
        return dict(coin_balance=obj.creator_account.coin_balance, coin_freeze=obj.creator_account.coin_freeze)


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'


class AddressListSerializer(serializers.ModelSerializer):
    address = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Address
        fields = ('id', 'name', 'phone', 'is_default', 'address')

    def get_address(self, obj):
        _l = [obj.province, obj.city, obj.district, obj.location]
        return ''.join([i for i in _l if i])


class UserCreatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCreator
        fields = ('status', 'video', 'team_introduction', 'capability_introduction', 'remark')


class UserCreatorPutSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserCreator
        fields = ('video', 'team_introduction', 'capability_introduction', 'video')
