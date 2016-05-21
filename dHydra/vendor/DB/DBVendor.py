# -*- coding: utf-8 -*-
"""
# Created on 
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

from pymongo import MongoClient

class DBVendor(Vendor):
	def __init__(self):
		pass
	
	def get_mongodb(self, host = "localhost", port = 27017, timeout = 1500):
		# connect to mongodb named: stock
		try:
			print("尝试连接到Mongodb")
			client = MongoClient(host=host,port=port,serverSelectionTimeoutMS=timeout)
			client.server_info()
			print("已经成功连接到mongodb")
			return client
		except:
			self.logger.warning(">>>>>>>>>>>>>>>>>>连接到mongodb失败<<<<<<<<<<<<<<<<<<<")
			return False