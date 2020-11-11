# Create your views here

from django.contrib.auth.hashers import check_password
from rest_framework import permissions, mixins, exceptions
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.relations.tasks import save_invite_relation
from users.models import Users, UserExtra, UserBase
from libs.common.permission import ManagerPermission
from libs.jwt.serializers import CusTomSerializer
from libs.jwt.services import JwtServers

from users.services import WXBizDataCrypt, WeChatApi
from tiktokdata.config.settings.base import APP_ID, SECRET


class LoginViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = CusTomSerializer

    @action(methods=['post', ], detail=False, permission_classes=[permissions.AllowAny])
    def admin(self, request):
        """
        超管端登陆接口
        username: 用户名/手机号
        password : 密码
        :param request:
        :return:
        """
        serializer = self.get_serializer(data=request.data)
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({"detail": '请输入账号/密码'}, status=status.HTTP_400_BAD_REQUEST)
        user = Users.objects.filter(username=username, status=0).last()
        if not user:
            return Response({"detail": "用户不存在"}, status=status.HTTP_400_BAD_REQUEST)
        if not check_password(password, user.password):
            return Response({"detail": '密码错误!'}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            data = getattr(JwtServers(user=user), 'get_token_and_user_info')()
            return Response(data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post', ], detail=False, permission_classes=[permissions.AllowAny])
    def auth(self, request):
        """微信授权登录"""
        openid = request.data.get('openid', None)
        username = request.data.get('username', None)
        role = request.data.get('role', None)
        user_info = request.data.get('userInfo', None)
        category = request.data.get('category', None)
        code = request.data.get('iCode', None)
        if not openid and not username:
            return Response({"detail": "缺少参数!"}, status=status.HTTP_400_BAD_REQUEST)
        user_instance = self.save_user_and_openid(username, openid, role, user_info, category)
        user_info = JwtServers(user=user_instance).get_token_and_user_info()
        if code:  # 存在注册码绑定邀请关系
            save_invite_relation.delay(code, username)  # 绑定邀请关系
        return Response(user_info, status=status.HTTP_200_OK)

    @action(methods=['post', ], detail=False, permission_classes=[permissions.AllowAny])
    def get_phone(self, request):
        """获取手机号码"""
        if {'session_key', 'encrypted_data', 'iv'}.issubset(set(request.data.keys())):
            session_key = request.data.get('session_key')
            encrypted_data = request.data.get('encrypted_data')
            iv = request.data.get('iv')
            pc = WXBizDataCrypt(APP_ID, session_key)
            data = pc.decrypt(encrypted_data, iv)
            if not data:
                return Response({'code': 0, 'detail': 'session_key错误/已过期'}, status=status.HTTP_200_OK)
            user_qs = Users.objects.filter(username=data.get('purePhoneNumber'))
            if user_qs.exists():
                is_exists = True
            else:
                is_exists = False
            return Response(data={'code': 1, 'phone': data.get('purePhoneNumber'), 'is_exists': is_exists}, status=status.HTTP_200_OK)
        return Response({'detail': '缺少参数'}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post', ], detail=False, permission_classes=[permissions.AllowAny])
    def get_openid(self, request):
        """获取openid"""
        code = request.data.get('code', None)
        if code:
            openid, session_key = WeChatApi(APP_ID, SECRET).get_openid_and_session_key(code)
            return Response({'openid': openid, 'session_key': session_key}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'code不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    def save_user_and_openid(self, username, openid, role=None, user_info=None, category=None):
        """保存用户信息以及openid"""
        user_qs = Users.objects.filter(username=username)
        if not user_qs.exists():
            user = Users.objects.create(
                username=username,
                openid=openid,
                identity=role,
                category=category,
            )
            UserExtra.objects.create(uid=user)
            UserBase.objects.create(
                uid=user,
                phone=username,
                nickname=user_info.get('nickName'),
                avatars=user_info.get('avatarUrl')
            )
        user = user_qs.first()
        if user.status == Users.FROZEN:
            raise exceptions.ParseError('用户已被冻结，请联系管理员')
        # 是否换微信登录
        if user.openid != openid:
            user_qs.update(openid=openid)
        return user












