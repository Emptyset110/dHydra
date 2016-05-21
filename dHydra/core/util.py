# -*- coding: utf-8 -*-
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
		@modified: Wen Gu
	"""
	if code in C.INDEX_LIST.keys():
		return C.INDEX_LIST[code]
	else:
		if len(code) != 6 :
			return ''
		else:
			return 'sh%s'%code if code[:1] in ['5', '6', '9', '0' ] else 'sz%s'%code

def symbol_list_to_code(symbolList):
	codeList = []
	for symbol in symbolList:
		codeList.append(symbol[2:8])
	return codeList

def code_list_to_symbol(codeList):
	symbolList = []
	for code in codeList:
		symbolList.append( _code_to_symbol(code) )
	return symbolList

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

"""
与时间相关的转化函数
"""
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

"""
symbols相关函数
"""
def split_symbols(symbols):
	df = DataFrame(symbols, columns = ['s'])
	sz = list(df[ df.s > 'sz' ]["s"])
	sh = list(df[ df.s < 'sz' ]["s"])
	return [ sz, sh ]

def upper(dataList):
	for i in range( 0, len(dataList) ):
		dataList[i] = dataList[i].upper()
	return dataList

"""
用于解析Sina l2的函数
"""
def ws_parse( message, to_dict = False ):
	dataList = re.findall(r'(?:((?:2cn_)?((?:sh|sz)[\d]{6})(?:_0|_1|_orders|_i)?)(?:=)(.*)(?:\n))',message)
	result = list()
	for data in dataList:
		if (len(data[0])==12):	# quotation
			wstype = 'quotation'
		elif ( (data[0][-2:]=='_0') | (data[0][-2:]=='_1') ):
			wstype = 'deal'
		elif ( data[0][-6:]=='orders' ):
			wstype = 'orders'
		elif ( (data[0][-2:]=='_i') ):
			wstype = 'info'
		else:
			wstype = 'other'
		result = ws_parse_to_list( wstype=wstype,symbol=data[1],data=data[2],result=result, to_dict = to_dict )
	return result

def ws_parse_to_list( wstype, symbol, data, result ,to_dict ):
	data = data.split(',')
	if wstype is 'deal':
		for d in data:
			x = list()
			x.append(wstype)
			x.append(symbol)
			x.extend( d.split('|') )
			if to_dict is True:
				result.append( deal_to_dict( x ) )
			else:
				result.append(x)
	else:
		x = list()
		x.append(wstype)
		x.append(symbol)
		x.extend(data)
		if to_dict is True:
			if wstype is 'quotation':
				result.append( quotation_to_dict( x ) )
			elif wstype is 'info':
				result.append( info_to_dict( x ) )
			elif wstype is 'orders':
				result.append( orders_to_dict(x) )
		else:
			result.append(x)
	return result

def orders_to_dict( orders ):
	"""
	return
	------
	"""
	return orders

def quotation_to_dict( data ):
	"""
	整个转换大约耗时1*10^(-4)s, 其中datetime.strptime()占用较多耗时
	return
	------
	"""
	print("{}, length = {}".format( data, len(data) ))
	quotation = {
		"data_type" : 'quotation'
	,	"symbol": data[1] # "股票代码"
	,   "name": data[2] # "中文名"
	,   "time": datetime.strptime(data[3]+' '+data[4], "%H:%M:%S %Y-%m-%d") # "datetime格式的日期时间"
	,   "last_close": float( data[5] ) # "昨收"
	,   "open": float( data[5] ) # "今开"
	,   "high": float( data[7] ) #"最高价"
	,   "low": float( data[8] ) #"最低价"
	,   "now": float( data[9] ) #"现价"
	,   "status": data[10] #"状态, PH=盘后，PZ=盘中，TP=停牌, WX=午休, LT=临时停牌,KJ=开盘集合竞价,PZ=连续竞价"
	,   "deal_count": float( data[11] ) #"成交笔数"
	,   "total": int( data[12] ) #"成交总量"
	,   "amount": float( data[13] ) #"总成交金额"
	,   "current_ask": int( data[14] ) if data[14] else 0 # "当前委买总量"
	,   "average_ask": float( data[15] ) if data[15] else 0.0 # "加权平均委买价格"
	,   "current_bid": int( data[16] ) if data[16] else 0 # "当前委卖总量"
	,   "average_bid": float( data[17] ) if data[17] else 0.0 # "加权平均委卖价格"
	# ,   "cancel_ask_num" : int( data[18] ) # "买入撤单笔数" ?
	# ,   "cancel_ask_volumn" : int( data[19] ) #"买入撤单量"?
	# ,   "cancel_ask_amount" : float( data[20] ) #"买入撤单总金额"?
	# ,   "cancel_bid" : int( data[21] ) # "卖出撤单笔数" ?
	# ,   "cancel_bid_volumn" : int( data[22] ) # "卖出撤单量"?
	# ,   "cancel_bid_amount" : float( data[23] ) #"卖出撤单总金额"?
	,   "total_ask" : int( data[24] ) if data[24] else 0 # "委买总笔数"
	,   "total_bid" : int( data[25] ) if data[25] else 0 # "委卖总笔数"
	# ,   "ask" : data[26] #"买档位"
	# ,   "bid" : data[27] #"卖档位"
	,   "b1_price": float( data[28] ) if data[28] else 0.0 # 买1价
	,   "b2_price": float( data[29] ) if data[29] else 0.0 # 买2价
	,	"b3_price": float( data[30] ) if data[30] else 0.0 # 买3价
	,	"b4_price": float( data[31] ) if data[31] else 0.0# 买4价
	,	"b5_price": float( data[32] ) if data[32] else 0.0 # 买5价
	,	"b6_price": float( data[33] ) if data[33] else 0.0 # 买6价
	,	"b7_price": float( data[34] ) if data[34] else 0.0 # 买7价
	,	"b8_price": float( data[35] ) if data[35] else 0.0# 买8价
	,	"b9_price": float( data[36] ) if data[36] else 0.0 # 买9价
	,   "b10_price": float( data[37] ) if data[37] else 0.0 # 买10价
	,   "b1_volume": int( data[38] ) if data[38] else 0 # 买1量
	,   "b2_volume": int( data[39] ) if data[39] else 0 # 买2量
	,	"b3_volume": int( data[40] ) if data[40] else 0 # 买3量
	,	"b4_volume": int( data[41] ) if data[41] else 0 # 买4量
	,	"b5_volume": int( data[42] ) if data[42] else 0 # 买5量
	,	"b6_volume": int( data[43] ) if data[43] else 0 # 买6量
	,	"b7_volume": int( data[44] ) if data[44] else 0 # 买7量
	,	"b8_volume": int( data[45] ) if data[45] else 0 # 买8量
	,	"b9_volume": int( data[46] ) if data[46] else 0 # 买9量
	,   "b10_volume": int( data[47] ) if data[47] else 0 # 买10量
	,   "a1_price": float( data[48] ) if data[48] else 0.0 # 卖1价
	,   "a2_price": float( data[49] ) if data[49] else 0.0 # 卖2价
	,	"a3_price": float( data[50] ) if data[50] else 0.0 # 卖3价
	,	"a4_price": float( data[51] ) if data[51] else 0.0 # 卖4价
	,	"a5_price": float( data[52] ) if data[52] else 0.0 # 卖5价
	,	"a6_price": float( data[53] ) if data[53] else 0.0 # 卖6价
	,	"a7_price": float( data[54] ) if data[54] else 0.0 # 卖7价
	,	"a8_price": float( data[55] ) if data[55] else 0.0 # 卖8价
	,	"a9_price": float( data[56] ) if data[56] else 0.0 # 卖9价
	,   "a10_price": float( data[57] ) if data[57] else 0.0 # 卖10价
	,   "a1_volume": int( data[58] ) if data[58] else 0 #卖1量
	,   "a2_volume": int( data[59] ) if data[59] else 0 # 卖2量
	,	"a3_volume": int( data[60] ) if data[60] else 0 # 卖3量
	,	"a4_volume": int( data[61] ) if data[61] else 0 # 卖4量
	,	"a5_volume": int( data[62] ) if data[62] else 0 # 卖5量
	,	"a6_volume": int( data[63] ) if data[63] else 0 # 卖6量
	,	"a7_volume": int( data[64] ) if data[64] else 0 # 卖7量
	,	"a8_volume": int( data[65] ) if data[65] else 0 # 卖8量
	,	"a9_volume": int( data[66] ) if data[66] else 0 # 卖9量
	,   "a10_volume": int( data[67] ) if data[67] else 0 #卖10量
	}
	return quotation

def deal_to_dict( data ):
	deal = {
			"data_type" : 'deal'
		,   "symbol" : data[1]   # 股票代码
		,   "index"  : deal[2]     #成交序号
		,   "time" : deal[3]    # 时间，字符串格式，不带日期
		,   "price" :  float( deal[4] )  # 成交价格
		,   "volume" : int( deal[5] )  # 成交量
		,   "amount" : float( deal[6] ) # 成交金额
		,   "buynum": int( deal[7] ) # 买单委托序号
		,   "sellnum": int( deal[8] ) # 卖单委托序号
		,   "iotype": int( deal[9] ) #主动性买卖标识
		,   "channel" : int( deal[10] ) #成交通道（这是交易所的一个标记，没有作用）
	}
	return deal


def symbol_type( symbol ):
	"""
	description: 用于判断股票代码类型：母基金，分级基金，指数，AB股
	return
	------
	"""
	return symbol_type
