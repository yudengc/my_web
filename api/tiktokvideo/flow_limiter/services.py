import json
import re
import sys
import time
from functools import wraps

import redis
from django.conf import settings
from redis import StrictRedis
from django_redis import get_redis_connection
from rest_framework import exceptions, status
from rest_framework.request import Request
from rest_framework.response import Response

from libs.common.utils import get_ip

conn = get_redis_connection('default')  # type: StrictRedis


class FlowLimiter:
    """
    limited格式:
        数字/时间(day, hour, minute, second),
        多个用分号隔开, 如:
            10000/day;1000/hour;100/minute;10/second;
    """

    limited_str = r'^(\d+/(day|hour|minute|second);){1,4}$'
    limited_pattern = re.compile(limited_str)
    limited_former = "flow_limiter"
    trigger_former = "trigger"
    size = 100

    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def set_limited(cls, limiter_key: str, limited: str):
        if not limiter_key:
            raise ValueError("请输入limiter_key。")
        if not cls.limited_pattern.match(limited):
            raise ValueError(f"limited格式错误: 1000/(day/hour/minute/second);[分号隔开]。 当前key: {limited}")
        key = f"{cls.limited_former}_{limiter_key}"
        conn.set(key, limited)
        return True

    @classmethod
    def del_limited(cls, action: str):
        if not action:
            raise ValueError("请输入action。")
        key = f"{cls.limited_former}_{action}"
        if conn.exists(key):
            conn.delete(key)
            return True
        return False

    @classmethod
    def trigger(cls, limit_key: str, action_key: str, use_latest: bool):
        limited_key = f"{cls.limited_former}_{limit_key}"
        if conn.exists(limited_key):
            now = int(time.time())
            limited_str = conn.get(limited_key).decode('utf-8')
            limited_list = [i for i in limited_str.split(';') if i]
            limit_dict = {}
            for limit in limited_list:
                value, key = limit.split('/')
                if key == 'day':
                    limit_dict[86400] = int(value)
                elif key == 'hour':
                    limit_dict[3600] = int(value)
                elif key == 'minute':
                    limit_dict[60] = int(value)
                elif key == 'second':
                    limit_dict[1] = int(value)
            trigger_key = f"{cls.trigger_former}_{action_key}"
            this_sec_count = conn.zcount(trigger_key, now, now)
            wait_sec = 0
            min_sec = sys.maxsize
            record_last = False
            for k, v in limit_dict.items():
                min_sec = min(min_sec, now - k)
                trigger_history_lst = conn.zrangebyscore(trigger_key, now - k, now, num=v + 1, withscores=True, start=0)
                length = len(trigger_history_lst)
                if length >= v:
                    this_wait_sec = trigger_history_lst[0][1] + k - now
                    if this_wait_sec > wait_sec:
                        wait_sec = this_wait_sec
                elif length == v - 1:
                    record_last = True
            conn.zremrangebyscore(trigger_key, 0, min_sec - 1)
            if wait_sec > 0:
                latest_return_data = f"latest_data_{action_key}"
                latest_return_code = f"latest_code_{action_key}"
                if use_latest and conn.exists(latest_return_data):
                    print(f'{action_key}:用缓存, wait:{wait_sec}')
                    latest_data = json.loads(conn.get(latest_return_data).decode('utf-8').replace('\'', '\"'))
                    latest_code = int(conn.get(latest_return_code))
                    return Response(latest_data, status=latest_code)
                else:
                    return exceptions.Throttled(detail=f"操作太频繁, 请等等(剩余秒数:{int(wait_sec)})")
            else:
                try:
                    conn.zadd(trigger_key, {f"{now}_{this_sec_count}": now})
                except redis.exceptions.RedisError:
                    '''
                    redis 2.10.x版本的 zadd用法是 zadd(key-name, score, member)
                    redis 3.0版本的zadd用法是 zadd(key0-name, {member:score})
                    '''
                    conn.zadd(trigger_key, now, f"{now}_{this_sec_count}")
                return record_last

    # 函数装饰器
    @staticmethod
    def limited_decorator(limited: str, use_latest: bool = settings.FLOW_LIMITER.get('use_latest', False)):

        def deco_func(func):
            limit_key = func.__hash__()
            FlowLimiter.set_limited(limit_key, limited)

            @wraps(func)
            def wrapper(*args, **kwargs):
                request = args[1]
                if not isinstance(request, Request):
                    raise exceptions.APIException(detail="请求错误, 无法获取request",
                                                  code=status.HTTP_500_INTERNAL_SERVER_ERROR)
                action_key = f"{get_ip(request)}_{request.path}"
                trigger_return = FlowLimiter.trigger(limit_key, action_key, use_latest)
                if isinstance(trigger_return, bool):
                    func_return = func(*args, **kwargs)
                    if isinstance(func_return, Response):
                        if trigger_return and use_latest:
                            latest_return_data = f"latest_data_{action_key}"
                            latest_return_code = f"latest_code_{action_key}"
                            conn.set(latest_return_data, json.dumps(func_return.data), 86400)
                            conn.set(latest_return_code, func_return.status_code, 86400)
                    return func_return
                elif isinstance(trigger_return, Response):
                    return trigger_return
                elif isinstance(trigger_return, exceptions.Throttled):
                    raise trigger_return

            return wrapper

        return deco_func
