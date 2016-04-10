# -*- coding: utf8 -*-
"""
雪球社区接口类 
Created on 03/17/2016
@author: Wen Gu
@contact: emptyset110@gmail.com
"""
# 以下是自动生成的 #
# --- 导入系统配置
import dHydra.core.util as util
from dHydra.core.Vendor import Vendor
from dHydra.config import connection as CON
from dHydra.config import const as C
# --- 导入自定义配置
from .connection import *
from .const import *
from .config import *
# 以上是自动生成的 #

import requests
import asyncio
from pandas import DataFrame
import functools
import threading

class XueqiuVendor(Vendor):

	def __init__(self):
		self.session = requests.Session()
		# 先爬取一遍雪球页面，获取cookies
		xq = self.session.get(
			"https://xueqiu.com/hq"
		,	headers = HEADERS_XUEQIU
		)

	"""
	stockTypeList 	: list
		['sha','shb','sza','szb']分别代表沪A，沪B，深A，深B。如果为空则代表获取所有沪深AB股
		e.g: stockTypeList = ['sha','shb']即获取所有沪A沪B
	columns 		:	string
		默认为："symbol,name,current,chg,percent,last_close,open,high,low,volume,amount,market_capital,pe_ttm,high52w,low52w,hasexist"
	"""
	def get_stocks(	self
				,	stockTypeList	=	['sha','shb','sza','szb']
				,	columns 		=	CONST_XUEQIU_QUOTE_ORDER_COLUMN
		):
		for stockType in stockTypeList:
			print( "正在从雪球获取：{}".format( EX_NAME[stockType] ) )
			page = 1
			while True:
				response = self.session.get(
					URL_XUEQIU_QUOTE_ORDER(page,columns,stockType)
				,	headers = HEADERS_XUEQIU
				).json()
				df = DataFrame.from_records(response["data"], columns=response["column"])
				if 'stocks' not in locals().keys():
					stocks = df
				else:
					stocks = stocks.append(df)
				if df.size==0:
					break
				page += 1
		return stocks

	"""
	返回：set
	"""
	def get_symbols(	self
					,	stockTypeList = ['sha','shb','sza','szb']
		):
		symbols = self.get_stocks(stockTypeList = stockTypeList, columns = 'symbol')
		return set(symbols.symbol)

	"""
	获取雪球行情/基本面的接口
	"""
	def get_quotation(self, symbol=None, symbolSet=None, dataframe = True, threadNum = 3):
		if 'quotation' in self.__dict__.keys():
			del(self.quotation)
			# Cut symbolList
		symbolList = list(symbolSet)
		threads = []
		symbolListSlice = util.slice_list(num = threadNum,dataList = symbolList)
		for symbolList in symbolListSlice:
			loop = asyncio.new_event_loop()
			symbolsList = util.slice_list(step=50, dataList = symbolList)
			tasks = [self.get_quotation_task(symbols=symbols) for symbols in symbolsList]
			t = threading.Thread(target = util.thread_loop,args=(loop,tasks) )
			threads.append(t)
		for t in threads:
			t.start()
		for t in threads:
			t.join()

		if dataframe:
			self.quotation = DataFrame.from_records( self.quotation ).T
		return(self.quotation)


	@asyncio.coroutine
	def get_quotation_task(self, symbols):
		symbols = util.symbols_to_string(symbols)
		quotation = yield from self.fetch_quotation_coroutine(symbols = symbols)
		if 'quotation' not in self.__dict__.keys():
			self.quotation = quotation
		else:
			self.quotation.update( quotation )

	"""
	雪球单股基本面数据获取coroutine
	"""
	@asyncio.coroutine
	def fetch_quotation_coroutine(self, symbols=None):
		loop = asyncio.get_event_loop()
		if symbols is not None:
			async_req = loop.run_in_executor(None, functools.partial( self.session.get
			,	URL_XUEQIU_QUOTE(symbols)
			,	headers = HEADERS_XUEQIU
			) )
			try:
				quotation = yield from async_req
			except Exception as e:
				print(e)
				async_req = loop.run_in_executor(None, functools.partial( self.session.get
				,	URL_XUEQIU_QUOTE(symbols)
				,	headers = HEADERS_XUEQIU
				) )
				quotation = yield from async_req
			quotation = quotation.json()
		return(quotation)

	# """
	# 雪球单股基本面数据获取
	# 默认返回值格式是dict，若参数dataframe为True则返回dataframe
	# """
	# def fetch_quotation(self, symbols = None, dataframe = False):
	# 	symbols = util.symbols_to_string(symbols)
	# 	if symbols is not None:
	# 		quotation = self.session.get(
	# 			URL_XUEQIU_QUOTE(symbols)
	# 		,	headers = HEADERS_XUEQIU
	# 		).json()
	# 	if dataframe:
	# 		quotation = DataFrame.from_records( quotation ).T
	# 	return(quotation)

	"""
	雪球历史k线接口，包括前/后复权(默认不复权)
		period: 1day,1week,1month
	"""
	def get_kline(self, symbol, period = '1day', fqType = 'normal', begin = None, end = None, dataframe = True):
		if end is None:
			end = util.time_now()
		if isinstance(begin, str):
			begin = util.date_to_timestamp( begin )
		if isinstance(end, str):
			end = util.date_to_timestamp( end )
		kline = self.session.get(
				URL_XUEQIU_KLINE( symbol = symbol, period = period, fqType = fqType, begin = begin, end = end )
			,	headers = HEADERS_XUEQIU
			).json()
		if kline["success"]=='true':
			if dataframe:
				return DataFrame.from_records( kline["chartlist"] ).set_index("time")
			else:
				return kline["chartlist"]
		else:
			return False


	"""
	period  = '1d'  	只显示当日分钟线
			= '5d'		5分钟线，250行（最多5个交易日）
			= 'all'		历史周线
	"""
	def get_today(self, symbol, period = '1day', dataframe = True):
		quotation = self.session.get(
				URL_XUEQIU_CHART( symbol = symbol, period = period)
			,	headers = HEADERS_XUEQIU
			).json()
		if quotation["success"] == "true":
			if dataframe:
				return DataFrame.from_records( quotation["chartlist"] ).set_index("time")
			else:
				return quotation["chartlist"]
		else:
			return False

	# def get_realtime_quote_sync(self, symbols, dataframe = True):
	# 	print("正在从雪球获取股票行情(同步方式)...")
	# 	symbolListSlice = util.slice_list( step = 50, dataList = list(symbols) )
	# 	for symbolList in symbolListSlice:
	# 		if 'quote' in locals().keys():
	# 			if dataframe:
	# 				quote = quote.append( self.get_realtime_quote(symbols = symbolList, dataframe = dataframe) )
	# 			else:
	# 				quote.update( self.get_realtime_quote(symbols = symbolList, dataframe = dataframe) )
	# 		else:
	# 			quote = self.get_realtime_quote(symbols = symbolList, dataframe = dataframe)
	# 	return quote

	# def get_realtime_quote_async(self, symbols, dataframe = True):
	# 	if 'quote' in self.__dict__.keys():
	# 		del(self.quote)
	# 	print("正在从雪球获取股票行情(异步方式)...")
	# 	symbolListSlice = util.slice_list( step = 50, dataList = list(symbols) )
	# 	loop = asyncio.new_event_loop()
	# 	asyncio.set_event_loop(loop)
	# 	tasks = list()
	# 	for symbolList in symbolListSlice:
	# 		symbols = util.symbols_to_string( symbolList )
	# 		tasks.append( self.get_realtime_quote_coroutine(symbols, loop) )
	# 	loop.run_until_complete( asyncio.wait(tasks) )

	# 	if dataframe:
	# 		return DataFrame.from_records( self.quote ).T
	# 	return self.quote

	# @asyncio.coroutine
	# def get_realtime_quote_coroutine(self, symbols, loop):
	# 	async_req = loop.run_in_executor(None, functools.partial( self.session.get
	# 	,	URL_XUEQIU_QUOTE(symbols)
	# 	,	headers = HEADERS_XUEQIU
	# 	) )
	# 	quote = yield from async_req
	# 	quote = quote.json()
	# 	if 'quote' not in self.__dict__.keys():
	# 		self.quote = quote
	# 	else:
	# 		self.quote.update( quote )

	# def get_realtime_quote(self, symbols, dataframe = True):
	# 	symbols = util.symbols_to_string(symbols)
	# 	quote = self.session.get(
	# 			URL_XUEQIU_QUOTE(symbols)
	# 		,	headers = HEADERS_XUEQIU
	# 		).json()
	# 	if dataframe:
	# 		return DataFrame.from_records( quote ).T
	# 	return quote

	"""
	雪球键盘助手
	"""
	def keyboard_helper(self,symbol):
		response = self.session.get(
			"https://xueqiu.com/stock/search.json?code=%s&size=10&_=%s"%(symbol,int(t.time()*1000))
		).json()["stocks"]
		return response