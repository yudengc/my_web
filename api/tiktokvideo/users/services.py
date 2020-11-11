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
            print(self.sessionKey)
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

