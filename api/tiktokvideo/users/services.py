# -*- coding: utf-8 -*-
"""
@Time    : 2020/10/26 10:49 上午
@Author  : LuckyTom
@File    : services.py
"""
import base64
import json

import requests
from Crypto.Cipher import AES


class WeChatApi:

    def __init__(self, appid, secret):
        self.app_id = appid
        self.secret = secret

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
        session_key = r.json().get('session_key', '')
        return openid, session_key


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
        return s[:-ord(s[len(s)-1:])]


class InviteCls:
    # 千万别乱改这个地方
    invite_char = [
        'x', 'v', 'f', 'u', 'c', 'k', '1', '3', '5', '0', 'a', 'q', 'm', '9', 'n', 'e', 's', '4', '2',
        't', 'h', 'i', 'l', 'y', 'R', 'd', 'Q', 'F', 'w', 'o', 'p', 'g', 'j', 'A', '6', 'S', 'M', 'K'
    ]
    fill_char = '8'
    length = len(invite_char)
    invite_code_length = 4
    max_id = length ** invite_code_length

    @classmethod
    def encode_invite_code(cls, user_id: int):
        if not isinstance(user_id, int):
            raise ValueError('用户id不是一个int')
        if user_id >= cls.max_id or user_id <= 0:
            raise ValueError(f'id范围:(0, {cls.max_id})')
        this_int = user_id
        invite_code = []
        while this_int / cls.length > 0:
            mod = this_int % cls.length
            this_int = this_int // cls.length
            invite_code.insert(0, cls.invite_char[mod])
        invite_code = ''.join(invite_code)
        now_len = len(invite_code)
        sub_len = cls.invite_code_length - now_len
        if sub_len > 0:
            invite_code = cls.fill_char * sub_len + invite_code
        return invite_code

    @classmethod
    def decode_invite_code(cls, invite_code: str):
        if not isinstance(invite_code, str):
            raise ValueError('邀请码要是字符串')
        if len(invite_code) != cls.invite_code_length:
            raise ValueError(f'邀请码长度不对: 要{cls.invite_code_length}位')
        invite_code = invite_code.replace(cls.fill_char, '')
        user_id = 0
        i = 0
        for c in invite_code[::-1]:
            if c not in cls.invite_char:
                raise ValueError('无法解码, 请确认邀请码正确')
            user_id += cls.invite_char.index(c) * cls.length ** i
            i += 1
        return user_id
