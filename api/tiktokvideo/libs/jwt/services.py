
from datetime import datetime

from rest_framework_jwt.settings import api_settings

from libs.jwt.token_return import jwt_response_payload_handler

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class JwtServers:

    def __init__(self, user=None):
        self.user = user

    def get_token_and_user_info(self, request=None):
        user = self.user
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        response = jwt_response_payload_handler(token, user, request)
        if api_settings.JWT_AUTH_COOKIE:
            expiration = (datetime.utcnow() +
                          api_settings.JWT_EXPIRATION_DELTA)
            response.set_cookie(api_settings.JWT_AUTH_COOKIE,
                                token,
                                expires=expiration,
                                httponly=True)
        return response


