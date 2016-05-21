# -*- coding: utf-8 -*-
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
from dHydra.core.Functions import V
from dHydra.config import connection as CON
from dHydra.config import const as C
# --- 导入自定义配置
from .connection import *
from .const import *
from .config import *
# 以上是自动生成的 #
import pytz
import requests
import asyncio
from pandas import DataFrame
import pandas
from datetime import datetime, timedelta
import functools
import threading
import pymongo
import time

class XueqiuVendor(Vendor):

	def __init__(self):
		super().__init__()
		self.session = requests.Session()
		# 先爬取一遍雪球页面，获取cookies
		xq = self.session.get(
			"https://xueqiu.com/hq"
		,	headers = HEADERS_XUEQIU
		)
		self.mongodb = None

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
		try:
			response = self.session.get(
					URL_XUEQIU_KLINE( symbol = symbol, period = period, fqType = fqType, begin = begin, end = end )
				,	headers = HEADERS_XUEQIU
				,	timeout = 3
				)
			kline = response.json()
			time.sleep(0.5)
		except Exception as e:
			self.logger.warning("{}".format(e))
			self.logger.info(response.text)
			time.sleep(3)
			return None

		if kline["success"]=='true':
			if dataframe:
				if kline["chartlist"] is not None:
					df = DataFrame.from_records( kline["chartlist"] )
					df["time"] = pandas.to_datetime( df["time"] )
					df["time"] += timedelta(hours=8)
					df["symbol"] = symbol
					return df
				else:
					return DataFrame()
			else:
				return kline["chartlist"]
		else:
			return None

	"""
	将单股票历史k线存入mongodb
	"""
	def kline_to_mongodb(self, symbol, types=["normal","before","after"], end = None, dbName = 'stock', collectionName = 'kline_history', host='localhost', port=27017):
		types = ["normal","before","after"]
		if end is None:
			end = datetime.now().date()
		else:
			end = util.string_to_date(end)
		if self.mongodb is None:
			self.mongodb = V("DB").get_mongodb(host=host, port=port)
		if self.mongodb == False:
			self.logger.error("没有连接上mongodb")
			return False

		for fqType in types:
			# 先找到mongodb中这条股票的最新记录
			latest = self.mongodb[dbName][collectionName].find_one(
				{ "symbol"	:	symbol, "type" : fqType }
			,	sort = [("time", -1)]
			)
			if latest is not None:
				begin = ( latest["time"]+timedelta(days=1) ).strftime("%Y-%m-%d")
				self.logger.info("symbol = {}, {}\t最近更新记录为 {}".format(symbol,fqType,latest["time"]))
				if latest["time"].date() >= end:
					self.logger.info("不需要更新")
					return True
			else:
				begin = None
				self.logger.info("symbol = {}, {}\t无最近更新记录".format(symbol,fqType))

			self.logger.info("开始更新symbol = {} \t {}".format(symbol, fqType))
			kline = None
			while kline is None:
				kline = self.get_kline(symbol, begin = begin)

			if len(kline)>0:
				kline["type"] = fqType
				kline = kline.iloc[0:len(kline)].to_dict(orient="records")
				self.mongodb[dbName][collectionName].insert_many( kline )
		return True

	def kline_history(self, symbols = None,end = None, types = ["normal","before","after"], dbName = "stock", collectionName = "kline_history", host="localhost", port=27017):
		if symbols is None:
			# 我选择从新浪获取一份股票列表
			sina = V("Sina")
			symbolList = sina.get_symbols()
		elif isinstance(symbols, str):
			symbolList = symbols.split(',')
		else:
			symbolList = list(symbols)

		for symbol in symbolList:
			self.kline_to_mongodb(symbol, types=types,end = end, dbName=dbName, collectionName=collectionName, host=host, port=port)
		return True

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
				df = DataFrame.from_records( quotation["chartlist"] )
				df["time"] = pandas.to_datetime( df["time"] )
				df["time"] += timedelta(hours=8)
				df["symbol"] = symbol
				return df
			else:
				return quotation["chartlist"]
		else:
			return False

	"""
	雪球键盘助手
	"""
	def keyboard_helper(self,symbol):
		response = self.session.get(
			"https://xueqiu.com/stock/search.json?code=%s&size=10&_=%s"%(symbol,int(t.time()*1000))
		).json()["stocks"]
		return response