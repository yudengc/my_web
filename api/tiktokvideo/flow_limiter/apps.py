from django.apps import AppConfig
from django.conf import settings

from flow_limiter.services import FlowLimiter
from libs.parser import JsonParser, Argument


# example:
# FLOW_LIMITER = {
#     'use_latest': bool(os.environ.get("USE_LATEST")),
#     'global': {
#         'user': '1000/day;',
#         'nonuser': '100/day;',
#     },
# }

class FlowLimiterConfig(AppConfig):
    name = 'flow_limiter'

    def ready(self):
        flow_limiter_setting = getattr(settings, 'FLOW_LIMITER', None)
        if not flow_limiter_setting:
            raise ValueError("缺少FLOW_LIMITER参数, 请在setting里面配置")
        form, error = JsonParser(
            Argument('use_latest', type=bool, help='请配置是否使用限流缓存(use_latest: bool)'),
            Argument('global', type=dict,
                     help='请配置全局规则(global: {"nonuser": "1000/day;", "user": "2000/day;"})',
                     filter=lambda x: x.get('user') and x.get('nonuser')
                     ),
        ).parse(flow_limiter_setting)
        if error:
            raise ValueError(error)
        user_limit = form['global'].get('user')
        nonuser_limit = form['global'].get('nonuser')
        FlowLimiter.set_limited('user', user_limit)
        FlowLimiter.set_limited('nonuser', nonuser_limit)
