import logging
import re
import threading
import traceback
from xml.etree.ElementTree import tostring

from celery import shared_task
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.db.transaction import atomic
from django.http import HttpResponse
from django_filters import rest_framework
from django_filters.rest_framework import DjangoFilterBackend
from django_redis import get_redis_connection
from redis import StrictRedis
from rest_framework import mixins, exceptions, filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.utils import check_signature

from account.models import CreatorAccount
from libs.common.permission import AllowAny, ManagerPermission, CreatorPermission, AdminPermission, \
    custom_check_permission
from libs.parser import JsonParser, Argument
from libs.utils import trans_xml_to_dict, trans_dict_to_xml, content_shape
from permissions.models import UserGroups
from relations.models import InviteRelationManager
from relations.tasks import save_invite_relation

from tiktokvideo.base import APP_ID, SECRET
from users.filter import TeamFilter, UserInfoManagerFilter, UserCreatorInfoManagerFilter, UserBusinessInfoManagerFilter, \
    TeamUsersManagerTeamFilter, ManagerUserFilter, UserBusinessDeliveryManagerFilter
from users.models import Users, UserExtra, UserBase, Team, UserBusiness, ScriptType, CelebrityStyle, Address, \
    UserCreator
from libs.jwt.serializers import CusTomSerializer
from libs.jwt.services import JwtServers
from users.serializers import UserBusinessSerializer, UserBusinessCreateSerializer, UserInfoSerializer, \
    AddressSerializer, AddressListSerializer, CreatorUserInfoSerializer, UserCreatorSerializer, \
    UserCreatorPutSerializer, ManageAddressSerializer, UserInfoManagerSerializer, UserCreatorInfoManagerSerializer, \
    UserCreatorInfoUpdateManagerSerializer, UserBusinessInfoManagerSerializer, UserBusinessInfoUpdateManagerSerializer, \
    BusinessInfoManagerSerializer, TeamManagerSerializer, TeamManagerCreateUpdateSerializer, TeamUserManagerSerializer, \
    TeamUserLeaderManagerSerializer, TeamUserManagerUpdateSerializer, TeamLeaderManagerSerializer, \
    TeamLeaderManagerUpdateSerializer, CelebrityStyleSerializer, ScriptTypeSerializer, ManagerUserSerializer, \
    ManagerUserUpdateSerializer, UserBusinessDeliveryManagerSerializer

from users.services import WXBizDataCrypt, WeChatApi, InviteCls, WeChatOfficial, HandleOfficialAccount, \
    OfficialAccountMsg

redis_conn = get_redis_connection('default')  # type: StrictRedis
logger = logging.getLogger()


class LoginViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = CusTomSerializer

    @action(methods=['post', ], detail=False, permission_classes=[AllowAny])
    def admin(self, request):
        """
        后台管理员端登录接口
        username: 用户名/手机号
        password : 密码
        :param request:
        :return:
        """
        form, error = JsonParser(
            Argument('username', help="请输入账号username!!"),
            Argument('password', help="请输入密码password!!")
        ).parse(request.data)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        user = Users.objects.filter(username=form.username, status=0,
                                    sys_role__in=[Users.ADMIN, Users.SUPER_ADMIN]).last()
        if not user:
            return Response({"detail": "用户不存在"}, status=status.HTTP_400_BAD_REQUEST)
        if not check_password(form.password, user.password):
            return Response({"detail": '密码错误!'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            data = getattr(JwtServers(user=user), 'get_token_and_user_info')()
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post', ], detail=False, permission_classes=[AllowAny])
    def auth(self, request):
        """微信授权登录"""
        openid = request.data.get('openid', None)
        username = request.data.get('username', None)
        logger.info(username)
        user_info = request.data.get('userInfo', None)
        logger.info(user_info)
        code = request.data.get('iCode')
        if not username:
            return Response({"detail": "缺少参数!"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_instance = Users.objects.get(username=username)
        except Users.DoesNotExist:
            return Response({'detail': '新用户', 'code': 666}, status=status.HTTP_200_OK)
        if user_instance.status == Users.FROZEN:
            return Response({'detail': '账户被冻结，请联系客服处理', 'code': 444}, status=status.HTTP_200_OK)
        user_instance = self.save_user_and_openid(user_instance, openid, user_info=user_info)  # 更新微信昵称头像
        user_info = JwtServers(user=user_instance).get_token_and_user_info()
        # 存在注册码绑定邀请关系(如果一开始是自然用户，后面仍可绑定邀请关系，创作者只能在第一次登陆时输入邀请码绑定关系)
        if code and user_instance.identity == Users.BUSINESS:
            # save_invite_relation.delay(code, username)  # 绑定邀请关系
            threading.Thread(target=save_invite_relation,
                             args=(code, username)).start()  # 绑定邀请关系
        return Response(user_info, status=status.HTTP_200_OK)

    @action(methods=['post', ], detail=False, permission_classes=[AllowAny])
    def first_auth(self, request):
        """第一次登陆"""
        username = request.data.get('username', None)
        user_info = request.data.get('userInfo', None)
        openid = request.data.get('openid', None)
        code = request.data.get('iCode')
        identity = request.data.get('identity')

        form, error = JsonParser(
            Argument('username', help="缺少username"),
            Argument('userInfo', help="缺少userInfo"),
            Argument('identity', help="请选择注册角色"),
            Argument('openid', help="缺少openid")
        ).parse(request.data)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
        if identity not in [Users.BUSINESS, Users.CREATOR]:
            return Response({"detail": "identity错误"}, status=status.HTTP_400_BAD_REQUEST)
        if identity == Users.CREATOR and not code:
            return Response({"detail": "请填写邀请码"}, status=status.HTTP_400_BAD_REQUEST)

        if identity == Users.CREATOR and code:  # 校验salesman
            try:
                salesman_obj = Users.objects.get(iCode=code)
            except Users.DoesNotExist:
                return Response({"detail": "填写的邀请码错误"}, status=status.HTTP_400_BAD_REQUEST)
            if not salesman_obj.has_power:
                # 该业务员无权力邀请创作者
                return Response({"detail": "邀请码错误"}, status=status.HTTP_400_BAD_REQUEST)

        user_instance = self.save_user_and_openid(username, openid, identity, user_info)
        if code:
            threading.Thread(target=save_invite_relation,
                             args=(code, username)).start()  # 绑定邀请关系
        user_info = JwtServers(user=user_instance).get_token_and_user_info()
        return Response(user_info, status=status.HTTP_200_OK)

    @action(methods=['post', ], detail=False, permission_classes=[AllowAny])
    def get_phone(self, request):
        """获取手机号码"""
        if {'encrypted_data', 'iv', 'openid'}.issubset(set(request.data.keys())):
            openid = request.data.get('openid')
            logger.info('get_phone openid')
            logger.info(openid)
            session_key = redis_conn.get(openid)
            if not session_key:
                return Response({'detail': '找不到session_key'}, status=status.HTTP_400_BAD_REQUEST)
            encrypted_data = request.data.get('encrypted_data')
            iv = request.data.get('iv')
            pc = WXBizDataCrypt(APP_ID, str(session_key, encoding='utf8'))
            data = pc.decrypt(encrypted_data, iv)
            if not data:
                return Response({'code': 0, 'detail': 'session_key错误/已过期'}, status=status.HTTP_200_OK)
            user_qs = Users.objects.filter(username=data.get('purePhoneNumber'))
            if user_qs.exists():
                is_exists = True
            else:
                is_exists = False
            return Response(data={'code': 1, 'phone': data.get('purePhoneNumber'), 'is_exists': is_exists})
        return Response({'detail': '缺少参数'}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post', ], detail=False, permission_classes=[AllowAny])
    def get_openid(self, request):
        """获取openid"""
        code = request.data.get('code', None)
        if code:
            obj = WeChatApi(APP_ID, SECRET)
            openid, session_key = obj.get_openid_and_session_key(code)
            union_id = obj.get_union_id()
            logger.info('get_openid  openid union_id')
            logger.info(openid, union_id)
            res = redis_conn.set(openid, session_key)
            if union_id:
                redis_conn.set(f'{openid}_union_id', union_id, 3600)
            logger.info(res)
            return Response({'openid': openid}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'code不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    def save_user_and_openid(self, username, openid, select_identity=None, user_info=None):
        """保存用户信息以及openid"""
        if not username:
            raise exceptions.ParseError('username不能为空')
        if not isinstance(username, Users):
            user = Users.objects.create(
                username=username,
                openid=openid,
                identity=select_identity
            )
            user.iCode = InviteCls.encode_invite_code(user.id)
            user.save()
            UserExtra.objects.create(uid=user)
            UserBase.objects.create(
                uid=user,
                phone=username,
                nickname=user_info.get('nickName'),
                avatars=user_info.get('avatarUrl')
            )
            if select_identity == Users.CREATOR:
                UserCreator.objects.create(uid=user)
                CreatorAccount.objects.create(uid=user)
            elif select_identity == Users.BUSINESS:
                UserBusiness.objects.create(uid=user)
        else:
            # 如果后台创建的用户要补充微信信息
            user = username
            user_base = UserBase.objects.filter(uid=user).first()
            if user_base:
                user_base.phone = user.username
                user_base.nickname = user_info.get('nickName')
                user_base.avatars = user_info.get('avatarUrl')
                user_base.save()
        # 是否换微信登录
        if user.openid != openid:
            user.openid = openid
            user.save()
        if redis_conn.exists(f"{openid}_union_id"):
            union_id = redis_conn.get(f"{openid}_union_id").decode('utf-8')
            if user.union_id != union_id:
                user.union_id = union_id
                user.save()
        return user


class ManagerUserViewSet(mixins.CreateModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         GenericViewSet):
    """后台账号管理"""
    permission_classes = (AdminPermission,)
    queryset = Users.objects.filter(sys_role__in=[Users.ADMIN, Users.SUPER_ADMIN], is_superuser=False)
    serializer_class = ManagerUserSerializer
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = ManagerUserFilter
    search_fields = ('username', '=auth_base__phone')

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            self.serializer_class = ManagerUserUpdateSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        user_status = request.data.get('status')
        reason = request.data.get('reason')
        password = request.data.get('password')
        nickname = request.data.get('nickname')
        permission_group = request.data.get('permission_group')

        form, error = JsonParser(
            Argument('username', help="缺少用户名"),
            Argument('status', help="缺少状态"),
            Argument('reason', help="缺少备注"),
            Argument('password', help="缺少密码"),
            Argument('nickname', help="缺少名称"),
            Argument('permission_group', help="缺少所属权险组")
        ).parse(request.data)
        if error:
            return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

        try:
            Users.objects.get(username=username)
            return Response({'detail': '该账号已存在'}, status=status.HTTP_400_BAD_REQUEST)
        except Users.DoesNotExist:
            group_obj = UserGroups.objects.filter(id=permission_group).first()
            if not group_obj:
                return Response({"detail": "没有这个权限组"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                with atomic():
                    new_user_obj = Users(username=username, sys_role=Users.ADMIN, reason=reason,
                                         permission_group=group_obj, status=user_status)
                    new_user_base = UserBase(uid=new_user_obj, nickname=nickname)
                    new_user_extra = UserExtra(uid=new_user_obj)
                    new_user_obj.set_password(password)
                    new_user_obj.save()
                    new_user_base.save()
                    new_user_extra.save()
            except Exception as e:
                logger.info(e)
                return Response({'detail': '创建失败'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': '创建成功'}, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if request.data.get('nickname') is not None:
            UserBase.objects.filter(uid=instance).update(nickname=request.data.get('nickname'))

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class UserBusinessViewSet(mixins.CreateModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.RetrieveModelMixin,
                          GenericViewSet):
    permission_classes = (ManagerPermission,)
    queryset = UserBusiness.objects.all()
    serializer_class = UserBusinessSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            self.serializer_class = UserBusinessCreateSerializer
        return super().get_serializer_class()


class UserInfoViewSet(viewsets.ReadOnlyModelViewSet):
    """用户中心"""
    permission_classes = (ManagerPermission,)

    def get_queryset(self):
        identity = self.request.user.identity
        if identity == Users.CREATOR:
            self.queryset = Users.objects.select_related('user_creator', 'auth_base').filter(uid=self.request.user.uid)
        else:
            self.queryset = Users.objects.select_related('user_business').filter(uid=self.request.user.uid)
        return super().get_queryset()

    def get_serializer_class(self):
        identity = self.request.user.identity
        if identity == Users.CREATOR:
            self.serializer_class = CreatorUserInfoSerializer
        else:
            self.serializer_class = UserInfoSerializer
        return super().get_serializer_class()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data[0])


class BusInfoOtherView(APIView):
    permission_classes = (ManagerPermission,)

    def get(self, request):
        style_lis = []
        script_lis = []
        for obj in CelebrityStyle.objects.all():
            style_lis.append(dict(id=obj.id, title=obj.title))
        for obj in ScriptType.objects.all():
            script_lis.append(dict(id=obj.id, title=obj.title))
        return Response(dict(style=style_lis, script=script_lis))


class AddressViewSet(viewsets.ModelViewSet):
    """收货地址"""
    permission_classes = (ManagerPermission,)
    serializer_class = AddressSerializer

    def get_serializer_class(self):
        if self.action in ['list', ]:
            return AddressListSerializer
        return super().get_serializer_class()

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        with atomic():
            if self.request.data.get('is_default') is True:
                Address.objects.filter(uid=request.user).update(is_default=False)
            return super().update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        request.data['uid'] = self.request.user.uid
        with atomic():
            if request.data.get('is_default') is True:
                Address.objects.filter(uid=request.user).update(is_default=False)
            return super().create(request, *args, **kwargs)

    def get_queryset(self):
        self.queryset = Address.objects.filter(uid=self.request.user).extra(
            select={'default': "CAST(is_default AS integer)=1"}
        ).order_by('-default', '-date_created')
        return super(AddressViewSet, self).get_queryset()


class ManageAddressViewSet(viewsets.ModelViewSet):
    permission_classes = [AdminPermission, ]
    serializer_class = ManageAddressSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    search_fields = ('=uid__username', 'uid__auth_base__nickname', 'phone', 'name')
    filter_fields = ('uid__identity',)
    queryset = Address.objects.exclude(uid__identity__in=[Users.SALESMAN, Users.SUPERVISOR])


class UserCreatorViewSet(mixins.ListModelMixin,
                         mixins.UpdateModelMixin,
                         GenericViewSet):
    """创作者信息"""
    permission_classes = (CreatorPermission,)
    serializer_class = UserCreatorSerializer
    queryset = UserCreator.objects.all()

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            self.serializer_class = UserCreatorPutSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.action == 'list':
            self.queryset = self.queryset.filter(uid=self.request.user)
        return super(UserCreatorViewSet, self).get_queryset()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data[0] if serializer.data else {})

    @action(methods=['put'], detail=False, serializer_class=UserCreatorPutSerializer)
    def creator_info(self, request, *args, **kwargs):
        try:
            instance = UserCreator.objects.get(uid=request.user)
        except UserCreator.DoesNotExist:
            instance = UserCreator.objects.create(uid=request.user)
        request.data['status'] = UserCreator.PENDING
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class UserInfoManagerViewSet(mixins.ListModelMixin,
                             mixins.UpdateModelMixin,
                             GenericViewSet):
    """用户管理"""
    permission_classes = (AdminPermission,)
    serializer_class = UserInfoManagerSerializer
    queryset = Users.objects.exclude(is_superuser=True, sys_role__in=[Users.ADMIN, Users.SUPER_ADMIN],
                                     identity__in=[Users.SALESMAN, Users.SUPERVISOR]).order_by('-date_created')
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = UserInfoManagerFilter
    search_fields = ('=username', 'auth_base__nickname')


class UserCreatorInfoManagerViewSet(mixins.ListModelMixin,
                                    mixins.RetrieveModelMixin,
                                    mixins.UpdateModelMixin,
                                    GenericViewSet):
    """创作者用户管理"""
    permission_classes = (AdminPermission,)
    serializer_class = UserCreatorInfoManagerSerializer
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = UserCreatorInfoManagerFilter
    search_fields = ('=uid__username', 'uid__auth_base__nickname')

    def get_queryset(self):
        if self.action in ['list', 'retrieve']:
            self.queryset = UserCreator.objects.select_related('uid').order_by('-date_created')
        elif self.action in ['update', 'partial_update']:
            self.queryset = UserCreator.objects.all()
        return super().get_queryset()

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            self.serializer_class = UserCreatorInfoUpdateManagerSerializer
        return super().get_serializer_class()


class UserBusinessInfoManagerViewSet(mixins.ListModelMixin,
                                     mixins.RetrieveModelMixin,
                                     mixins.UpdateModelMixin,
                                     GenericViewSet):
    """商家用户管理"""
    permission_classes = (AdminPermission,)
    serializer_class = UserBusinessInfoManagerSerializer
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    queryset = Users.objects.filter(identity=Users.BUSINESS, sys_role=Users.COMMON, is_superuser=False)
    filter_class = UserBusinessInfoManagerFilter
    search_fields = ('=username', 'auth_base__nickname', '=user_invitee__salesman__username',
                     'user_invitee__salesman__salesman_name')

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            self.serializer_class = UserBusinessInfoUpdateManagerSerializer
        return super().get_serializer_class()


class BusinessInfoManagerViewSet(mixins.ListModelMixin,
                                 mixins.RetrieveModelMixin,
                                 # mixins.UpdateModelMixin,
                                 GenericViewSet):
    """商家信息后台"""
    permission_classes = (AdminPermission,)
    serializer_class = BusinessInfoManagerSerializer
    queryset = UserBusiness.objects.all()
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = UserInfoManagerFilter
    search_fields = ('=uid__username', 'uid__auth_base__nickname', 'contact')


class TeamManagerViewSet(mixins.ListModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.CreateModelMixin,
                         GenericViewSet):
    """团队管理"""
    permission_classes = (AdminPermission,)
    serializer_class = TeamManagerSerializer
    queryset = Team.objects.all()
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = TeamFilter
    search_fields = ('name', 'leader__username')

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'create']:
            self.serializer_class = TeamManagerCreateUpdateSerializer
        return super().get_serializer_class()

    @action(methods=['get'], detail=False)
    def leader(self, request, *args, **kwargs):
        """团队领导下拉框"""
        lis = []
        for user in Users.objects.filter(identity=Users.SUPERVISOR, user_team__isnull=True).order_by('-date_created'):
            lis.append(dict(uid=user.uid, username=user.username, salesman_name=user.salesman_name))
        return Response(lis)


class TeamLeaderManagerViewSet(mixins.ListModelMixin,
                               mixins.RetrieveModelMixin,
                               mixins.UpdateModelMixin,
                               mixins.CreateModelMixin,
                               GenericViewSet):
    """团队主管管理"""
    permission_classes = (AdminPermission,)
    serializer_class = TeamLeaderManagerSerializer
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = UserInfoManagerFilter
    search_fields = ('=username', 'salesman_name')

    def get_queryset(self):
        if self.action == 'list':
            self.queryset = Users.objects.filter(identity=Users.SUPERVISOR).order_by('-date_created')
        else:
            self.queryset = Users.objects.all()
        return super().get_queryset()

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            self.serializer_class = TeamLeaderManagerUpdateSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        salesman_name = request.data.get('salesman_name')
        has_power = request.data.get('has_power', False)
        if not username or not password or not salesman_name:
            return Response({'detail': '参数缺失'}, status=status.HTTP_400_BAD_REQUEST)
        phone_re = re.match(r"^1[356789]\d{9}$", username)
        if not phone_re:
            return Response({'detail': '创建失败，用户账号请输入正确的手机号'}, status=status.HTTP_400_BAD_REQUEST)
        if Users.objects.filter(username=username).exists():
            return Response({'detail': '创建失败，该账号已存在'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with atomic():
                user = Users.objects.create(username=username, identity=Users.SUPERVISOR,
                                            salesman_name=salesman_name, has_power=has_power)
                user.set_password(password)
                user.iCode = InviteCls.encode_invite_code(user.id)
                user.save()
                UserExtra.objects.create(uid=user)
                UserBase.objects.create(
                    uid=user,
                    phone=user.username
                )
                UserBusiness.objects.create(uid=user)
        except Exception as e:
            logger.info('后台创建团队主管失败')
            logger.info(e)
            return Response({'detail': '创建失败！'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': '创建成功'}, status=status.HTTP_201_CREATED)


class TeamUsersManagerViewSet(mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              mixins.UpdateModelMixin,
                              mixins.CreateModelMixin,
                              GenericViewSet):
    """团队成员管理"""
    permission_classes = (AdminPermission,)
    serializer_class = TeamUserManagerSerializer
    queryset = Users.objects.all()
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = TeamUsersManagerTeamFilter
    search_fields = ('=username', 'salesman_name')

    def get_queryset(self):
        if self.action == 'list':  # 团队成员
            self.queryset = Users.objects.filter(identity=Users.SALESMAN)
        return super().get_queryset()

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            self.serializer_class = TeamUserManagerUpdateSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        salesman_name = request.data.get('salesman_name')
        team = request.data.get('team')
        has_power = request.data.get('has_power', False)
        if not username or not password or not salesman_name or not team:
            return Response({'detail': '参数缺失'}, status=status.HTTP_400_BAD_REQUEST)
        phone_re = re.match(r"^1[35678]\d{9}$", username)
        if not phone_re:
            return Response({'detail': '创建失败，用户账号请输入正确的手机号'}, status=status.HTTP_400_BAD_REQUEST)
        if Users.objects.filter(username=username).exists():
            return Response({'detail': '创建失败，该账号已存在'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with atomic():
                user = Users.objects.create(username=username, identity=Users.SALESMAN,
                                            team_id=team, salesman_name=salesman_name, has_power=has_power)
                user.set_password(password)
                user.iCode = InviteCls.encode_invite_code(user.id)
                user.save()
                UserExtra.objects.create(uid=user)
                UserBase.objects.create(
                    uid=user,
                    phone=user.username
                )
                leader = Team.objects.get(id=team).leader
                inviter_queryset = InviteRelationManager.objects.filter(invitee=leader)
                if inviter_queryset.exists():
                    inviter_obj = inviter_queryset.first()
                    superior = f'{inviter_obj.superior}|{leader.id}'
                else:
                    superior = f'{leader.id}'
                InviteRelationManager.objects.create(inviter=leader, invitee=user, level=1, superior=superior)
                UserBusiness.objects.create(uid=user)
        except Exception as e:
            logger.info('后台创建团队成员失败')
            logger.info(e)
            return Response({'detail': '创建失败！'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': '创建成功'}, status=status.HTTP_201_CREATED)


class CelebrityStyleViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.CreateModelMixin,
                            GenericViewSet):
    """达人风格后台配置"""
    permission_classes = (AdminPermission,)
    serializer_class = CelebrityStyleSerializer
    queryset = CelebrityStyle.objects.order_by('-date_created')
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title',)


class ScriptTypeViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.CreateModelMixin,
                        GenericViewSet):
    """脚本类别后台配置"""
    permission_classes = (AdminPermission,)
    serializer_class = ScriptTypeSerializer
    queryset = ScriptType.objects.order_by('-date_created')
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title',)


class PublicWeChat(APIView):
    """公众号相关"""

    permission_classes = (AllowAny,)

    def get(self, request, **kwargs):
        _action = kwargs.get('_action', 'default')
        if not hasattr(self, _action):
            raise exceptions.NotFound()
        return getattr(self, _action)(request, **kwargs)

    def post(self, request, **kwargs):
        _action = kwargs.get('_action', 'default')
        if not hasattr(self, _action):
            raise exceptions.NotFound()
        return getattr(self, _action)(request, **kwargs)

    def default(self, request, **kwargs):
        """
        微信公众号回调处理
        """
        this_method = self.request.method.lower()
        if this_method == 'get':
            signature = request.GET.get('signature', '')
            timestamp = request.GET.get('timestamp', '')
            nonce = request.GET.get('nonce', '')
            echo_str = request.GET.get('echostr', '')
            try:
                check_signature(settings.DSJ_WECHAT_TOKEN, signature, timestamp, nonce)
            except InvalidSignatureException:
                echo_str = 'error'
            response = HttpResponse(echo_str, content_type="text/plain")
            return response
        elif this_method == 'post':
            data = trans_xml_to_dict(request.body)
            logger.info(data)
            try:
                msg_type = data.get('MsgType', None)
                if msg_type == 'event':
                    event = data.get('Event', None)
                    if event is not None:
                        func_name = f'handle_event_{event}'
                        if hasattr(HandleOfficialAccount, func_name) and \
                                callable(getattr(HandleOfficialAccount, func_name)):
                            result = getattr(HandleOfficialAccount, func_name)(data)
                            if result is not None:
                                return HttpResponse(result)
                elif msg_type == 'text':
                    result = HandleOfficialAccount.handle_msg(data)
                    if result is not None:
                        return HttpResponse(result)
            except:
                logger.error('======handle err!=======')
                logger.error(data)
                logger.error(traceback.format_exc())
            else:
                return HttpResponse("success")
        else:
            raise exceptions.MethodNotAllowed(this_method.upper())

    @custom_check_permission([ManagerPermission, ])
    def qrcode(self, request, **kwargs):
        """
        公众号二维码处理
        """
        action_lst = ['subscribe', 'login']
        this_method = self.request.method.lower()
        if this_method == 'get':
            form, error = JsonParser(
                Argument('action', filter=lambda x: x in action_lst, help="请输入正确的行为")
            ).parse(request.query_params)
            if error:
                return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
            if form.action == 'subscribe':
                key = f'subscribe_{self.request.user.uid.hex}'
                if redis_conn.exists(key):
                    value = redis_conn.get(key).decode('utf-8')
                    if str(value) == '0':
                        return Response({"detail": 'waiting'}, status=status.HTTP_200_OK)
                    elif str(value) == '1':
                        return Response({"detail": 'done'}, status=status.HTTP_200_OK)
                else:
                    return Response({"detail": 'timeout'}, status=status.HTTP_200_OK)
            elif form.action == 'login':
                return Response({"detail": "功能暂未开放"}, status=status.HTTP_400_BAD_REQUEST)
        elif this_method == 'post':
            form, error = JsonParser(
                Argument('action', filter=lambda x: x in action_lst, help="请输入正确的行为")
            ).parse(request.data)
            if error:
                return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
            if form.action == 'subscribe':
                qr_url = WeChatOfficial().get_qr_url(self.request.user.uid.hex)
                redis_conn.set(f'subscribe_{self.request.user.uid.hex}', 0, 300)
                return Response({"url": qr_url}, status=status.HTTP_200_OK)
            elif form.action == 'login':
                return Response({"detail": "功能暂未开放"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            raise exceptions.MethodNotAllowed(this_method.upper())

    @custom_check_permission([AdminPermission, ], union=False)
    def template(self, request, **kwargs):
        """公众号模板消息"""
        this_method = self.request.method.lower()
        if this_method == 'get':
            try:
                template_list = OfficialAccountMsg().get_template_list()
            except Exception as e:
                logger.info(traceback.format_exc())
                return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            result = list()
            for template in template_list:
                result.append({
                    "template_id": template.get('template_id'),
                    "title": template.get("title"),
                    "example": template.get("example"),
                    "content": content_shape(template.get("content")),
                })
            return Response(result, status=status.HTTP_200_OK)
        elif this_method == 'post':
            try:
                template_list = OfficialAccountMsg().get_template_list()
                id_dict = {i.get('template_id'): i for i in template_list}
                form, error = JsonParser(
                    Argument("template_id", help="要输入模板的id噢", filter=lambda x: x in id_dict),
                    Argument("user_list", help="请输入用户列表", type=list),
                    *[
                        Argument(i.get("field_name"), help=f"请输入{i.get('field')}{i.get('field_name')}")
                        for i in content_shape(
                            id_dict.get(request.data.get('id')).get("content")
                        ) if i.get("field_name")
                    ]
                ).parse(request.data)
                if error:
                    return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
                user_qs = Users.objects.filter(id__in=form.user_list).only('id').prefetch_related('official_account')
                form.pop("user_list")
                record_id_list = []
                for user in user_qs:
                    try:
                        OfficialAccountMsg.template_send(user, **form)
                    except Exception as e:
                        record_id_list.append(
                            {
                                'id': user.id,
                                'status': 'error',
                                'reason': str(e)
                            }
                        )
                    else:
                        record_id_list.append(
                            {
                                'id': user.id,
                                'status': 'ok',
                                'reason': '成功发送'
                            }
                        )

            except Exception as e:
                logger.info(traceback.format_exc())
                return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            raise exceptions.MethodNotAllowed(this_method.upper())


class UserBusinessDeliveryManagerViewSet(viewsets.ReadOnlyModelViewSet):
    """商家交付数据管理"""
    queryset = Users.objects.filter(identity=Users.BUSINESS, sys_role=Users.COMMON, is_superuser=False)
    permission_classes = (AdminPermission,)
    serializer_class = UserBusinessDeliveryManagerSerializer
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = UserBusinessDeliveryManagerFilter
    search_fields = ('=username', 'auth_base__nickname')
