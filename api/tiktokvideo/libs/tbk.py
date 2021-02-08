# -*- coding: utf-8 -*-
"""
@Time    : 2020/5/22 3:39 下午
@Author  : LuckyTom
@File    : tbk.py
"""

import requests
import time
import hashlib

APP_KEY = '27678001'
APP_SECRET = '99402cdc622e6430ebfe3d17ec582298'
url = 'http://gw.api.taobao.com/router/rest'


class GetTBKCouponInfo(object):
    def __init__(self):
        pass

    def sign(self, secret, parameters):
        # =====================================
        # '''签名方法
        # @param secret: 签名需要的密钥
        # @param parameters: 支持字典和string两种
        # '''
        # =====================================
        # 如果parameters 是字典类的话
        if hasattr(parameters, "items"):
            keys = parameters.keys()
            keylist = sorted(keys)

            parameters = "%s%s%s" % (secret,
                                     str().join('%s%s' % (key, parameters[key]) for key in keylist),
                                     secret)
            sign = hashlib.md5(parameters.encode('utf-8')).hexdigest().upper()
            return sign

    def my_custom_api(self, **kwargs):
        """
        参数自己加
        https://open.taobao.com/api.htm?docId=285&docType=2
        """
        params = {
            'app_key': APP_KEY,
            'method': None,
            'sign_method': 'md5',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
            'v': '2.0',
            'format': 'json',
        }

        for key in kwargs:
            params[key] = kwargs[key]

        if not params['method']:
            print('写上method名字')
            return

        sign = self.sign(APP_SECRET, params)
        params['sign'] = sign
        response = requests.get(url, params)
        return response.json()
