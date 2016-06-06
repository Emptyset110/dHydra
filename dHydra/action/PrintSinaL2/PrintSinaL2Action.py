# -*- coding: utf-8 -*-
from dHydra.core.Action import Action
from dHydra.core import util
from dHydra.app import PRODUCER_NAME, PRODUCER_HASH
from dHydra.core.Functions import *
from dHydra.core.ThreadManager import Manager
import re
from datetime import datetime
import threading

class PrintSinaL2Action(Action):
	def __init__(self, **kwargs):

		if "raw" in kwargs.keys():
			self.raw = kwargs["raw"]
		else:
			self.raw = True
		# 设置进程检查消息队列的间隔
		super().__init__( **kwargs )
		self.logger.info(self._name +"初始化")
		self.count = 0

	# 需要重写的方法
	def handler(self, event):
		dt = datetime.now()
		if not self.raw:
			event.data = util.ws_parse(message = event.data)
		if isinstance(event.data, list):
			for data in event.data:
				self.count += 1
				print("PrintSinaL2:{}, Count:{}\n{}".format( dt,self.count,data ) )
		else:
			self.count += 1
			print("PrintSinaL2:{}, Count:{}\n{}".format( dt,self.count,data ) )

		# self.logger.info("线程退出")
