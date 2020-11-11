# -*- coding: utf-8 -*-
# @Time    : 2020/2/17 10:28 PM
# @Author  : HF

from rest_framework.settings import api_settings
from rest_framework_jwt.utils import *

from tiktokvideo.settings import JWT_AUTH
from users.serializers import UsersLoginSerializer


def jwt_payload_handler(user):
    username_field = get_username_field()
    account = get_username(user)

    payload = {
        'id': user.pk,
        'uid': user.uid,
        'username': user.username,
        'exp': datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA
    }
    if isinstance(user.pk, uuid.UUID):
        payload['user_id'] = str(user.pk)

    payload[username_field] = account
    # Include original issued at time for a brand new token,
    # to allow token refresh
    if api_settings.JWT_ALLOW_REFRESH:
        payload['orig_iat'] = timegm(
            datetime.utcnow().utctimetuple()
        )

    if api_settings.JWT_AUDIENCE is not None:
        payload['aud'] = api_settings.JWT_AUDIENCE

    if api_settings.JWT_ISSUER is not None:
        payload['iss'] = api_settings.JWT_ISSUER

    return payload


def jwt_response_payload_handler(token, user=None, request=None):
    """
    Returns the response data for both the login and refresh views.
    Override to return a custom response such as including the
    serialized representation of the User.

    Example:

    def jwt_response_payload_handler(token, user=None, request=None):
        return {
            'token': token,
            'user': UserSerializer(user, context={'request': request}).data
        }

    """
    return {

        "token": JWT_AUTH.get('JWT_AUTH_HEADER_PREFIX') + ' ' + token,
        "expires_in": datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA,
        "user_info": UsersLoginSerializer(user, context={'request': request}).data

    }
