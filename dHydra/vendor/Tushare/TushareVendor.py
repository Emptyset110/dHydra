# -*- coding: utf8 -*-
"""
股票接口类 
Created on 02/17/2016
@author: Wen Gu
@contact: emptyset110@gmail.com
"""
# 这部分自动生成 #
from dHydra.core.Vendor import Vendor
from dHydra.config import connection as CON
from dHydra.config import const as C
import dHydra.core.util as util
###############

from pymongo import MongoClient
from datetime import datetime, timedelta
import pandas
from pandas import DataFrame
from pandas.compat import StringIO
import tushare as ts
import time as t
import json
import os
import re
import requests

class TushareVendor(Vendor):
	def __init__(self, lang='cn'):
		# Connect to mongodb
		self.db = self.get_mongodb()
		self.outstanding = list()
		self.session = requests.Session()
		# self.xq = self.get_xueqiu()	#获取雪球实例

		self.get_symbolList()
		if self.db:
			# INITIALIZATION: CHECKING UPDATES
			self.update_basic_info()
			[self.codeList, self.symbolList, self.basicInfo] = self.get_basic_info()
		else:
			print("目前采用非数据库模式")

		self.sina = None
		self.xueqiu_basics = {}

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
		,	headers = HEADERS_XUEQIU
		)
		print( "正在从雪球社区获取当日沪深股票..." )
		try:
			self.xueqiuSHA = self.xq.get_stocks(stockTypeList=['sha'])	#从雪球获取沪A股
			self.xueqiuSHB = self.xq.get_stocks(stockTypeList=['shb'])	#从雪球获取沪B股
			self.xueqiuSZA = self.xq.get_stocks(stockTypeList=['sza'])	#从雪球获取深A股
			self.xueqiuSZB = self.xq.get_stocks(stockTypeList=['szb'])	#从雪球获取深B股
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
			client = MongoClient(serverSelectionTimeoutMS=1000)
			db = client.stock
			client.server_info()
			print("已经成功连接到mongodb")
			return db
		except:
			print(">>>>>>>>>>>>>>>>>>>>>连接到mongodb失败<<<<<<<<<<<<<<<<<<<")
			print("请确保mongodb服务开启以后重新加载本类")
			return False

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

	def get_basic_info(self):
		result = self.db.basicInfo.find_one(
			{
				"lastUpdated": {"$exists":True, "$ne": None}
			}
		)
		if (result != None):
			codeList = list(result["basicInfo"]["name"].keys())
		else:
			update_basic_info()
			[codeList, symbolList, result] = self.get_basic_info()

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
			[self.codeList, self.symbolList, self.basicInfo] = self.get_basic_info()

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
			[self.codeList, self.symbolList, self.basicInfo] = self.get_basic_info()
			self.outstanding = list()
			for i in range(0,num):
				self.outstanding.append( self.basicInfo["basicInfo"]["outstanding"][code[i]] )

	# fetch realtime data using TuShare
	#	Thanks to tushare.org
	def fetch_realtime(self, codeList = None):
		if codeList is None:
			codeList = self.codeList
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
	def get_realtime(self,time,codeList = None):
		realtime = self.fetch_realtime(codeList = codeList)

		data_time = realtime.iloc[0]['time']
		if (data_time>time):
			time = data_time
		else:
			print( "No need", data_time,time )
			return data_time

		self.db.realtime.insert_many( realtime.iloc[0:2900].to_dict(orient='records') )
		print( "data_time", data_time )
		return data_time

	def start_realtime(self, timeInterval = None, codeList = None):
		loop = asyncio.get_event_loop()
		time = datetime.now()
		while True:
			try:
				start = datetime.now()

				if (start.hour<9 or start.hour>15):
					print( "It's Too Early or Too late", start )
					t.sleep(360)
					continue
				if timeInterval is not None:
					t.sleep(timeInterval)
					time = self.get_realtime( time )
				else:
					time = self.get_realtime( time )
				print( "time cost:", (datetime.now()-start) )
			except Exception as e:
				print( e )