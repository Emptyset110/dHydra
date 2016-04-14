# -*- coding: utf8 -*-
"""
# Created on 04/12/2016
# @author: Emptyset
# @contact: Emptyset110@gmail
"""
# 以下是自动生成的 #
# --- 导入系统配置
from dHydra.app import PRODUCER_NAME, PRODUCER_HASH
import dHydra.core.util as util
from dHydra.core.Action import Action
from dHydra.core.Event import Event
from dHydra.config import connection as CON
from dHydra.config import const as C
from dHydra.core.Functions import *
# --- 导入自定义配置

from pymongo import MongoClient
import pymongo
import time
from datetime import datetime

# 以上是自动生成的 #
class SinaTickToMongoAction(Action):
	def __init__(self, name, **kwargs):
		# 用户自定义自动加载的_producerList
		self._producerList = [
			{	
				"name"	:	"SinaFreeQuote"
			,	"pName"	:	"SinaTickToMongo.SinaFreeQuote"		#这是在action内部给producer起的自定义名字，可随意。一般最好遵守<actionName.producerName>
			}
		]
		# 设置进程检查消息队列的间隔
		self._interval = 0.5
		super().__init__(name, **kwargs)
		print(self._name,"初始化")
		self.db = False
		while self.db == False:
			self.db = self.get_mongodb()
			time.sleep(2)

		# 这里需要初始化一下最近插入mongodb的时间戳
		sh = self.db.realtime.find_one( 
			{
				"symbol" : { '$lt' : 'sz' }
			}
		,	sort = [("_id", pymongo.DESCENDING)]
			)
		sz = self.db.realtime.find_one( 
			{
				"symbol" : { '$gt' : 'sz' }
			}
		,	sort = [("_id", pymongo.DESCENDING)]
			)
		if sh is not None:
			self.shTime = sh["time"]
			print("数据库中最近的SH ticktime:", self.shTime)
		if sz is not None:
			self.szTime = sz["time"]
			print("数据库中最近的SZ ticktime:", self.szTime)
		if (sh is None) and (sz is None):
			self.szTime = datetime(1970,1,1)
			self.shTime = datetime(1970,1,1)

	# 需要重写的方法
	def handler(self):
		while not self._queue.empty():
			event = self._queue.get(True)
			# 将event.data存储到mongodb
			l = len(event.data)
			if event.exchange == 'SZ':
				self.time = self.szTime
			elif event.exchange == 'SH':
				self.time = self.shTime
			if event.time > self.time:
				self.time = event.time
				self.db.realtime.insert_many( event.data.iloc[0:l].to_dict(orient='records') )
				print("Insert Realtime Quotes Successfully, {}, {}".format(self.time, event.exchange))
			else:
				print("消息队列中获取到一个已经存过了时间戳, {}, {}".format(self.time, event.exchange) )


	def get_mongodb(self):
		# connect to mongodb named: stock
		try:
			print("尝试连接到Mongodb")
			client = MongoClient(serverSelectionTimeoutMS=1500)
			db = client.stock
			client.server_info()
			print("已经成功连接到mongodb")
			return db
		except:
			print(">>>>>>>>>>>>>>>>>>>>>连接到mongodb失败<<<<<<<<<<<<<<<<<<<")
			print("将在2秒后重试")
			return False