# -*- coding: utf-8 -*-
"""
工具类
Created on 03/01/2016
@author: Wen Gu
@contact: emptyset110@gmail.com
"""
import requests
import asyncio
import math
import time
from datetime import datetime
import pandas
import os
import ntplib
from pandas import DataFrame
import re
import json
import logging


def camel_to_underscore(name):
    pass


def get_logger(
    logger_name="main",
    log_path="log",                     #
    console_log=True,                   # 屏幕打印日志开关，默认True
    console_log_level=logging.INFO,     # 屏幕打印日志的级别，默认为INFO
    critical_log=False,                 # critical单独写文件日志，默认关闭
    error_log=True,                     # error级别单独写文件日志，默认开启
    warning_log=False,                  # warning级别单独写日志，默认关闭
    info_log=True,                      # info级别单独写日志，默认开启
    debug_log=False,                    # debug级别日志，默认关闭
):
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    if log_path:
        # 补全文件夹
        if log_path[-1] != '/':
            log_path += '/'

    if not logger.handlers:
        # 屏幕日志打印设置
        if console_log:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.INFO)
            logger.addHandler(console_handler)

        if not os.path.exists(log_path + logger_name):
            os.makedirs(log_path + logger_name)
        # 打开下面的输出到文件
        if critical_log:
            log_handler = logging.FileHandler(
                log_path + logger_name + '/critical.log'
            )
            log_handler.setLevel(logging.CRITICAL)
            log_handler.setFormatter(formatter)
            logger.addHandler(log_handler)
        if error_log:
            log_handler = logging.FileHandler(
                log_path + logger_name + '/error.log'
            )
            log_handler.setLevel(logging.ERROR)
            log_handler.setFormatter(formatter)
            logger.addHandler(log_handler)
        if warning_log:
            log_handler = logging.FileHandler(
                log_path + logger_name + '/warning.log'
            )
            log_handler.setLevel(logging.WARNING)
            log_handler.setFormatter(formatter)
            logger.addHandler(log_handler)
        if info_log:
            log_handler = logging.FileHandler(
                log_path + logger_name + '/info.log'
            )
            log_handler.setLevel(logging.INFO)
            log_handler.setFormatter(formatter)
            logger.addHandler(log_handler)
        if debug_log:
            log_handler = logging.FileHandler(
                log_path + logger_name + '/debug.log'
            )
            log_handler.setLevel(logging.DEBUG)
            log_handler.setFormatter(formatter)
            logger.addHandler(log_handler)
    return logger


def generate_token():
    import hashlib
    token = hashlib.sha1()
    token.update(str(time.time()).encode())
    token = token.hexdigest()
    return token


def symbol_list_to_code(symbolList):
    codeList = []
    for symbol in symbolList:
        codeList.append(symbol[2:8])
    return codeList


def _get_public_ip():
    return requests.get('http://ipinfo.io/ip').text.strip()


def get_client_ip():
    while True:
        try:
            response = requests.get(
                'https://ff.sinajs.cn/?_=%s&list=sys_clientip'
                % int(time.time() * 1000)).text
            ip = re.findall(r'\"(.*)\"', response)
            break
        except Exception as e:
            try:
                ip = _get_public_ip()
                return ip
            except:
                pass
    return ip[0]

def slice_list(step=None, num=None, data_list=None):
    """
    用于将一个list按一定步长切片，返回这个list切分后的list
    :param step:
    :param num:
    :param data_list:
    :return:
    """
    if not ((step is None) & (num is None)):
        if num is not None:
            step = math.ceil(len(data_list) / num)
        return [data_list[i: i + step] for i in range(0, len(data_list), step)]
    else:
        print("step和num不能同时为空")
        return False


def symbols_to_string(symbols):
    if (
        isinstance(symbols, list) or
        isinstance(symbols, set) or
        isinstance(symbols, tuple) or
        isinstance(symbols, pandas.Series)
    ):
        return ','.join(symbols)
    else:
        return symbols

"""
与时间相关的转化函数
"""


def datetime_to_timestamp(dt, timeFormat='ms'):
    if timeFormat == 'ms':
        return int(time.mktime(dt.timetuple()) * 1000)
    elif timeFormat == 's':
        return int(time.mktime(dt.timetuple()))


def date_to_timestamp(date, dateFormat='%Y-%m-%d', timeFormat='ms'):
    return datetime_to_timestamp(
        dt=datetime.strptime(date, dateFormat),
        timeFormat=timeFormat,
    )


def string_to_date(date):
    return datetime.strptime(date, "%Y-%m-%d").date()


def timestamp_to_datetime(timestamp, timeFormat='ms'):
    if timeFormat == 'ms':
        timestamp = timestamp / 1000
    return datetime.strftime(timestamp)


def time_now():
    return int(time.time() * 1000)

# 从国家授时中心获取时间戳


def get_network_time():
    start = time.time()
    c = ntplib.NTPClient()
    response = c.request('pool.ntp.org')
    ts = response.tx_time
    return ts


def check_time(precision=0.1):
    duration = 2.0
    while duration > precision:
        try:
            print("{}, 开始获取网络时间戳".format(time.time()))
            start = time.time()
            networkTime = get_network_time()
            end = time.time()
            duration = end - start
        except Exception as e:
            print("获取网络时间出了点小状况，正重试", duration)
    # print("网络耗时：{}".format( duration ) )
    # print("{}, 网络时间戳".format( networkTime ) )
    # print("{}, 现在时间戳".format( time.time()) )
    difference = networkTime - (start + duration)
    print("difference = {}, (本地时间戳+difference)=网络时间戳".format(difference))
    return difference

"""
symbols相关函数
"""


def split_symbols(symbols):
    df = DataFrame(symbols, columns=['s'])
    sz = list(df[df.s > 'sz']["s"])
    sh = list(df[df.s < 'sz']["s"])
    return [sz, sh]


def upper(data_list):
    for i in range(0, len(data_list)):
        data_list[i] = data_list[i].upper()
    return data_list


def read_config(file_path):
    # 读取配置
    try:
        f_config = open(file_path)
        cfg = json.load(f_config)
    except Exception as e:
        print("{}".format(e))
        cfg = dict()
        print(
            "未能正确加载{}，请检查路径，json文档格式，或者忽略此警告"
            .format(file_path)
        )
    return cfg


def write_config(cfg, file_path):
    # 将配置写入
    print("写入配置：\n{}".format(json.dumps(cfg, indent=2)))
    f = open(file_path, 'w', encoding='UTF-8')
    f.write(json.dumps(cfg, indent=2))
    f.close()
