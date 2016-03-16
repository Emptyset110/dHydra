# -*- coding: utf8 -*-
"""
股票接口类 
Created on 02/17/2016
@author: Wen Gu
@contact: emptyset110@gmail.com
"""
from __future__ import print_function, absolute_import
from pymongo import MongoClient
from datetime import datetime, timedelta
import pandas
from pandas import DataFrame
from pandas.compat import StringIO
import tushare as ts
import time as t
import json
from .config import const as C
from .config import connection as CON
from . import util
import threading
import asyncio
import functools
import os
import re
import requests

import inspect
import traceback
import sys

class Stock:
	def __init__(self, lang='cn'):
		# Magic, don't ask why #
		# I was trying to get the instance name from inside the class
		# BUT I'M GIVING UP
        ########################
		self.loop = asyncio.get_event_loop()
		# Connect to mongodb
		self.db = self.get_mongodb()
		self.outstanding = list()
		self.session = requests.Session()
		# 无数据库连接的方案
		if self.db==False:
			self.get_symbolList()
		else:
			# INITIALIZATION: CHECKING UPDATES
			self.update_basic_info()
			[self.codeList, self.symbolList, self.basicInfo] = self.fetch_basic_info()
		self.sina = None

	"""
	此接口用于从tushare,xueqiu两者中获取当日可靠的symbolList列表
	"""
	def get_symbolList(self):
		print( "正在从tushare获取基本面信息..." )
		self.tushareBasics = self.get_tushare_basics()
		self.tushareCodeList = list(self.tushareBasics.index)
		print( "从tushare获取的基本面已经保存到<实例名>.tushareBasics" )
		print( "也可以用<实例名>.tushareCodeList属性访问tushare获取的股票列表" )

		print( "正在从雪球社区获取股票" )
		# 先爬取一遍雪球页面，获取cookies
		xueqiu = self.session.get(
			"http://xueqiu.com/hq"
		,	headers = CON.HEADERS_XUEQIU
		)
		print( "正在从雪球社区获取当日沪深股票..." )
		try:
			self.xueqiuSHA = self.get_xueqiu_stocks(stockTypeList=['sha'])	#从雪球获取沪A股
			self.xueqiuSHB = self.get_xueqiu_stocks(stockTypeList=['shb'])	#从雪球获取沪B股
			self.xueqiuSZA = self.get_xueqiu_stocks(stockTypeList=['sza'])	#从雪球获取深A股
			self.xueqiuSZB = self.get_xueqiu_stocks(stockTypeList=['szb'])	#从雪球获取深B股
			self.xueqiu = self.xueqiuSHA.append(
				self.xueqiuSHB.append(
					self.xueqiuSZA.append(self.xueqiuSZB)
				)
			)
			self.xueqiuSymbolList = list(self.xueqiu.symbol)
			self.xueqiuCodeList = []
			for symbol in self.xueqiuSymbolList:
				self.xueqiuCodeList.append( symbol[2:8] )
			print( "<实例名>.xueqiu, <实例名>.xueqiuCodeList,<实例名>.xueqiuSymbolList" )
		except Exception as e:
			print( e )

	def get_mongodb(self):
		# connect to mongodb named: stock
		try:
			client = MongoClient(serverSelectionTimeoutMS=1)
			db = client.stock
			client.server_info()
			print("已经成功连接到mongodb")
			return db
		except:
			print("连接到mongodb失败")
			return False

	# def get_my_name(self):
	# 	ans = []
	# 	frame = inspect.currentframe().f_back
	# 	tmp = frame.f_globals.copy()
	# 	tmp.update(frame.f_locals)
	# 	for k, var in tmp.items():
	# 		if isinstance(var, self.__class__):
	# 			if hash(self) == hash(var):
	# 				ans.append(k)
	# 	return ans

	def get_symbol_list_eastmoney(self):
		response = self.session.get("http://quote.eastmoney.com/stocklist.html").text
		symbolListEastMoney = re.findall(r'<li><a target=\"_blank\" href=\"http:\/\/quote\.eastmoney\.com\/((?:sh|sz)(?:60|00|30|90|20)[\d]{4})\.html\">',response)
		codeListEastMoney = re.findall(r'<li><a target=\"_blank\" href=\"http:\/\/quote\.eastmoney\.com\/(?:sh|sz)((?:60|00|30|90|20)[\d]{4})\.html\">',response)

	"""
		这个数据来源自tushare
		更新频率不确定，存在更新不及时现象
	"""
	def get_tushare_basics(self):
		ts = self.session.get(CON.URL_TUSHARE_BASICS).text
		ts = ts.replace('--', '')
		tushare_basics = pandas.read_csv(StringIO(ts), dtype={'code':'object'})
		tushare_basics = tushare_basics.set_index('code')
		return tushare_basics


	"""
	>>>   雪球相关接口	   <<<
	"""
	"""
	stockTypeList 	: list
		['sha','shb','sza','szb']分别代表沪A，沪B，深A，深B。如果为空则代表获取所有沪深AB股
		e.g: stockTypeList = ['sha','shb']即获取所有沪A沪B
	columns 		:	string
		默认为："symbol,name,current,chg,percent,last_close,open,high,low,volume,amount,market_capital,pe_ttm,high52w,low52w,hasexist"
	"""
	def get_xueqiu_stocks(		self
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
	def async_fetch_xueqiu_basics(self, symbol=None):
		if symbol is not None:
			async_req = loop.run_in_executor(None, functools.partial( self.session.get
			,	CON.URL_XUEQIU_QUOTE(symbol)
			,	headers = CON.HEADERS_XUEQIU
			) )
			xueqiu_basics = yield from async_req
		return(xueqiu_basics)

	"""
	雪球单股基本面数据获取
	默认返回值格式是dict，若参数dataframe为True则返回dataframe
	"""
	def fetch_xueqiu_basics(self, symbol = None, dataframe = False):
		if symbol is not None:
			xueqiu_basics = self.session.get(
				CON.URL_XUEQIU_QUOTE(symbol)
			,	headers = CON.HEADERS_XUEQIU
			).json()
		if dataframe:
			xueqiu_basics = DataFrame.from_records( xueqiu_basics ).T
		return(xueqiu_basics)

	def get_xueqiu_basics_task(self):
		pass


	def get_xueqiu_basics(self, symbol=None, symbolList=None, async = True, dataframe = True):
		if async == False:
			if symbol is not None:
				xueqiu_basics = self.fetch_xueqiu_basics( symbol = symbol )
			elif symbolList is not None:
				xueqiu_basics = dict()
				for symbol in symbolList:
					xueqiu_basics.update( self.fetch_xueqiu_basics( symbol = symbol, dataframe = False) )
			else:
				print( "缺少symbol或symbolList参数" )
				xueqiu_basics = False
		else:
			loop = asyncio.get_event_loop()
			
			loop.close()

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


	## NOT IN USE ##
	def fetch_classification(self):
		# 数据来源自新浪财经的行业分类/概念分类/地域分类
		print( "Trying: get_today_all" )
		today_all = ts.get_today_all() #一次性获取今日全部股价
		set_today_all = set(today_all.T.values[0])

		print( "Trying: get_industry_classified" )
		industry_classified = ts.get_industry_classified()
		set_industry_classified = set(industry_classified.T.values[0])

		print( "Trying: get_area_classified" )
		area_classified = ts.get_area_classified()
		set_area_classified = set(area_classified.T.values[0])

		print( "Trying: get_concept_classified" )
		concept_classified = ts.get_concept_classified()
		set_concept_classified = set(concept_classified.T.values[0])

		print( "Trying: get_sme_classified" )
		sme_classified = ts.get_sme_classified()
		set_sme_classified = set(sme_classified.T.values[0])

		return [
					today_all
				,	set_today_all
				,	industry_classified
				,	set_industry_classified
				,	area_classified
				,	set_area_classified
				,	concept_classified
				,	set_concept_classified
				,	sme_classified
				,	set_sme_classified
				]

	# Will automatically call "update_basic_info" if needed
	# @return [self.codeList, self.symbolList, self.basicInfo]
	def fetch_basic_info(self):
		result = self.db.basicInfo.find_one( 
			{
				"lastUpdated": {"$exists":True, "$ne": None}
			}
		)
		if (result != None):
			codeList = list(result["basicInfo"]["name"].keys())
		else:
			update_basic_info()
			[codeList, result] = self.fetch_basic_info()

		symbolList = list()
		for code in codeList:
			symbolList.append( util._code_to_symbol(code) )

		self.updated = datetime.now()
		return [codeList, symbolList, result]

	# Update stock.basicInfo in mongodb
	def update_basic_info(self):
		update_necessity = False
		basicInfo = self.db.basicInfo.find_one( 
			{
				"lastUpdated": {"$exists":True, "$ne": None}
			}
		)
		if (basicInfo == None):
			print( "No record of basicInfo found. A new record is to be created......" )
			update_necessity = True
		else:
			# Criteria For Updating
			if ( ( basicInfo["lastUpdated"].date()<datetime.now().date() ) ):
				update_necessity = True
				print( "Stock Basic Info last updated on: ", basicInfo["lastUpdated"], "trying to update right now..." )
			elif ( basicInfo["lastUpdated"].hour<9 ) & ( datetime.now().hour>=9 ) :
				update_necessity = True
				print( "Stock Basic Info last updated on: ", basicInfo["lastUpdated"], "trying to update right now..." )
			else:
				print( "Stock Basic Info last updated on: ", basicInfo["lastUpdated"], " NO NEED to update right now..." )

		if (update_necessity):
			basicInfo = ts.get_stock_basics()
			
			result = self.db.basicInfo.update_one(
				{
					"lastUpdated": {"$exists": True, "$ne": None}
				},
				{
					"$set": {
						"lastUpdated": datetime.now(),
						"basicInfo": json.loads(ts.get_stock_basics().to_json()),
						"codeList": list(basicInfo.index)
					}
				},
				upsert = True
			)
			[self.codeList, self.symbolList, self.basicInfo] = self.fetch_basic_info()

	def self_updated(self,code):
		num = len(code)
		# TODO: UGLY HERE. Need a better logic for updating
		if ( ( self.updated.date() == datetime.now().date() ) & ( self.updated.hour >= 9 ) ):
			if ( self.outstanding == [] ):
				for i in range(0,num):
					self.outstanding.append( self.basicInfo["basicInfo"]["outstanding"][code[i]] )
		else:
			print( "The basicInfo is outdated. Trying to update basicInfo..." )
			self.update_basic_info()
			[self.codeList, self.symbolList, self.basicInfo] = self.fetch_basic_info()
			self.outstanding = list()
			for i in range(0,num):
				self.outstanding.append( self.basicInfo["basicInfo"]["outstanding"][code[i]] )

	# fetch realtime data using TuShare
	#	Thanks to tushare.org
	def fetch_realtime(self):
		i = 0
		while ( self.codeList[i:i+500] != [] ):
			if (i==0):
				realtime = ts.get_realtime_quotes( self.codeList[i : i+500] )
			else:
				realtime = realtime.append( ts.get_realtime_quotes( self.codeList[i : i+500] ), ignore_index=True )
			i += 500

		# Get the datetime
		data_time = datetime.strptime( realtime.iloc[0]["date"] + " " + realtime.iloc[0]["time"] , '%Y-%m-%d %H:%M:%S')
		code = realtime["code"]
		realtime["time"] = data_time
		# Drop Useless colulmns
		realtime = realtime.drop( realtime.columns[[0,6,7,30]] ,axis = 1)
		# Convert string to float
		realtime = realtime.convert_objects(convert_dates=False,convert_numeric=True,convert_timedeltas=False)
		# update self.basicInfo & self.outstanding
		self.self_updated(code)
		# Compute turn_over_rate
		realtime["turn_over_ratio"] = realtime["volume"]/self.outstanding/100
		realtime["code"] = code

		return realtime

	# First fetch_realtime, then insert it into mongodb
	def get_realtime(self,time):
		realtime = self.fetch_realtime()

		data_time = realtime.iloc[0]['time']
		if (data_time>time):
			time = data_time
		else:
			print( "No need", time )
			return data_time

		self.db.realtime.insert_many( realtime.iloc[0:2900].to_dict(orient='records') )
		print( "data_time", data_time )
		return time

	def start_realtime(self):
		time = datetime.now()
		while True:
			try:
				start = datetime.now()

				if (start.hour<9 or start.hour>15):
					print( "It's Too Early or Too late", start )
					t.sleep(360)
					continue
				time = self.get_realtime( time )
				print( "time cost:", (datetime.now()-start) )
			except Exception as e:
				print( e )
				# traceback.print_exc()

	def export_realtime_csv(	self
							,	date=None
							,	end=str( (datetime.now()+timedelta(days=1)).date() )
							,	resample=None,	prefix=''
							,	path=C.PATH_DATA_ROOT+C.PATH_DATA_REALTIME
							):
		total_len = len(self.codeList)
		start_time = datetime.now()

		if date==None:
			s_date = input('Please input the date(Format:"2016-02-16"):')
		else:
			s_date = date

		# import os
		try:
		    os.makedirs( "%s%s" % ( path,s_date ), exist_ok=True )
		except Exception as e:
			print(e)
			try:
				os.makedirs( "%s%s" % ( path,s_date ) )
			except Exception as e:
				print(e)
				pass
		date = datetime.strptime(s_date, '%Y-%m-%d')

		for i in range(0,total_len):

			items = list()
			# print( type(self.codeList[i]) )
			stock_cursor = self.db.realtime.find(
				{
					"code": self.codeList[i]
				,	"time": { "$gt": date, "$lt" : date + timedelta(days=1) }
				}
			)

			if (stock_cursor.count() == 0):
				continue

			for row in stock_cursor:
				items.append(row)

			stock_csv = pandas.DataFrame.from_dict(items)

			stock_csv["turn_over_ratio"] = stock_csv["volume"]/self.basicInfo["basicInfo"]["outstanding"][ self.codeList[i] ]/100

			stock_csv.set_index("time",drop=False,inplace=True)
			if (resample!=None):
				stock_csv = stock_csv.resample(resample,how='last')
			upper_bound = datetime.strptime( s_date+" "+'09:15:00' , '%Y-%m-%d %H:%M:%S')
			lower_bound = datetime.strptime( s_date+" "+'15:05:00' , '%Y-%m-%d %H:%M:%S')
			stock_csv = stock_csv[(stock_csv.time>upper_bound) & (stock_csv.time<lower_bound)]
			stock_csv.to_csv( 	'%s%s/%s.csv'% (path,s_date,self.codeList[i])
							,	columns = [	
											"volume"
										,	"amount"
										,	"price"
										,	"b1_ratio"
										,	"a1_p",	"a1_v"
										,	"a2_p",	"a2_v"
										,	"a3_p",	"a3_v"
										,	"a4_p",	"a4_v"
										,	"a5_p",	"a5_v"
										,	"b1_p",	"b1_v"
										,	"b2_p",	"b2_v"
										,	"b3_p",	"b3_v"
										,	"b4_p",	"b4_v"
										,	"b5_p",	"b5_v"
										,	"open",	"pre_close"
										,	"turn_over_ratio"
										]
			)

			print("time cost:",( datetime.now()-start_time ) )
			print("Process: ",float(i)/float(total_len)*100, "%")

	"""
	下面是调用新浪部分
	"""
	def get_sina(self):
		from . import sinaFinance
		self.sina = sinaFinance.SinaFinance()
		return self.sina

	# 开启新浪L2 Websocket
	def start_sina(self, callback=None):
		if (self.sina is None):
			self.get_sina()

		if not(self.sina.isLogin):
			print("新浪没有登录成功，请重试")
			return False

		threads = []
		# Cut symbolList
		step = 30
		symbolListSlice = [self.symbolList[ i : i + step] for i in range(0, len(self.symbolList), step)]
		for symbolList in symbolListSlice:

			loop = asyncio.get_event_loop()
			if loop.is_running():
				loop = asyncio.new_event_loop()
				asyncio.set_event_loop( loop )

			t = threading.Thread(target = self.sina.start_ws,args=(symbolList,loop,callback) )
			threads.append(t)
		for t in threads:
			t.setDaemon(True)
			t.start()
			print("开启线程：",t.name)
		for t in threads:
			t.join()

	# thread_num代表同时开启的线程数量，默认15个
	def sina_l2_hist(self,thread_num = 15, symbolList = None):
		if (symbolList is None):
			symbolList = self.symbolList
		if (self.sina is None):
			self.get_sina()
		if not(self.sina.isLogin):
			print("新浪没有登录成功，请重试")
			return False
		threads = []
		step = int( len(symbolList)/thread_num ) if ( int( len(symbolList)/thread_num )!=0 ) else 1
		symbolListSlice = [symbolList[ i : i + step] for i in range(0, len(symbolList), step)]
		for symbolList in symbolListSlice:

			loop = asyncio.get_event_loop()
			if loop.is_running():
				loop = asyncio.new_event_loop()
				asyncio.set_event_loop( loop )

			t = threading.Thread(target = self.sina.l2_hist_list, args=(symbolList,loop,) )
			threads.append(t)

		for t in threads:
			t.setDaemon(True)
			t.start()
			print("开启线程：",t.name)
		for t in threads:
			t.join()
