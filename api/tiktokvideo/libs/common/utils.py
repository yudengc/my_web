# -*- coding: utf-8 -*-
"""
@Time    : 2020/10/26 2:28 下午
@Author  : LuckyTom
@File    : utils.py
"""

import random
import string
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta


def dict_to_xml(dict_data):
    """
    dict to xml
    :param dict_data:
    :return:
    """
    xml = ["<xml>"]
    for k, v in dict_data.items():
        xml.append("<{0}>{1}</{0}>".format(k, v))
    xml.append("</xml>")
    return "".join(xml)


def xml_to_dict(xml_data):
    """
    xml to dict
    :param xml_data:
    :return:
    """
    xml_dict = {}
    root = ET.fromstring(xml_data)
    for child in root:
        xml_dict[child.tag] = child.text
    return xml_dict


def get_out_trade_no():
    """
    获取订单号
    :return:
    """
    out_trade_no = datetime.now().__format__('%Y%m%d%H%M%S%f')
    return out_trade_no


def get_application_order():
    """
    获取申请订单号
    :return:
    """
    out_trade_no = datetime.now().__format__('%Y%m%d%H%M%S%f')
    return 'va' + out_trade_no


def get_nonce_str():
    """
    随机字符串
    :return:
    """
    data = "123456789zxcvbnmasdfghjklqwertyuiopZXCVBNMASDFGHJKLQWERTYUIOP"
    nonce_str = ''.join(random.sample(data, 30))
    return nonce_str


def get_ip(request):
    """获取外网ip"""
    if request.META.get('HTTP_X_FORWARDED_FOR'):
        ip = request.META.get("HTTP_X_FORWARDED_FOR")
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_code(n=6, alpha=False):
    """
    生成验证码
    :param n:
    :param alpha:
    :return:
    """
    s = ''  # 创建字符串变量,存储生成的验证码
    for i in range(n):  # 通过for循环控制验证码位数
        num = random.randint(0, 9)  # 生成随机数字0-9
        if alpha:  # 需要字母验证码,不用传参,如果不需要字母的,关键字alpha=False
            upper_alpha = chr(random.randint(65, 90))
            lower_alpha = chr(random.randint(97, 122))
            num = random.choice([num, upper_alpha, lower_alpha])
        s = s + str(num)
    return s


def get_iCode(n=4, alpha=False):
    # s = ''  # 创建字符串变量,存储生成的验证码
    s = random.choice(string.ascii_letters)
    for i in range(n):  # 通过for循环控制验证码位数
        num = random.randint(0, 9)  # 生成随机数字0-9
        if alpha:  # 需要字母验证码,不用传参,如果不需要字母的,关键字alpha=False
            upper_alpha = chr(random.randint(65, 90))
            lower_alpha = chr(random.randint(97, 122))
            num = random.choice([num, upper_alpha, lower_alpha])
        s = s + str(num)
    return s


def get_last_year_month():
    """获取上个月的年月"""
    today = datetime.today().date()
    first = today.replace(day=1)
    last_date = first - timedelta(days=1)
    return last_date.year, last_date.month


def get_first_and_now():
    """获取本月第一天和此刻时间"""
    now = datetime.now()
    return datetime(now.year, now.month, 1), now
