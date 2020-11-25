import logging
import threading

from django.contrib.auth.hashers import check_password
from django_filters.rest_framework import DjangoFilterBackend
from django_redis import get_redis_connection
from redis import StrictRedis
from rest_framework import mixins, exceptions, filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from libs.common.permission import AllowAny, SalesmanPermission, ManagerPermission
from relations.tasks import save_invite_relation

from tiktokvideo.base import APP_ID, SECRET
from users.filter import TeamFilter
from users.models import Users, UserExtra, UserBase, Team, UserBusiness, ScriptType, CelebrityStyle, Address
from libs.jwt.serializers import CusTomSerializer
from libs.jwt.services import JwtServers
from users.serializers import UserBusinessSerializer, UserBusinessCreateSerializer, TeamSerializer, UserInfoSerializer, \
    AddressSerializer, AddressListSerializer

from users.services import WXBizDataCrypt, WeChatApi, InviteCls

redis_conn = get_redis_connection('default')  # type: StrictRedis
logger = logging.getLogger()


class LoginViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = CusTomSerializer

    @action(methods=['post', ], detail=False, permission_classes=[AllowAny])
    def admin(self, request):
        """
        超管端登陆接口
        username: 用户名/手机号
        password : 密码
        :param request:
        :return:
        """
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({"detail": '请输入账号/密码'}, status=status.HTTP_400_BAD_REQUEST)
        user = Users.objects.filter(username=username, status=0, identity=Users.SALESMAN).last()
        if not user:
            return Response({"detail": "用户不存在"}, status=status.HTTP_400_BAD_REQUEST)
        if not check_password(password, user.password):
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
        user_info = request.data.get('userInfo', None)
        code = request.data.get('iCode', None)
        if not openid and not username:
            return Response({"detail": "缺少参数!"}, status=status.HTTP_400_BAD_REQUEST)
        user_instance = self.save_user_and_openid(username, openid, user_info)
        user_info = JwtServers(user=user_instance).get_token_and_user_info()
        if code:  # 存在注册码绑定邀请关系
            # save_invite_relation.delay(code, username)  # 绑定邀请关系
            logger.info('准备进入线程')
            threading.Thread(target=save_invite_relation,
                             args=(code, username)).start()  # 绑定邀请关系
            logger.info('结束线程')
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

    def save_user_and_openid(self, username, openid, user_info=None):
        """保存用户信息以及openid"""
        user_qs = Users.objects.filter(username=username)
        if not user_qs.exists():
            user = Users.objects.create(
                username=username,
                openid=openid,
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
        else:
            # 如果后台创建的用户要补充微信信息
            user = user_qs.first()
            user_base = UserBase.objects.filter(uid=user).first()
            if user_base:
                user_base.phone = username
                user_base.nickname = user_info.get('nickName')
                user_base.avatars = user_info.get('avatarUrl')
                user_base.save()

        if user.status == Users.FROZEN:
            raise exceptions.ParseError('用户已被冻结，请联系管理员')
        # 是否换微信登录
        if user.openid != openid:
            user_qs.update(openid=openid)
        return user


class TeamViewSet(viewsets.ModelViewSet):
    permission_classes = (SalesmanPermission,)
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    search_fields = ('name', 'leader__username')
    filter_class = TeamFilter


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
    serializer_class = UserInfoSerializer

    def get_queryset(self):
        self.queryset = Users.objects.select_related('user_business').filter(uid=self.request.user.uid)
        return super().get_queryset()

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
    permission_classes = ManagerPermission
    serializer_class = AddressSerializer

    def get_serializer_class(self):
        if self.action in ['list', ]:
            return AddressListSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        self.queryset = Address.objects.filter(uid=self.request.user).extra(
            select={'default': 'is_default=1'}).order_by('-create_time').order_by('-default')
        return super(AddressViewSet, self).get_queryset()
