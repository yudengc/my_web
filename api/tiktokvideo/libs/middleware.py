import json
import logging

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django_redis import get_redis_connection
from redis import StrictRedis
from rest_framework import status, exceptions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from flow_limiter.services import FlowLimiter
from libs.common.utils import get_ip
from users.models import Users

logger = logging.getLogger()
conn = get_redis_connection('default')  # type: StrictRedis


def is_json(json_str):
    try:
        _json = json.loads(json_str)
        if 'items' in dir(_json):
            return True
        else:
            return False
    except ValueError:
        return False


class ResponseMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            # for content_type in settings.HTTP_HEADER_ROUTING_MIDDLEWARE_URLCONF_MAP:
            if request.META['HTTP_ACCEPT'].find('text/xml,text/javascript,text/html') != -1:
                request.META['HTTP_ACCEPT'] = 'application/json'
        except KeyError:
            pass

    def process_response(self, request, response):
        status_code = response.status_code
        if status_code in [400, ]:
            logger.info('错误信息')
            logger.info(status_code)
            res = response.content.decode()
            logger.info(res)
            if is_json(res):
                if 'detail' not in json.loads(res):
                    res_text = ''
                    for k, v in json.loads(res).items():
                        if isinstance(v, list):
                            res_text += k + v[0]
                        else:
                            return response
                    return JsonResponse({'detail': res_text.replace(' ', '')}, status=status.HTTP_400_BAD_REQUEST)
        return response


class FrozenCheckMiddleware(MiddlewareMixin):

    def __call__(self, request):
        response = None
        if isinstance(request.user, Users):
            req = request
        elif hasattr(request, '_req'):
            req = request._req
        else:
            req = Request(
                request,
                authenticators=[JSONWebTokenAuthentication()],
            )
            request._req = req
        if isinstance(req.user, Users):
            if req.user.status == Users.FROZEN:
                # 冻结用户的所有 post, put, patch, delete 请求都屏蔽了
                if request.method.lower() in ['post', 'put', 'patch', 'delete']:
                    return JsonResponse({"detail": "该账号已被冻结, 无法执行该操作, 解冻请联系客服"},
                                        status=status.HTTP_206_PARTIAL_CONTENT)
        response = response or self.get_response(request)
        return response


class FlowLimitMiddleware(MiddlewareMixin):

    def __call__(self, request):
        response = None
        use_latest = settings.FLOW_LIMITER.get('use_latest', False)
        global_setting = settings.FLOW_LIMITER.get('global', None)
        if isinstance(request.user, Users):
            req = request
        elif hasattr(request, '_req'):
            req = request._req
        else:
            req = Request(
                request,
                authenticators=[JSONWebTokenAuthentication()],
            )
            request._req = req
        if global_setting:
            if isinstance(req.user, AnonymousUser):
                # 用这个ip作为身份辨识貌似有点问题
                host = get_ip(request)
                key = f"{host}_nonuser"
                limiter_key = 'nonuser'
            else:
                # 登录之后用uid作为辨识
                key = f"{req.user.uid.hex}_user"
                limiter_key = 'user'
            trigger_return = FlowLimiter.trigger(limiter_key, key, use_latest)
            if isinstance(trigger_return, bool):
                func_return = self.get_response(request)
                if isinstance(func_return, Response):
                    if trigger_return and use_latest:
                        latest_return_data = f"latest_data_{key}"
                        latest_return_code = f"latest_code_{key}"
                        conn.set(latest_return_data, json.dumps(func_return.data), 86400)
                        conn.set(latest_return_code, func_return.status_code, 86400)
                return func_return
            elif isinstance(trigger_return, Response):
                return JsonResponse(trigger_return.data, status=trigger_return.status_code)
            elif isinstance(trigger_return, exceptions.Throttled):
                return JsonResponse({"detail": trigger_return.detail},
                                    status=trigger_return.status_code)

        response = response or self.get_response(request)
        return response
