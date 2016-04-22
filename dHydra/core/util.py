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
import os
import ntplib
from pandas import DataFrame
from pymongo import MongoClient
import re
import random

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

def get_client_ip():
	response = requests.get( 'https://ff.sinajs.cn/?_=%s&list=sys_clientip' % int(time.time()*1000) ).text
	ip = re.findall(r'\"(.*)\"', response)
	return ip[0]

# 用于将一个loop交给一个线程来完成一些任务
def thread_loop(loop, tasks):
	# loop = asyncio.new_event_loop()
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

# n个任务交给m个Thread完成
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

def string_to_date(date):
	return datetime.strptime(date, "%Y-%m-%d").date()

def timestamp_to_datetime(timestamp, timeFormat='ms'):
	if timeFormat == 'ms':
		timestamp = timestamp/1000
	return datetime.strftime(timestamp)

def time_now():
	return int(time.time()*1000)

# 从国家授时中心获取时间戳
def get_network_time():
	start = time.time()
	c = ntplib.NTPClient() 
	response = c.request('pool.ntp.org') 
	ts = response.tx_time 
	return ts

def check_time(precision = 0.1):
	duration = 2.0
	while duration > precision:
		try:
			print("{}, 开始获取网络时间戳".format( time.time() ))
			start = time.time()
			networkTime = get_network_time()
			end = time.time()
			duration = end-start
		except Exception as e:
			print("获取网络时间出了点小状况，正重试", duration)
	# print("网络耗时：{}".format( duration ) )
	# print("{}, 网络时间戳".format( networkTime ) )
	# print("{}, 现在时间戳".format( time.time()) )
	difference = networkTime - (start+duration)
	print("difference = {}, (本地时间戳+difference)=网络时间戳".format(difference))
	return difference

def split_symbols(symbols):
	df = DataFrame(symbols, columns = ['s'])
	sz = list(df[ df.s > 'sz' ]["s"])
	sh = list(df[ df.s < 'sz' ]["s"])
	return [ sz, sh ]

def upper(dataList):
	for i in range( 0, len(dataList) ):
		dataList[i] = dataList[i].upper()
	return dataList
