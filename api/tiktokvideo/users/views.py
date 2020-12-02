import logging
import re
import threading

from celery import shared_task
from django.contrib.auth.hashers import check_password
from django.db.transaction import atomic
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

from account.models import CreatorAccount
from libs.common.permission import AllowAny, ManagerPermission, CreatorPermission, AdminPermission
from libs.parser import JsonParser, Argument
from relations.models import InviteRelationManager
from relations.tasks import save_invite_relation

from tiktokvideo.base import APP_ID, SECRET
from users.filter import TeamFilter, UserInfoManagerFilter, UserCreatorInfoManagerFilter, UserBusinessInfoManagerFilter, \
    TeamUsersManagerTeamFilter
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
    TeamLeaderManagerUpdateSerializer, CelebrityStyleSerializer, ScriptTypeSerializer

from users.services import WXBizDataCrypt, WeChatApi, InviteCls

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
        user = Users.objects.filter(username=form.username, status=0, sys_role__in=[Users.ADMIN, Users.SUPER_ADMIN]).last()
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
        logger.info('开始登陆')
        openid = request.data.get('openid', None)
        username = request.data.get('username', None)
        logger.info('打印username')
        logger.info(username)
        user_info = request.data.get('userInfo', None)
        logger.info(user_info)
        code = request.data.get('iCode')
        identity = request.data.get('identity')
        if not openid or not username or not identity:
            # if not openid or not username:
            return Response({"detail": "缺少参数!"}, status=status.HTTP_400_BAD_REQUEST)
        user_instance = self.save_user_and_openid(username, openid, identity, user_info)

        if user_instance.status == Users.FROZEN:
            return Response({'detail': '账户被冻结，请联系客服处理', 'code': 444}, status=status.HTTP_200_OK)
        user_info = JwtServers(user=user_instance).get_token_and_user_info()
        if code and identity == Users.BUSINESS:  # 存在注册码绑定邀请关系
            # save_invite_relation.delay(code, username)  # 绑定邀请关系
            threading.Thread(target=save_invite_relation,
                             args=(code, username)).start()  # 绑定邀请关系
        return Response(user_info, status=status.HTTP_200_OK)

    @action(methods=['post', ], detail=False, permission_classes=[AllowAny])
    def get_phone(self, request):
        """获取手机号码"""
        if {'encrypted_data', 'iv', 'openid'}.issubset(set(request.data.keys())):
            openid = request.data.get('openid')
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

    # @action(methods=['post', ], detail=False, permission_classes=[AllowAny])
    # def get_unionid(self, request):
    #     form, error = JsonParser(
    #         Argument("encryptedData", handler=lambda x: decode_encrypted_data(x), help="请输入加密信息")
    #     )
    #     if error:
    #         return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)
    #     union_id = None
    #     return Response({"detail": union_id})

    @action(methods=['post', ], detail=False, permission_classes=[AllowAny])
    def get_openid(self, request):
        """获取openid"""
        code = request.data.get('code', None)
        if code:
            openid, session_key = WeChatApi(APP_ID, SECRET).get_openid_and_session_key(code)
            redis_conn.set(openid, session_key)
            return Response({'openid': openid}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'code不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    def save_user_and_openid(self, username, openid, select_identity, user_info=None):
        """保存用户信息以及openid"""
        if not username:
            raise exceptions.ParseError('username不能为空')
        user_qs = Users.objects.filter(username=username)
        if not user_qs.exists():
            user = Users.objects.create(
                username=username,
                openid=openid,
                identity=select_identity
            )
            user.iCode = InviteCls.encode_invite_code(user.id)
            user.save()
            UserExtra.objects.create(uid=user)
            UserBusiness.objects.create(uid=user)
            UserBase.objects.create(
                uid=user,
                phone=username,
                nickname=user_info.get('nickName'),
                avatars=user_info.get('avatarUrl')
            )
            if select_identity == Users.CREATOR:
                UserCreator.objects.create(uid=user)
                CreatorAccount.objects.create(uid=user)
        else:
            # 如果后台创建的用户要补充微信信息
            user = user_qs.first()
            user_identity = user.identity
            user_base = UserBase.objects.filter(uid=user).first()
            if user_base:
                user_base.phone = username
                user_base.nickname = user_info.get('nickName')
                user_base.avatars = user_info.get('avatarUrl')
                user_base.save()
            if user_identity == Users.CREATOR:
                if select_identity != Users.CREATOR:
                    raise exceptions.ParseError('请选择创作者角色登陆')
            elif user_identity in [Users.BUSINESS, Users.SALESMAN, Users.SUPERVISOR]:  # 商家，业务员，主管都用商家端
                if select_identity != Users.BUSINESS:
                    raise exceptions.ParseError('请选择商家角色登陆')
            else:
                raise exceptions.ParseError('角色错误')

        # 是否换微信登录
        if user.openid != openid:
            user_qs.update(openid=openid)
        return user


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
    queryset = Address.objects.all()


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
    queryset = Users.objects.exclude(is_superuser=True).order_by('-date_created')
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = UserInfoManagerFilter
    search_fields = ('username', 'auth_base__nickname')


class UserCreatorInfoManagerViewSet(mixins.ListModelMixin,
                                    mixins.RetrieveModelMixin,
                                    mixins.UpdateModelMixin,
                                    GenericViewSet):
    """创作者用户管理"""
    permission_classes = (AdminPermission,)
    serializer_class = UserCreatorInfoManagerSerializer
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_class = UserCreatorInfoManagerFilter
    search_fields = ('uid__username', 'uid__auth_base__nickname')

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
    queryset = Users.objects.exclude(is_superuser=True).filter(identity=Users.BUSINESS, sys_role=Users.COMMON)
    filter_class = UserBusinessInfoManagerFilter
    search_fields = ('username', 'auth_base__nickname', 'user_salesman__salesman__username')

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
    search_fields = ('uid__username', 'uid__auth_base__nickname', 'contact')


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
    search_fields = ('username', 'salesman_name')

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
        if not username or not password or not salesman_name:
            return Response({'detail': '参数缺失'}, status=status.HTTP_400_BAD_REQUEST)
        phone_re = re.match(r"^1[35678]\d{9}$", username)
        if not phone_re:
            return Response({'detail': '创建失败，用户账号请输入正确的手机号'}, status=status.HTTP_400_BAD_REQUEST)
        if Users.objects.filter(username=username).exists():
            return Response({'detail': '创建失败，该账号已存在'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with atomic():
                user = Users.objects.create(username=username, identity=Users.SUPERVISOR, salesman_name=salesman_name)
                user.set_password(password)
                user.iCode = InviteCls.encode_invite_code(user.id)
                user.save()
                UserExtra.objects.create(uid=user)
                UserBase.objects.create(
                    uid=user,
                    phone=user.username
                )
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
    search_fields = ('username', 'salesman_name')

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
                                            team_id=team, salesman_name=salesman_name)
                user.set_password(password)
                user.iCode = InviteCls.encode_invite_code(user.id)
                user.save()
                UserExtra.objects.create(uid=user)
                UserBase.objects.create(
                    uid=user,
                    phone=user.username
                )
                leader = Team.objects.get(id=team).leader
                InviteRelationManager.objects.create(inviter=leader, invitee=user, level=1)
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
    search_fields = ('title', )


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
    search_fields = ('title', )


@shared_task
def ee():
    print('celery12312312312')


class Test(APIView):
    permission_classes = (AllowAny, )

    def get(self, request):
        ee.delay()
