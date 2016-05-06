# -*- coding: utf8 -*-
"""
# Created on 05/06/2016
# @author: Emptyset
# @contact: emptyset110@gmail
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
import socket
import time
import threading

# 以上是自动生成的 #
class SinaL2TCPAction(Action):
	def __init__(	self
				,	name
				,	producerList = [
					{	
						"name"	:	"SinaLevel2WS"
					,	"pName"	:	"SinaL2TCP.quotation"
					,	"query"	:	['quotation']	#只获取10档行情
					} 
					]
				,	addr = "127.0.0.1"
				,	port 	= 9999
				,	interval = 0.2
				, 	**kwargs
				):
		# 用户自定义自动加载的_producerList
		self._producerList = producerList
		# 设置进程检查消息队列的间隔
		self._interval = interval
		super().__init__(name, **kwargs)
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		while True:
			try:
				self.s.connect( ( addr, port ) )
				break
			except Exception as e:
				self.logger.error( "{}:{}建立socket连接失败, {}\n5秒后重试".format(addr,port,e) )
				time.sleep(5)
		self.mutex = threading.Lock()

	# 需要重写的方法
	def handler(self):
		while not self._queue.empty():
			self.mutex.acquire()
			event = self._queue.get(True)
			self.mutex.release()
			if isinstance(event.data, list):
				for data in event.data:
					try:
						self.s.send( event.data.encode(encoding="utf-8") )
					except Exception as e:
						self.logger.error( "{}".format(e) )
						time.sleep(2)
			else:
				try:
					# print( "发送{}".format(event.data) )
					self.s.send( event.data.encode(encoding="utf-8") )
				except Exception as e:
					self.logger.error( "{}".format(e) )
					time.sleep(2)
