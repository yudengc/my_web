import stat

from tiktokvideo.base import *


from datetime import timedelta

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True
#
# ALLOWED_HOSTS = ['*']

# 创建log日志路径
LOG_PATH = '/var/log/projects_logs/tiktokvideo/'

LOGGING = {
    'version': 1,  # 保留字
    'disable_existing_loggers': False,  # 禁用已经存在的logger实例
    # 日志文件的格式
    'formatters': {
        # 详细的日志格式
        'standard': {
            'format': '[%(asctime)s]-[%(filename)s:%(lineno)d]-%(levelname)s: %(message)s'
        },
    },
    # 过滤器
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    # 处理器
    'handlers': {
        # 默认的
        'default': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件，自动切
            'filename': '%s/all.log' % LOG_PATH,  # 日志文件
            'maxBytes': 1024 * 1024 * 500,  # 日志大小 500M
            'backupCount': 10,  # 最多备份几个
            'formatter': 'standard',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        # 默认的logger应用如下配置
        '': {
            'handlers': ['default'],  # 上线之后可以把'console'移除
            'level': 'DEBUG',
            'propagate': True,  # 向不向更高级别的logger传递
        },

    },
}

# ################### CORS SETTINGS ##########################

CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True


