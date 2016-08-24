# -*- coding: utf-8 -*-
"""
# Created on
# @author:
# @contact:
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
# import datetime
from datetime import datetime
from pandas import DataFrame
import time
import threading
# 以上是自动生成的 #
class SinaL2ToMongoAction(Action):
	def __init__(self, **kwargs):
		super().__init__( **kwargs )
		self.logger.info(self._name +"初始化")
		self.db = V("DB").get_mongodb()
		self.count = 0
		self.total = 0
		self.start_time = time.time()
		t = threading.Thread(target = self.thread_count )
		t.setDaemon(True)
		t.start()

	def thread_count(self,):
		while True:
			time.sleep(15)
			self.logger.info("Time Elapsed: {}, Data Inserted: {}, Data Handled: {}".format( time.time()-self.start_time, self.count, self.total ) )

	# 需要重写的方法
	def handler(self, event):
		event.data = util.ws_parse( message = event.data, to_dict = True )
		for data in event.data:
			try:
				self.total += 1
				if data["data_type"] == "deal":
					self.count += 1
					result = self.db.stock.l2_deal.insert_one( data )	# 自己建立unique索引
				elif data["data_type"] == "quotation":
					self.count += 1
					result = self.db.stock.l2_quotation.insert_one( data )	# 自己建立unique索引
			except Exception as e:
				self.total += 1
