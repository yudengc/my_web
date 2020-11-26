# -*- coding: utf-8 -*-
"""
@Time    : 2020/5/6 7:53 下午
@Author  : LuckyTom
@File    : decorator.py
"""
import functools
import logging

import traceback

logger = logging.getLogger()


def try_decorator(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            result = method(self, *args, **kwargs)
        except Exception as e:
            logger.info("========================")
            logger.info(f"当前method：{method.__name__}")
            logger.info(f"错误信息：{traceback.format_exc()}")
            logger.info("========================")
            result = False
        return result
    return wrapper
