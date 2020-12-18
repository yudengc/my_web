import datetime

from django.db.models import Sum, F, FloatField
from rest_framework import serializers, exceptions

from account.models import CreatorBill
from application.models import VideoOrder
from demand.models import VideoNeeded
from libs.common.utils import get_last_year_month, get_first_and_now
from relations.models import InviteRelationManager
from tiktokvideo.base import QINIU_ACCESS_KEY, QINIU_SECRET_KEY
from transaction.models import UserPackageRelation, UserPackageRecord
from users.models import Users, Team, UserBusiness, Address, UserCreator, UserBase, CelebrityStyle, ScriptType, \
    UserExtra, OfficialTemplateMsg


class UsersLoginSerializer(serializers.ModelSerializer):
    """
    登陆
    """

    # remain_video_num = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Users
        fields = ('username', 'iCode', 'identity', 'is_subscribed')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def get_is_subscribed(self, obj):
        try:
            return obj.user_extra.is_subscribed
        except UserExtra.DoesNotExist:
            UserExtra.objects.create(uid=obj)
            return False

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
        r_ps = UserPackageRecord.objects.filter(uid=obj).order_by('-date_created')
        lis = []
        for r_obj in r_ps:
            relation_obj = UserPackageRelation.objects.filter(uid=obj, package_id=r_obj.package_id).first()
            lis.append(dict(package_title=r_obj.package_title,
                            expiration_time=relation_obj.expiration_time if relation_obj else None))
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
        return obj.video + '?vframe/jpg/offset/1' if obj.video else None


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


class ManagerUserSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(source='auth_base.nickname')
    permission_group = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ('id', 'nickname', 'username', 'status', 'reason', 'permission_group')

    def get_permission_group(self, obj):
        permission_obj = obj.permission_group
        if permission_obj:
            return {'id': permission_obj.id, 'title': permission_obj.title}
        return None


class ManagerUserUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Users
        fields = ('status', 'reason', 'permission_group')


class UserBusinessDeliveryManagerSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(source='auth_base.nickname')
    num_data = serializers.SerializerMethodField()
    package = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ('id', 'username', 'nickname', 'date_created', 'num_data', 'package')

    def get_num_data(self, obj):
        record_qs = UserPackageRecord.objects.filter(uid=obj)

        # 商家总视频数（商家购买套餐后，套餐内拍摄视频数总和）
        total = record_qs.aggregate(total=Sum(F('buy_video_num') + F('video_num')))['total']
        if not total:
            total = 0

        # 已完成视频数（商家发布的需求订单，订单状态为已完成的视频数总和）
        done_num = VideoOrder.objects.filter(status=VideoOrder.DONE,
                                             demand__uid=obj).aggregate(total=Sum('num_selected'))['total']
        if not done_num:
            done_num = 0

        # 进行中的视频数（需求订单拍摄视频数-已完成订单视频数）
        need_video_num = VideoNeeded.objects.filter(uid=obj).aggregate(total=Sum('video_num_needed'))['total']
        if not need_video_num:
            need_video_num = 0
        ongoing_video_num = need_video_num - done_num

        # 待交付视频数（商家总拍摄视频数-商家发布的需求拍摄视频数）
        pending_video_num = total - need_video_num

        # 交付状态为：未购买、待交付、进行中、已完成；
        # 未购买：总拍摄视频数为0时，状态为未购买；
        # 待交付：总拍摄视频数＞0，待交付视频数＞0时，状态为【待交付】；
        # 进行中；总拍摄视频数＞0，待交付视频数=0，进行中视频数＞0时，状态为【进行中】；
        # 已完成：总拍摄视频数＞0，待交付视频数=0，进行中视频数=0时，状态为【已完成】；
        if total == 0:
            status = '未购买'
        elif total > 0 and pending_video_num > 0:
            status = '待交付'
        elif total > 0 and pending_video_num == 0:
            if ongoing_video_num > 0:
                status = '进行中'
            else:
                status = '已完成'
        else:
            status = '异常'

        return {'status': status, 'total': total, 'done_num': done_num,
                'ongoing_video_num': ongoing_video_num, 'pending_video_num': pending_video_num}

    def get_package(self, obj):
        lis = []
        relation_qs = UserPackageRelation.objects.filter(uid=obj).select_related('package').order_by('-expiration_time')
        for relation_obj in relation_qs:
            lis.append({
                'package_id': relation_obj.package.id,
                'package_title': relation_obj.package.package_title,
                'expiration_time': relation_obj.expiration_time
            })
        return lis


class TemplateMsgSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfficialTemplateMsg
        fields = '__all__'

    def __init__(self, obj_list, *args, **kwargs):
        for obj in obj_list:
            if obj.status == OfficialTemplateMsg.DOING:
                if datetime.datetime.now() - obj.send_time > datetime.timedelta(minutes=30):
                    # 超时30min了
                    obj.status = OfficialTemplateMsg.ERR
                    obj.fail_reason = "超时30分钟还没执行完"
                    obj.save()
        super(TemplateMsgSerializer, self).__init__(obj_list, *args, **kwargs)
