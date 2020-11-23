# -*- coding: utf-8 -*-
"""
@Time    : 2020/10/26 2:27 下午
@Author  : LuckyTom
@File    : pay.py
"""

import abc
import hashlib
import time
import requests
import logging

from libs.common import utils
from tiktokvideo.base import APP_ID, MCH_ID, MCH_KEY, PAY_NOTIFY_URL

logger = logging.getLogger()


class Payment(metaclass=abc.ABCMeta):
    """支付主类"""

    def __init__(self):
        # 微信支付url
        self.url = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
        # 微信退款url
        self.refund_url = 'https://api.mch.weixin.qq.com/secapi/pay/refund'

    @abc.abstractmethod
    def pay(self, *args, **kwargs):
        pass


class WeChatPay(Payment):
    """微信支付"""

    def __init__(self):
        super(WeChatPay, self).__init__()

    def pay(self, money, client_ip, order_number, openid, attach=''):
        """
        统一下单
        :param money: 金额
        :param client_ip: ip地址
        :param order_number: 订单号
        :param openid: 用户openid
        :param attach: 自定义参数
        :return:
        """
        # 拿到封装好的xml数据
        sign_obj = GenerateSign()
        body_data = sign_obj.get_body_data(spbill_create_ip=client_ip, out_trade_no=order_number, total_fee=money,
                                           openid=openid, attach=attach)
        # 获取时间戳
        timestamp = str(int(time.time()))
        # 请求微信接口下单
        response = requests.post(self.url, body_data.encode("utf-8"),
                                 headers={'Content-Type': 'text/xml;charset=utf-8'})
        # 返回数据为xml,将其转为字典
        content = utils.xml_to_dict(response.content)
        print(content)
        logger.info(f'微信支付接口返回数据{content}')
        if content["return_code"] == 'SUCCESS':
            # 获取预支付交易会话标识
            prepay_id = content.get("prepay_id")
            # 获取随机字符串
            nonce_str = content.get("nonce_str")
            # 获取paySign签名，这个需要我们根据拿到的prepay_id和nonceStr进行计算签名
            sign = sign_obj.pay_sign_again(prepay_id, timestamp, nonce_str)
            # 封装返回给前端的数据
            data = {
                "order_number": order_number,
                "prepay_id": prepay_id,
                "nonceStr": nonce_str,
                "paySign": sign,
                "timeStamp": timestamp
            }
            return data
        return False

    def refund(self, out_trade_no, out_refund_no, total_fee, refund_fee):
        """
        申请退款
        :param out_trade_no: 商户订单号
        :param out_refund_no: 商户退款单号
        :param total_fee: 订单金额
        :param refund_fee: 退款金额
        :return:
        """
        # 拿到封装好的xml数据
        sign_obj = GenerateSign()
        body_data = sign_obj.get_body_data(
            out_trade_no=out_trade_no, out_refund_no=out_refund_no, total_fee=total_fee, refund_fee=refund_fee
        )
        response = requests.post(self.refund_url, body_data.encode("utf-8"),
                                 headers={'Content-Type': 'text/xml;charset=utf-8'})

        # 返回数据为xml,将其转为字典
        content = utils.xml_to_dict(response.content)
        if content["return_code"] == 'SUCCESS':
            print('退款成功')
            return True
        print(f"退款失败, 失败原因：{content['return_msg']}")
        return False


class GenerateSign:
    def __init__(self):
        self.app_id = APP_ID
        self.mch_id = MCH_ID
        self.mch_key = MCH_KEY

    def pay_sign(self, params):
        """生成签名"""
        return self.encryption(params)

    def pay_sign_again(self, prepay_id, timestamp, nonce_str):
        """根据得到的预支付订单ID再次签名"""
        pay_data = {
            'appId': self.app_id,
            'nonceStr': nonce_str,
            'package': "prepay_id=" + prepay_id,
            'signType': 'MD5',
            'timeStamp': timestamp
        }
        return self.encryption(pay_data)

    def encryption(self, params):
        # 处理函数，对参数按照key=value的格式，并按照参数名ASCII字典序排序
        str_a = '&'.join(["{0}={1}".format(k, params.get(k)) for k in sorted(params)])
        str_sign_temp = '{0}&key={1}'.format(str_a, self.mch_key)
        sign = hashlib.md5(str_sign_temp.encode("utf-8")).hexdigest()
        return sign.upper()

    def get_body_data(self, **kwargs):
        nonce_str = utils.get_nonce_str()  # 随机字符串
        out_refund_no = kwargs.get('out_refund_no')  # 退款单号
        params = {
            "appid": self.app_id,
            "mch_id": self.mch_id,
            "nonce_str": nonce_str,
        }
        # 是否退款接口
        if out_refund_no:
            # 退款
            extra_dict = {
                "refund_desc": '自愿退款',
                "notify_url": REFUND_NOTIFY_URL
            }
        else:
            extra_dict = {
                "body": '松鼠短视频-购买套餐',
                "notify_url": PAY_NOTIFY_URL,
                "trade_type": 'JSAPI',
                "attach": kwargs.get('attach'),
            }
        dict_data = {**kwargs, **params, **extra_dict}
        sign = self.pay_sign(dict_data)
        dict_data['sign'] = sign
        return utils.dict_to_xml(dict_data)
