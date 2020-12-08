from django.db.models import Sum, F, FloatField
from qiniu import Auth
from rest_framework import serializers, exceptions

from account.models import CreatorBill
from application.models import VideoOrder
from libs.common.utils import get_last_year_month, get_first_and_now
from relations.models import InviteRelationManager
from tiktokvideo.base import QINIU_ACCESS_KEY, QINIU_SECRET_KEY
from transaction.models import UserPackageRelation
from users.models import Users, Team, UserBusiness, Address, UserCreator, UserBase, CelebrityStyle, ScriptType


class UsersLoginSerializer(serializers.ModelSerializer):
    """
    登陆
    """

    # remain_video_num = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Users
        fields = ('username', 'iCode', 'identity')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    # def get_remain_video_num(self, obj):
    #     try:
    #         return obj.user_business.remain_video_num
    #     except UserBusiness.DoesNotExist:
    #         return 0


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
            return dict(id=bus_obj.id, bus_name=bus_obj.bus_name, name_abb=bus_obj.name_abb,
                        remain_video_num=bus_obj.remain_video_num)
        return None

    def get_package_info(self, obj):
        r_ps = UserPackageRelation.objects.filter(uid=obj).order_by('-date_created')
        lis = []
        for r_obj in r_ps:
            lis.append(dict(package_title=r_obj.package.package_title, expiration_time=r_obj.expiration_time))
        return lis


class CreatorUserInfoSerializer(serializers.ModelSerializer):
    """
    创作者用户页
    """
    creator_id = serializers.IntegerField(source='user_creator.id')
    status = serializers.IntegerField(source='user_creator.status')
    coin_balance = serializers.CharField(source='creator_account.coin_balance')
    remark = serializers.CharField(source='user_creator.remark')
    coin_freeze = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ('creator_id', 'status', 'remark', 'coin_balance', 'coin_freeze')

    def get_coin_freeze(self, obj):
        """上个月待结算松子（上个月未入账可得松子数）"""
        year, month = get_last_year_month()
        bill_obj = CreatorBill.objects.filter(uid=obj, bill_year=year, bill_month=month).first()
        if bill_obj:
            if bill_obj.status == CreatorBill.PENDING:
                last_month_reward = bill_obj.total
            else:
                last_month_reward = 0
        else:
            last_month_reward = VideoOrder.objects.filter(user=obj,
                                                          status=VideoOrder.DONE,
                                                          done_time__year=year,
                                                          done_time__month=month).aggregate(
                total=Sum(F('num_selected') * F('reward'), output_field=FloatField()))['total']
            last_month_reward = last_month_reward if last_month_reward else 0

        """本月未入账待结算松子（本月到现在为止可得松子数）"""
        this_month_reward = VideoOrder.objects.filter(user=obj,
                                                      status=VideoOrder.DONE,
                                                      done_time__range=get_first_and_now()).aggregate(
            total=Sum(F('num_selected') * F('reward'), output_field=FloatField()))['total']
        this_month_reward = this_month_reward if this_month_reward else 0

        return last_month_reward + this_month_reward


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'


class AddressListSerializer(serializers.ModelSerializer):
    address = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Address
        fields = '__all__'

    def get_address(self, obj):
        _l = [obj.province, obj.city, obj.district, obj.location]
        return ''.join([i for i in _l if i])


class UserCreatorSerializer(serializers.ModelSerializer):
    cover = serializers.SerializerMethodField()

    class Meta:
        model = UserCreator
        fields = ('status', 'video', 'team_introduction', 'capability_introduction', 'remark', 'cover')

    def get_cover(self, obj):
        auth = Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)
        return auth.private_download_url(obj.video + '?vframe/jpg/offset/1')


class UserCreatorPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCreator
        fields = ('video', 'team_introduction', 'capability_introduction', 'status')


class ManageAddressSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField(read_only=True)
    role = serializers.SerializerMethodField(read_only=True)
    username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Address
        fields = '__all__'

    def get_role(self, obj):
        user = obj.uid
        return user.get_identity_display()

    def get_nickname(self, obj):
        user = obj.uid
        try:
            return user.auth_base.nickname
        except UserBase.DoesNotExist:
            return ''

    def get_username(self, obj):
        user = obj.uid
        return user.username


class UserInfoManagerSerializer(serializers.ModelSerializer):
    """注册账户后台"""
    nickname = serializers.CharField(source='auth_base.nickname')

    class Meta:
        model = Users
        fields = ('id', 'username', 'nickname', 'identity', 'status', 'reason', 'date_created')


class UserCreatorInfoManagerSerializer(serializers.ModelSerializer):
    """创作者用户后台"""
    username = serializers.CharField(source='uid.username')
    nickname = serializers.CharField(source='uid.auth_base.nickname')
    coin_balance = serializers.IntegerField(source='uid.creator_account.coin_balance')
    avatar = serializers.CharField(source='uid.auth_base.avatars')
    uuid = serializers.CharField(source='uid.uid')

    class Meta:
        model = UserCreator
        fields = ('id', 'username', 'nickname', 'status', 'is_signed', 'coin_balance', 'contract_reward',
                  'team_introduction', 'capability_introduction', 'video', 'remark', 'date_created',
                  'avatar', 'uuid')


class UserCreatorInfoUpdateManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCreator
        fields = ('status', 'contract_reward', 'is_signed', 'remark')


class UserBusinessInfoManagerSerializer(serializers.ModelSerializer):
    """商家用户后台"""
    nickname = serializers.CharField(source='auth_base.nickname')
    avatar = serializers.CharField(source='auth_base.avatars')
    package = serializers.SerializerMethodField()
    salesman = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ('id', 'username', 'nickname', 'avatar', 'status', 'salesman', 'package', 'date_created')

    def get_salesman(self, obj):
        # 所属业务员账号
        qs = InviteRelationManager.objects.filter(invitee=obj).first()
        if qs:
            salesman = qs.salesman
            if salesman:
                return {'salesman_username': qs.salesman.username, 'salesman_name': qs.salesman.salesman_name}
            return {'salesman_username': None, 'salesman_name': None}
        return {'salesman_username': None, 'salesman_name': None}

    def get_package(self, obj):
        qs = UserPackageRelation.objects.filter(uid=obj).first()
        if qs:
            return {'package_title': qs.package.package_title, 'expiration_time': qs.expiration_time}
        return {'package_title': None, 'expiration_time': None}


class UserBusinessInfoUpdateManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ('status', 'reason')


class BusinessInfoManagerSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(source='uid.auth_base.nickname')
    username = serializers.CharField(source='uid.username')

    class Meta:
        model = UserBusiness
        exclude = ('date_updated', 'uid', 'remain_video_num')


class TeamManagerSerializer(serializers.ModelSerializer):
    leader_username = serializers.SerializerMethodField()
    number = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ('id', 'name', 'leader_username', 'number', 'date_created')

    def get_leader_username(self, obj):
        return obj.leader.username

    def get_number(self, obj):
        return obj.team_user.count()


class TeamManagerCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Team
        fields = ('name', 'leader')


class TeamUserLeaderManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ('id', 'username', 'salesman_name')


class TeamUserManagerSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name')
    leader_username = serializers.CharField(source='team.leader.username')

    class Meta:
        model = Users
        fields = ('id', 'username', 'salesman_name', 'team_name', 'leader_username', 'date_created', 'has_power')


class TeamUserManagerUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Users
        fields = ('salesman_name', 'team', 'has_power')


class TeamLeaderManagerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Users
        fields = ('id', 'username', 'salesman_name', 'date_created', 'has_power')


class TeamLeaderManagerUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Users
        fields = ('salesman_name', 'has_power')


class CelebrityStyleSerializer(serializers.ModelSerializer):

    class Meta:
        model = CelebrityStyle
        exclude = ('date_updated',)


class ScriptTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ScriptType
        exclude = ('date_updated',)
