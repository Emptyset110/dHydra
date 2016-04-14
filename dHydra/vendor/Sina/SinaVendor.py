# -*- coding: utf8 -*-
"""
# Created on 2016/04/12
# @author: 
# @contact: 
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
import re
from pandas import DataFrame
import asyncio
import functools
from datetime import datetime
import json


class SinaVendor(Vendor):
	def __init__(self):
		self.session = requests.Session()
		self.quote = None

	# sz,sh的时间戳不同，强烈建议分开调用
	# 如果开启split = True, 则会返回
	def get_realtime_quotes(self, symbols = None, dataframe = True, loop = None, split = False):
		self.quote = None
		if symbols is None:
			symbols = self.get_symbols()
		if loop is None:
			loop = asyncio.get_event_loop()
		# if loop.is_running:
		else:
			asyncio.set_event_loop(loop)

		if isinstance(symbols, str):
			symbolList = symbols.split(',')
		else:
			symbolList = list(symbols)
		[ symbols_sz, symbols_sh ] = util.split_symbols(symbolList)
		symbolListSlice = util.slice_list(step = 800, dataList = symbols_sz)
		symbolListSlice.extend( util.slice_list(step = 800, dataList = symbols_sh) )
		loop.run_until_complete( self.get_quote_task(symbolListSlice=symbolListSlice, dataframe = dataframe) )
		if dataframe:
			self.quote = self.quote.drop( 'ms', axis = 1 )
			self.quote.convert_objects(convert_dates=False,convert_numeric=True,convert_timedeltas=False)
		if split:
			quote_sz = self.quote[ self.quote.symbol > 'sz' ]
			quote_sh = self.quote[ self.quote.symbol < 'sz' ]
			return [ quote_sz, quote_sh ]
		return self.quote

	@asyncio.coroutine
	def get_quote_task(self, symbolListSlice, dataframe):
		for symbolList in symbolListSlice:
			quote = yield from self.get_quote_coroutine(symbols = symbolList, dataframe=dataframe)
			if self.quote is None:
				self.quote = quote
			else:
				if dataframe:
					self.quote = self.quote.append(quote, ignore_index=True)
				else:
					self.quote.extend(quote)
					

	@asyncio.coroutine
	def get_quote_coroutine(self, symbols, dataframe):
		loop = asyncio.get_event_loop()
		if isinstance(symbols, list) or isinstance(symbols, set) or isinstance(symbols, tuple):
			symbolList = list(symbols)
		elif isinstance(symbols, str):
			symbolList = symbols.split(',')
		symbols = util.symbols_to_string(symbols)
		url = URL_QUOTATION(symbols) 

		retry = True
		while retry:
			try:
				async_req = loop.run_in_executor(None, functools.partial( self.session.get
				,	URL_QUOTATION(symbols)
				,	timeout = 0.1
				) )
				quote = yield from async_req
				retry = False
			except:
				pass
		quote = quote.text
		quote = re.findall(r'\"(.*)\"', quote)

		for i in range( 0, len(quote) ):
			quote[i] = quote[i].split(',')

		if dataframe:
			quote = DataFrame( quote, columns = SINA_QUOTE_COLUMNS )
			quote["symbol"] = symbolList
			quote["time"] = datetime.strptime( quote.iloc[0]["date"] + " " + quote.iloc[0]["time"] , '%Y-%m-%d %H:%M:%S')
		return quote

	# 新浪获取当前全部股票的接口
	# 如果 dataframe = True， 则返回panda.DataFrame格式，
	# 否则 返回list格式，每个list中是一个dict
	def get_today_all(self, node = 'hs_a', dataframe = True):
		import json
		import time

		# start = time.time()
		retry = True
		while retry:
			try:
				response = self.session.get(
					URL_API_MARKET_CENTER_GETHQNODEDATA(node)
				,	timeout = 3
					).text
				retry = False
			except:
				print("获取数据超时，正在重试")
		# 因为返回的json不标准，需要给key加上引号
		response = response.replace(
			"symbol","\"symbol\""
			).replace(
			"code","\"code\""
			).replace(
			"name","\"name\""
			).replace(
			"trade","\"trade\""
			).replace(
			"pricechange","\"pricechange\""
			).replace(
			"pricepercent","\"pricepercent\""
			).replace(
			"buy","\"buy\""
			).replace(
			"sell","\"sell\""
			).replace(
			"settlement","\"settlement\""
			).replace(
			"open","\"open\""
			).replace(
			"high","\"high\""
			).replace(
			"low","\"low\""
			).replace(
			"volume","\"volume\""
			).replace(
			"amount","\"amount\""
			).replace(
			"ticktime","\"ticktime\""
			).replace(
			"per","\"per\""
			).replace(
			"pb","\"pb\""
			).replace(
			"mktcap","\"mktcap\""
			).replace(
			"nmc","\"nmc\""
			).replace(
			"turnoverratio","\"turnoverratio\""
			).replace("change\"per\"cent","\"changepercent\"")
		# print(time.time()-start)
		todayAll = json.loads( response )
		if dataframe:
			todayAll = DataFrame(todayAll)
		return todayAll

	"""
	用于获取当日股票列表
	返回： list
	参数：
		（可选）stockTypeList:
			类型：list
			默认：["hs_a","hs_b"] 代表获取全部沪深AB代码
	"""
	def get_symbols(self, stockTypeList = ["hs_a","hs_b"]):
		symbolList = list()
		for node in stockTypeList:
			symbols = list(self.get_today_all(node = node)["symbol"])
			symbolList.extend(symbols)
		return symbolList

	def get_quote(self, symbols, dataframe = True):
		if isinstance(symbols, list) or isinstance(symbols, set) or isinstance(symbols, tuple):
			symbolList = list(symbols)
		elif isinstance(symbols, str):
			symbolList = symbols.split(',')
		symbols = util.symbols_to_string(symbols)
		url = URL_QUOTATION(symbols)
		retry = True
		while retry:
			try:
				quote  =self.session.get( 
						URL_QUOTATION(symbols) 
					,	timeout = 0.1
					).text
				retry = False
			except:
				pass
		quoteList = re.findall(r'\"(.*)\"', quote)
		if dataframe:
			for i in range( 0, len(quoteList) ):
				quoteList[i] = quoteList[i].split(',')
		else:
			for i in range( 0, len(quoteList) ):
				quoteList[i] = quoteList[i].split(',')
				quoteList[i].append( symbolList[i] )

		if dataframe:
			df_quote = DataFrame( quoteList, columns = SINA_QUOTE_COLUMNS )
			df_quote = df_quote.drop( 'ms', axis = 1 )
			df_quote["symbol"] = symbolList
			return df_quote
		else:
			return quoteList

	def get_ticktime(self):
		quote = self.get_quote(symbols= ["sz000001","sh600000"])
		szTime = datetime.strptime( quote.iloc[0]["date"] + " " + quote.iloc[0]["time"] , '%Y-%m-%d %H:%M:%S')
		shTime = datetime.strptime( quote.iloc[1]["date"] + " " + quote.iloc[1]["time"] , '%Y-%m-%d %H:%M:%S')
		return [szTime, shTime]