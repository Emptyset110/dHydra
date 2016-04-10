# -*- coding: utf8 -*-
"""
工具类
Created on 03/01/2016
@author: Wen Gu
@contact: emptyset110@gmail.com
"""
import dHydra.config.const as C
import requests
import threading
import asyncio
import math
import time
from datetime import datetime
import pandas

def _code_to_symbol(code):
    """
        生成symbol代码标志
        @author: Jimmy Liu
		@group : waditu
		@contact: jimmysoa@sina.cn
    """
    if code in C.INDEX_LABELS:
        return C.INDEX_LIST[code]
    else:
        if len(code) != 6 :
            return ''
        else:
            return 'sh%s'%code if code[:1] in ['5', '6', '9'] else 'sz%s'%code

def symbol_list_to_code(symbolList):
    codeList = []
    for symbol in symbolList:
        codeList.append(symbol[2:8])
    return codeList

def _get_public_ip():
	return requests.get('http://ipinfo.io/ip').text.strip()

# 用于将一个loop交给一个线程来完成一些任务
def thread_loop(loop, tasks):
    asyncio.set_event_loop(loop)
    loop.run_until_complete( asyncio.wait(tasks) )
    loop.close()

# 用于将一个list按一定步长切片，返回这个list切分后的list
def slice_list(step = None, num = None, dataList=None):
    if not ( (step is None) & (num is None) ):
        if num is not None:
            step = math.ceil(len(dataList)/num)
        return [dataList[ i : i + step] for i in range(0, len(dataList), step)]
    else:
        print("step和num不能同时为空")
        return False

# n个任务交给n个Thread完成
def threads_for_tasks(taskList):
    threads = []
    for task in taskList:
        t = threading.Thread(target = task.target, args = task.args)
        threads.append(t)
    for t in threads:
        t.start()
        print("开启线程：",t.name)
    for t in threads:
        t.join()

def symbols_to_string(symbols):
    if isinstance(symbols, list) or isinstance(symbols, set) or isinstance(symbols, tuple) or isinstance(symbols, pandas.Series):
        return ','.join(symbols)
    else:
        return symbols

def datetime_to_timestamp(dt, timeFormat = 'ms'):
    if timeFormat == 'ms':
        return int( time.mktime( dt.timetuple() )*1000 )
    elif timeFormat == 's':
        return int( time.mktime( dt.timetuple() ) )

def date_to_timestamp(date, dateFormat = '%Y-%m-%d', timeFormat = 'ms'):
    return datetime_to_timestamp( dt = datetime.strptime(date, dateFormat) , timeFormat = timeFormat)

def timestamp_to_datetime(timestamp, timeFormat='ms'):
    if timeFormat == 'ms':
        timestamp = timestamp/1000
    return datetime.strftime(timestamp)
def time_now():
    return int(time.time()*1000)
