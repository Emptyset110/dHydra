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
import re
import json
import logging

def get_logger(
    logger_name="main",
    log_path="log",                     #
    console_log=True,                   # 屏幕打印日志开关，默认True
    console_log_level=logging.INFO,     # 屏幕打印日志的级别，默认为INFO
    critical_log=False,                 # critica单独l写文件日志，默认关闭
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
用于解析Sina l2的函数
"""


def get_trading_date():
    from dHydra.core.Functions import get_vendor
    sina = get_vendor("Sina")
    sh000300 = sina.get_quote(symbols=["sh000300"])
    sh000300_date = sh000300.iloc[0].date

    return sh000300_date


def ws_parse(message, trading_date, to_dict=False):
    """
    trading_date 最好外部传入
    :param message:
    :param trading_date: e.g."2016-12-30"
    :param to_dict:
    :return:
    """
    data_list = re.findall(
        r'(?:((?:2cn_)?((?:sh|sz)[\d]{6})'
        r'(?:_0|_1|_orders|_i)?)(?:=)(.*)(?:\n))',
        message,
    )
    result = list()
    for data in data_list:
        if len(data[0]) == 12:  # quotation
            wstype = 'quotation'
        elif (data[0][-2:] == '_0') | (data[0][-2:] == '_1'):
            wstype = 'transaction'
        elif data[0][-6:] == 'orders':
            wstype = 'orders'
        elif data[0][-2:] == '_i':
            wstype = 'info'
        else:
            wstype = 'other'
        result = ws_parse_to_list(
            wstype=wstype,
            symbol=data[1],
            data=data[2],
            trading_date=trading_date,
            result=result,
            to_dict=to_dict
        )
    return result


def ws_parse_to_list(wstype, symbol, data, trading_date, result, to_dict):
    data = data.split(',')
    if wstype is 'transaction':
        for d in data:
            x = list()
            x.append(wstype)
            x.append(symbol)
            x.extend(d.split('|'))
            if to_dict is True:
                t = transaction_to_dict(x, trading_date)
                if t is not None:
                    result.append(t)
            else:
                result.append(x)
    else:
        x = list()
        x.append(wstype)
        x.append(symbol)
        x.extend(data)
        if to_dict is True:
            if wstype is 'quotation':
                result.append(quotation_to_dict(x))
            # elif wstype is 'info':
            #     result.append(info_to_dict(x))
            elif wstype is 'orders':
                result.append(orders_to_dict(x, trading_date))
        else:
            result.append(x)
    return result


def orders_to_dict(data, trading_date):
    """
    return
    ------
    """
    try:
        orders = {
            "data_type": "orders",
            "symbol": data[1],
            "time": datetime(
                int(trading_date[0:4]),
                int(trading_date[5:7]),
                int(trading_date[8:10]),
                int(data[3][0:2]),
                int(data[3][3:5]),
                int(data[3][6:8])
            ),  # 时间 datetime格式
            "bid_price": float(data[4]),
            "bid_volume": int(data[5]),
            "bid_num": int(data[6]),
            "ask_price": float(data[7]),
            "ask_volume": int(data[8]),
            "ask_num": int(data[9]),
            "bid_orders": data[10].split("|"),
            "ask_orders": data[12].split("|")
        }
    except ValueError:
        return {}
    return orders


def quotation_to_dict(data):
    """
    整个转换大约耗时1*10^(-4)s, 其中datetime.strptime()占用较多耗时
        根据Issue #5，"time"不再用strptime来转化
    return
    ------
    """
    # print("{}, length = {}".format( data, len(data) ))
    quotation = {}
    if len(data) == 68:
        quotation = {
            "data_type": 'quotation',
            "symbol": data[1],  # "股票代码"
            "name": data[2],  # "中文名"
            # "datetime格式的日期时间"
            "time": datetime(
                int(data[4][0:4]),
                int(data[4][5:7]),
                int(data[4][8:10]),
                int(data[3][0:2]),
                int(data[3][3:5]),
                int(data[3][6:8])
            ),
            # "昨收"
            "last_close": float(data[5]),
            # "今开"
            "open": float(data[6]),
            # "最高价"
            "high": float(data[7]),
            # "最低价"
            "low": float(data[8]),
            # "现价"
            "now": float(data[9]),
            # 状态：
            # PH=盘后，PZ=盘中，TP=停牌,
            # WX=午休, LT=临时停牌,KJ=开盘集合竞价,PZ=连续竞价
            "status": data[10],
            "transaction_count": float(data[11]),  # "成交笔数"
            "total_volume": int(data[12]),  # "成交总量"
            "total_amount": float(data[13]),  # "总成交金额"
            # "当前委买总金额"
            "current_bid_amount": int(data[14]) if data[14] else 0,
            # "加权平均委买价格"
            "average_bid_price": float(data[15]) if data[15] else 0.0,
            # "当前委卖总金额"
            "current_ask_amount": int(data[16]) if data[16] else 0,
            # "加权平均委卖价格"
            "average_ask_price": float(data[17]) if data[17] else 0.0,
            "cancel_bid_num": int(data[18]),    # "买入撤单笔数"
            "cancel_bid_amount": int(data[19]),  # "买入撤单金额"
            "unknown_bid": float(data[20]),   # 不知道是什么
            "cancel_ask": int(data[21]),    # "卖出撤单笔数"
            "cancel_ask_amount": int(data[22]),  # "卖出撤金额"
            "unknown_ask": float(data[23]),  # 不知道是什么
            "total_bid": int(data[24]) if data[24] else 0,  # "委买总笔数"
            "total_ask": int(data[25]) if data[25] else 0,  # "委卖总笔数"
            # "bid": data[26],  # "买档位"肯定是10，不记录
            # "ask": data[27],  # "卖档位"肯定是10，不记录
            "b1_price": float(data[28]) if data[28] else 0.0,  # 买1价
            "b2_price": float(data[29]) if data[29] else 0.0,  # 买2价
            "b3_price": float(data[30]) if data[30] else 0.0,  # 买3价
            "b4_price": float(data[31]) if data[31] else 0.0,  # 买4价
            "b5_price": float(data[32]) if data[32] else 0.0,  # 买5价
            "b6_price": float(data[33]) if data[33] else 0.0,  # 买6价
            "b7_price": float(data[34]) if data[34] else 0.0,  # 买7价
            "b8_price": float(data[35]) if data[35] else 0.0,  # 买8价
            "b9_price": float(data[36]) if data[36] else 0.0,  # 买9价
            "b10_price": float(data[37]) if data[37] else 0.0,  # 买10价
            "b1_volume": int(data[38]) if data[38] else 0,  # 买1量
            "b2_volume": int(data[39]) if data[39] else 0,  # 买2量
            "b3_volume": int(data[40]) if data[40] else 0,  # 买3量
            "b4_volume": int(data[41]) if data[41] else 0,  # 买4量
            "b5_volume": int(data[42]) if data[42] else 0,  # 买5量
            "b6_volume": int(data[43]) if data[43] else 0,  # 买6量
            "b7_volume": int(data[44]) if data[44] else 0,  # 买7量
            "b8_volume": int(data[45]) if data[45] else 0,  # 买8量
            "b9_volume": int(data[46]) if data[46] else 0,  # 买9量
            "b10_volume": int(data[47]) if data[47] else 0,  # 买10量
            "a1_price": float(data[48]) if data[48] else 0.0,  # 卖1价
            "a2_price": float(data[49]) if data[49] else 0.0,  # 卖2价
            "a3_price": float(data[50]) if data[50] else 0.0,  # 卖3价
            "a4_price": float(data[51]) if data[51] else 0.0,  # 卖4价
            "a5_price": float(data[52]) if data[52] else 0.0,  # 卖5价
            "a6_price": float(data[53]) if data[53] else 0.0,  # 卖6价
            "a7_price": float(data[54]) if data[54] else 0.0,  # 卖7价
            "a8_price": float(data[55]) if data[55] else 0.0,  # 卖8价
            "a9_price": float(data[56]) if data[56] else 0.0,  # 卖9价
            "a10_price": float(data[57]) if data[57] else 0.0,  # 卖10价
            "a1_volume": int(data[58]) if data[58] else 0,  # 卖1量
            "a2_volume": int(data[59]) if data[59] else 0,  # 卖2量
            "a3_volume": int(data[60]) if data[60] else 0,  # 卖3量
            "a4_volume": int(data[61]) if data[61] else 0,  # 卖4量
            "a5_volume": int(data[62]) if data[62] else 0,  # 卖5量
            "a6_volume": int(data[63]) if data[63] else 0,  # 卖6量
            "a7_volume": int(data[64]) if data[64] else 0,  # 卖7量
            "a8_volume": int(data[65]) if data[65] else 0,  # 卖8量
            "a9_volume": int(data[66]) if data[66] else 0,  # 卖9量
            "a10_volume": int(data[67]) if data[67] else 0,  # 卖10量
        }
    elif len(data) == 67:
        quotation = {
            "data_type": 'quotation',
            "symbol": data[1],  # "股票代码"
            "name": data[2],  # "中文名"
            # "datetime格式的日期时间"
            "time": datetime(
                int(data[4][0:4]),
                int(data[4][5:7]),
                int(data[4][8:10]),
                int(data[3][0:2]),
                int(data[3][3:5]),
                int(data[3][6:8])
            ),
            "last_close": float(data[5]),  # "昨收"
            "open": float(data[6]),  # "今开"
            "high": float(data[7]),  # "最高价"
            "low": float(data[8]),  # "最低价"
            "now": float(data[9]),  # "现价"
            # "状态,
            # PH=盘后，PZ=盘中，TP=停牌, WX=午休,
            # LT=临时停牌,KJ=开盘集合竞价,PZ=连续竞价"
            "status": data[10],
            "transaction_count": float(data[11]),  # "成交笔数"
            "total": int(data[12]),  # "成交总量"
            "amount": float(data[13]),  # "总成交金额"
        }
    return quotation


def transaction_to_dict(data, trading_date):
    if len(data) == 11:
        transaction = {
            "data_type": 'transaction',
            "symbol": data[1],   # 股票代码
            "index": data[2],  # 成交序号
            "time": datetime(
                int(trading_date[0:4]),
                int(trading_date[5:7]),
                int(trading_date[8:10]),
                int(data[3][0:2]),
                int(data[3][3:5]),
                int(data[3][6:8]),
                int(data[3][9:])*1000
            ),  # 时间 datetime格式
            # "time": data[3],   # 时间，字符串格式，不带日期
            "price":  float(data[4]),  # 成交价格
            "volume": int(data[5]),  # 成交量
            "amount": float(data[6]),  # 成交金额
            "buynum": int(data[7]),  # 买单委托序号
            "sellnum": int(data[8]),  # 卖单委托序号
            "iotype": int(data[9]),  # 主动性买卖标识
            "channel": int(data[10]),  # 成交通道（这是交易所的一个标记，没有作用）
        }
        return transaction
    else:
        return None


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
