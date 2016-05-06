# -*- coding: utf8 -*-
from dHydra.core.Action import Action
from dHydra.core import util
from dHydra.app import PRODUCER_NAME, PRODUCER_HASH
from dHydra.core.Functions import *

import re
from datetime import datetime
import threading

class PrintSinaL2Action(Action):
	def __init__(self, name, **kwargs):
		# 用户自定义自动加载的_producerList
		self._producerList = [
			{	
				"name"	:	"SinaLevel2WS"
			,	"pName"	:	"PrintSinaL2.SinaLevel2-quotation"
			,	"query"	:	['quotation']	#只获取10档行情
			}
		# ,	{
		# 		"name"	:	"SinaLevel2WS"
		# 	,	"pName"	:	"PrintSinaL2.SinaLevel2-deal"
		# 	,	"query"	:	['deal']
		# 	}
		]
		# 设置进程检查消息队列的间隔
		self._interval = 0.1
		super().__init__(name, **kwargs)
		self.logger.info(self._name +"初始化")
		self.count = 0
 
	# 需要重写的方法
	def handler(self):
		while not self._queue.empty():
			dt = datetime.now()
			event = self._queue.get(True)
			# event.data = self.ws_parse(message = event.data)
			if isinstance(event.data, list):
				for data in event.data:
					print("PrintSinaL2:\n", data )

					# print(self.count)
					pass
			else:
				print( datetime.now() )
				print(event.data)
				
		# self.logger.info("线程退出")

	"""
	用于解析Sina l2的函数
	"""
	def ws_parse(self, message):
		dataList = re.findall(r'(?:((?:2cn_)?((?:sh|sz)[\d]{6})(?:_0|_1|_orders|_i)?)(?:=)(.*)(?:\n))',message)
		result = list()
		for data in dataList:
			if (len(data[0])==12):	# quotation
				wstype = 'quotation'
				self.count += 1
			elif ( (data[0][-2:]=='_0') | (data[0][-2:]=='_1') ):
				wstype = 'deal'
			elif ( data[0][-6:]=='orders' ):
				wstype = 'orders'
			elif ( (data[0][-2:]=='_i') ):
				wstype = 'info'
			else:
				wstype = 'other'
			result = self.ws_parse_to_list(wstype=wstype,symbol=data[1],data=data[2],result=result)
		return result

	def ws_parse_to_list(self,wstype,symbol,data,result):
		data = data.split(',')
		if (wstype == 'deal'):
			for d in data:
				x = list()
				x.append(wstype)
				x.append(symbol)
				x.extend( d.split('|') )
				result.append(x)
		else:
			x = list()
			x.append(wstype)
			x.append(symbol)
			x.extend(data)
			result.append(x)
		return result