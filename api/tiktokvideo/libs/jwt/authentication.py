"""重写了JSONWebTokenAuthentication认证"""
import jwt
from django.utils.encoding import smart_text
from django.utils.translation import ugettext as _
from rest_framework import exceptions
from rest_framework.authentication import (BaseAuthentication, get_authorization_header)
from rest_framework_jwt.settings import api_settings

from users.models import Users

jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER


class BaseJSONWebTokenAuthentication(BaseAuthentication):
    """
    Token based authentication using the JSON Web Token standard.
    """

    def get_jwt_value(self, request):
        pass

    def authenticate(self, request):
        """
        Returns a two-tuple of `User"and token if a valid signature has been
        supplied using JWT-based authentication.  Otherwise returns `None`.
        """

        jwt_value = self.get_jwt_value(request)  # token
        if jwt_value is None:
            return None
        try:
            payload = jwt_decode_handler(jwt_value)  # {'username': '15917350598', 'user_id': 6, 'exp': 1535426862}
        except jwt.ExpiredSignature:
            result = {
                "detail": "登陆信息已失效，请重新登陆！"
            }
            raise exceptions.AuthenticationFailed(result)
        except jwt.DecodeError:
            result = {
                "detail": "token格式错误！"
            }
            raise exceptions.AuthenticationFailed(result)
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed()
        user = self.authenticate_credentials(payload)

        return (user, jwt_value)
        # 返回去用户和token进行认证"

    def authenticate_credentials(self, payload):
        """
        Returns an active user that matches the payload's user id and email.
        """
        username = payload.get('username')  # 如果更新用户信息时更改到手机号，则要重新登录获取新的token
        if not username:
            msg = _('Invalid payload.')
            raise exceptions.AuthenticationFailed(msg)
        try:
            user = Users.objects.get(username=username)
        except Users.DoesNotExist:
            msg = _('Invalid signature.')
            raise exceptions.AuthenticationFailed(msg)
        return user


class JSONWebTokenAuthentication(BaseJSONWebTokenAuthentication):
    """
    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string specified in the setting
    `JWT_AUTH_HEADER_PREFIX`. For example:

        Authorization: JWT eyJhbGciOiAiSFMyNTYiLCAidHlwIj
    """
    www_authenticate_realm = 'api'

    def get_jwt_value(self, request):
        auth = get_authorization_header(request).split()
        auth_header_prefix = api_settings.JWT_AUTH_HEADER_PREFIX.lower()

        if not auth:
            if api_settings.JWT_AUTH_COOKIE:
                return request.COOKIES.get(api_settings.JWT_AUTH_COOKIE)
            return None

        if smart_text(auth[0].lower()) != auth_header_prefix:
            return None

        if len(auth) == 1:
            msg = _('Invalid Authorization header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid Authorization header. Credentials string '
                    'should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)
        return auth[1]

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated"response, or `None"if the
        authentication scheme should return `403 Permission Denied"responses.
        """
        return '{0} realm="{1}"'.format(api_settings.JWT_AUTH_HEADER_PREFIX, self.www_authenticate_realm)
