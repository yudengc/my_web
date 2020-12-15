# -*- coding: utf-8 -*-
"""
@Time    : 2020/10/26 10:49 上午
@Author  : LuckyTom
@File    : services.py
"""
import base64
import json
import logging
from xml.etree.ElementTree import tostring

import requests
from Crypto.Cipher import AES
from django.conf import settings
from django_redis import get_redis_connection
from redis import StrictRedis

from libs.utils import trans_dict_to_xml
from users.models import Users

conn = get_redis_connection('default')  # type: StrictRedis
logger = logging.getLogger()


class WeChatApi:

    def __init__(self, appid, secret):
        self.app_id = appid
        self.secret = secret
        self.union_id = None
        self.openid = None
        self.session_key = None

    def get_openid_and_session_key(self, code):
        params = {
            'appid': self.app_id,
            'secret': self.secret,
            'js_code': code,
            'grant_type': 'authorization_code'
        }
        url = 'https://api.weixin.qq.com/sns/jscode2session'
        r = requests.get(url, params=params)
        openid = r.json().get('openid', '')
        self.union_id = r.json().get('unionid')
        session_key = r.json().get('session_key', '')
        return openid, session_key

    def get_union_id(self):
        return self.union_id


class WXBizDataCrypt:
    def __init__(self, app_id, session_key):
        self.app_id = app_id
        self.sessionKey = session_key

    def decrypt(self, encrypted_data, iv):
        # base64 decode
        try:
            # print(self.sessionKey)
            session_key = base64.b64decode(self.sessionKey)
            encrypted_data = base64.b64decode(encrypted_data)
            iv = base64.b64decode(iv)
            cipher = AES.new(session_key, AES.MODE_CBC, iv)
            sign = self._unpad(cipher.decrypt(encrypted_data)).decode()
            decrypted = json.loads(sign)
            if decrypted['watermark']['appid'] != self.app_id:
                raise Exception('Invalid Buffer')
            return decrypted

        except Exception as e:
            print(e)
            return False

    def _unpad(self, s):
        return s[:-ord(s[len(s) - 1:])]


class InviteCls:
    # 千万别乱改这个地方
    invite_char = [
        'x', 'v', 'f', 'u', 'c', 'k', '1', '3', '5', '0', 'a', 'q', 'm', '9', 'n', 'e', 's', '4', '2',
        't', 'h', 'i', 'l', 'y', 'd', 'w', 'o', 'p', 'g', 'j', '6', '8', 'b', 'r'
    ]
    length = len(invite_char)
    invite_code_length = 6
    # max_id = length ** invite_code_length
    max_id = 15144936
    prime1 = 3
    slat = 58523
    prime2 = 11

    @classmethod
    def encode_invite_code(cls, user_id: int) -> str:
        if not isinstance(user_id, int):
            raise ValueError('用户id不是一个int')
        if user_id >= cls.max_id or user_id <= 0:
            raise ValueError(f'id范围:(0, {cls.max_id})')
        user_id = user_id * cls.prime1 + cls.slat
        b = [0] * cls.invite_code_length
        b[0] = user_id
        for i in range(5):
            b[i + 1] = b[i] // cls.length
            b[i] = (b[i] + b[0] * i) % cls.length
        b[5] = (b[0] + b[1] + b[3] + b[4]) * cls.prime1 % cls.length
        index_lst = [''] * cls.invite_code_length
        for i in range(6):
            idx = i * cls.prime2 % cls.invite_code_length
            index_lst[i] = cls.invite_char[b[idx]]
        return ''.join(index_lst)

    @classmethod
    def decode_invite_code(cls, invite_code: str) -> int:
        if len(invite_code) != cls.invite_code_length:
            raise ValueError('邀请码错误')

        res = 0
        feature_idx = [0] * cls.invite_code_length
        real_idx = [0] * cls.invite_code_length
        char_lst = [''] * cls.invite_code_length
        for i in range(cls.invite_code_length):
            feature_idx[(i * cls.prime2) % cls.invite_code_length] = i

        for i in range(cls.invite_code_length):
            char_lst[i] = invite_code[feature_idx[i]]

        for i in range(cls.invite_code_length):
            feature_idx[i] = cls.invite_char.index(char_lst[i])

        real_idx[5] = (feature_idx[0] + feature_idx[1] + feature_idx[3] + feature_idx[4]) * cls.prime1 % cls.length
        if real_idx[5] != feature_idx[5]:
            raise ValueError('邀请码错误')

        for i in range(4, -1, -1):
            real_idx[i] = (feature_idx[i] - feature_idx[0] * i + cls.length * i) % cls.length

        for i in range(4, 0, -1):
            res += real_idx[i]
            res *= cls.length

        res = ((res + real_idx[0]) - cls.slat) // cls.prime1
        return res


class WeChatOfficial:
    """
    公众号
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance:
            return cls._instance
        this_instance = super(WeChatOfficial, cls).__new__(cls, *args, **kwargs)
        cls._instance = this_instance
        return this_instance

    def __init__(self) -> None:
        self.expired_time = 3600

    def get_access_token(self):
        arg = {
            'grant_type': 'client_credential',
            'appid': settings.WECHAT_OFFICIAL_APPID,
            'secret': settings.WECHAT_OFFICIAL_APPSECRET
        }
        base_url = "https://api.weixin.qq.com/cgi-bin/token"
        access_token = conn.get('wx_access_token')
        if access_token:
            return access_token

        req_obj = requests.get(base_url, params=arg)
        access_token = json.loads(req_obj.content).get('access_token', None)
        if not access_token:
            raise ValueError(f"token获取失败:{json.loads(req_obj.content)}")
        else:
            conn.set('wx_access_token', access_token, self.expired_time)
        return access_token

    def get_ticket(self, uid):
        url = f"https://api.weixin.qq.com/cgi-bin/qrcode/create?access_token={self.get_access_token()}"
        header = {
            "Content-Type": "application/json"
        }
        arg = {
            "expire_seconds": 180,  # 3分钟超时
            "action_name": "QR_STR_SCENE",
            "action_info": {
                "scene": {
                    "scene_id": uid
                }
            }
        }
        req_content = json.loads(requests.post(url, json=arg, headers=header).content)
        ticket = req_content.get('ticket', None)
        return ticket, req_content

    def get_qr_url(self, uid=123):
        ticket, req_content = self.get_ticket(uid)
        if not ticket:
            if str(req_content.get('errcode')) == '40001':
                # 删掉token缓存再执行一次
                conn.delete('wx_access_token')
                ticket, req_content = self.get_ticket(uid)
                if not ticket:
                    raise ValueError(f'ticket获取失败:{req_content}')

        qr_url = f"https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket={ticket}"
        return qr_url

    def get_user_info(self, open_id):
        url = "https://api.weixin.qq.com/cgi-bin/user/info"
        arg = {
            'access_token': self.get_access_token(),
            'openid': open_id,
            'lang': "zh_CN"
        }
        req_content = json.loads(requests.get(url, arg).content)
        # union_id = req_content.get('unionid', None)
        # if not union_id:
        #     raise ValueError(f"unionid获取失败:{req_content}")
        return req_content


class HandleOfficialAccount:
    """
    公众号消息处理
    """

    @staticmethod
    def handle_msg(data: dict) -> str:
        # xml = trans_dict_to_xml()
        # return tostring(xml, encoding='unicode')
        pass

    @staticmethod
    def handle_event_subscribe(data: dict) -> None:
        open_id = data.get('FromUserName', None)
        user_info = WeChatOfficial().get_user_info(open_id)
        # union_id = user_info.get('unionid')
        # qs = Users.objects.filter(union_id=union_id)
        # if qs.exists():
        #     this_man = qs.first()
        #     this_man.user_extra.is_subscribed = True
        #     this_man.user_extra.save()
        logger.info(user_info)

    @staticmethod
    def handle_event_unsubscribe(data: dict):
        open_id = data.get('FromUserName', None)
        user_info = WeChatOfficial().get_user_info(open_id)
        # 取消订阅拿不到union id用open_id
        qs = Users.objects.filter(pub_openid=open_id)
        if qs.exists():
            this_man = qs.first()
            this_man.user_extra.is_subscribed = False
            this_man.user_extra.save()
        logger.info(user_info)
