"""
Django settings for tiktokvideo project.

Generated by 'django-admin startproject' using Django 2.2.9.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""
import datetime
import os
from tiktokvideo.admin import *

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'a+42^l7a=^y=!b#kmcls)os2q5@36wz&)3-l%pwzi07h8s_ko2'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'simpleui',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'safedelete',
    'ckeditor',
    'flow_limiter',

    # app
    'users',
    'transaction',
    'config',
    'relations',
    'demand',
    'application',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'libs.middleware.FrozenCheckMiddleware',
    'libs.middleware.FlowLimitMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'libs.middleware.ResponseMiddleware',
]

ROOT_URLCONF = 'tiktokvideo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tiktokvideo.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DATABASE_NAME'),
        'USER': os.environ.get('DATABASE_USER'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD'),
        'HOST': os.environ.get('DATABASE_HOST'),
        'PORT': os.environ.get('DATABASE_PORT'),
    }
}


# 限流器
FLOW_LIMITER = {
    'use_latest': bool(os.environ.get("USE_LATEST", 0)),
    'global': {
        'user': '1000/day;',
        'nonuser': '100/day;',
    },
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
AUTH_USER_MODEL = 'users.Users'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static').replace('\\', '/'),
)
SITE_ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_ROOT = os.path.abspath(os.path.join(SITE_ROOT, '../'))
STATIC_ROOT = os.path.join(SITE_ROOT, 'collectstatic')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'tiktokvideo/media').replace('\\', '/')

# ############# REST FRAMEWORK ###################

REST_FRAMEWORK = {

    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'libs.pagination.StandardResultsSetPagination',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # 'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'libs.jwt.authentication.JSONWebTokenAuthentication',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
}


# ################### Cache SETTINGS ##########################
CACHE_COUNT_TIMEOUT = 60
CACHE_MACHINE_USE_REDIS = True
CACHE_MACHINE_NO_INVALIDATION = False
REDIS_BACKEND = os.environ.get('REDIS_BACKEND', 'redis://localhost:6379')
DEFAULT_TIMEOUT = 60

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_BACKEND}/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}


# ################### Celery SETTINGS ##########################
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')
CELERY_TASK_RESULT_EXPIRES = os.environ.get('CELERY_TASK_RESULT_EXPIRES', 60)
CELERY_BROKER_URL = os.environ.get('BROKER_URL')
CELERY_TASK_IGNORE_RESULT = True
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_SEND_TASK_SENT_EVENT = True
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']


# Json web token 设置/ 登陆凭证设置
JWT_AUTH = {
    #'JWT_EXPIRATION_DELTA': datetime.timedelta(days=int(os.environ.get('DAYS'))),
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=30),
    'JWT_AUTH_HEADER_PREFIX': os.environ.get('HEADER_PREFIX'),
}

# 微信小程序
APP_ID = os.environ.get('APP_ID')
SECRET = os.environ.get('SECRET')
# 微信支付
MCH_ID = os.environ.get('MCH_ID')
MCH_KEY = os.environ.get('MCH_KEY')
PAY_NOTIFY_URL = os.environ.get('PAY_NOTIFY_URL')

# 七牛云存储配置
QINIU_ACCESS_KEY = os.environ.get('QINIU_ACCESS_KEY')
QINIU_SECRET_KEY = os.environ.get('QINIU_SECRET_KEY')
QINIU_BUCKET_NAME = os.environ.get('QINIU_BUCKET_NAME')
QINIU_BUCKET_DOMAIN = os.environ.get('QINIU_BUCKET_DOMAIN')
IMG_QINIU_BUCKET_NAME = os.environ.get('IMG_QINIU_BUCKET_NAME')

# 好单库配置(详情：https://www.haodanku.com/api/detail/show/19.html)
HDK_API_KEY = os.environ.get('HDK_API_KEY')

# ################### DouYin SETTINGS ##########################
DY_CLIENT_KEY = os.environ.get('CLIENT_KEY')
DY_CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
DY_CHECK_HOME_URL = 'http://120.78.203.56:10088/api/check/shop'
DY_GET_USER_URL = 'http://120.78.203.56:10666/api/web/user'
# DY_CHECK_HOME_URL = 'http://119.23.109.99:10088/api/check/shop',  # 备用的，用的测试服
DY_CHECK_GOODS_URL = 'http://120.78.203.56:10088/api/check/commission'
DY_CHECK_SHOP_URL = 'http://120.78.203.56:10088/api/check/xiaodian'
DY_COUPON_MSG_URL = 'http://120.78.203.56:10088/api/query/shop_coupon'