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
    invite_code_length = 6
    max_id = length ** invite_code_length
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
