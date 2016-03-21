# -*- coding: utf8 -*-
"""
雪球社区接口类 
Created on 03/17/2016
@author: Wen Gu
@contact: emptyset110@gmail.com
"""
import requests
import asyncio
from pandas import DataFrame
from .config import const as C
from .config import connection as CON

class Xueqiu:
	def __init__(self):
		self.session = requests.Session()
		# 先爬取一遍雪球页面，获取cookies
		xq = self.session.get(
			"http://xueqiu.com/hq"
		,	headers = CON.HEADERS_XUEQIU
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
				,	columns 		=	CON.CONST_XUEQIU_QUOTE_ORDER_COLUMN
		):
		stock_xueqiu = None
		for stockType in stockTypeList:
			print( "正在从雪球获取：{}".format(C.EX_NAME[stockType]) )
			page = 1
			while True:
				response = self.session.get(
					CON.URL_XUEQIU_QUOTE_ORDER(page,columns,stockType)
				,	headers = CON.HEADERS_XUEQIU
				).json()
				df = DataFrame.from_records(response["data"], columns=response["column"])
				if stock_xueqiu is None:
					stock_xueqiu = df
				else:
					stock_xueqiu = stock_xueqiu.append(df)
				if df.size==0:
					break
				page += 1

		self.stock_xueqiu = stock_xueqiu
		return stock_xueqiu

	"""
	雪球单股基本面数据获取coroutine
	"""
	@asyncio.coroutine
	def async_fetch_basics(self, symbol=None):
		loop = asyncio.get_event_loop()
		if symbol is not None:
			async_req = loop.run_in_executor(None, functools.partial( self.session.get
			,	CON.URL_XUEQIU_QUOTE(symbol)
			,	headers = CON.HEADERS_XUEQIU
			) )
			xueqiu_basics = yield from async_req
			xueqiu_basics = xueqiu_basics.json()
		return(xueqiu_basics)

	"""
	雪球单股基本面数据获取
	默认返回值格式是dict，若参数dataframe为True则返回dataframe
	"""
	def fetch_basics(self, symbol = None, dataframe = False):
		if symbol is not None:
			xueqiu_basics = self.session.get(
				CON.URL_XUEQIU_QUOTE(symbol)
			,	headers = CON.HEADERS_XUEQIU
			).json()
		if dataframe:
			xueqiu_basics = DataFrame.from_records( xueqiu_basics ).T
		return(xueqiu_basics)

	@asyncio.coroutine
	def get_basics_task(self, symbol):
		xueqiu_basics = yield from self.async_fetch_basics(symbol = symbol)
		self.xueqiu_basics = self.xueqiu_basics.update( xueqiu_basics )

	def get_basics(self, symbol=None, symbolList=None, async = True, dataframe = True):
		loop = asyncio.get_event_loop()
		asyncio.set_event_loop(loop)
		if async == False:
			if symbol is not None:
				xueqiu_basics = self.fetch_basics( symbol = symbol )
			elif symbolList is not None:
				xueqiu_basics = dict()
				for symbol in symbolList:
					xueqiu_basics.update( self.fetch_basics( symbol = symbol, dataframe = False) )
			else:
				print( "缺少symbol或symbolList参数" )
				xueqiu_basics = False
		else:
			asyncio.set_event_loop(loop)
			tasks = [self.get_basics_task(symbol=symbol) for symbol in symbolList]
			loop.run_until_complete( asyncio.wait(tasks) )
			loop.close()

		if async:
			xueqiu_basics = self.xueqiu_basics
		if dataframe:
			xueqiu_basics = DataFrame.from_records( xueqiu_basics ).T
		return(xueqiu_basics)



	"""
	雪球键盘助手
	"""
	def keyboard_helper(self,symbol):
		response = self.session.get(
			"http://xueqiu.com/stock/search.json?code=%s&size=10&_=%s"%(symbol,int(t.time()*1000))
		).json()["stocks"]