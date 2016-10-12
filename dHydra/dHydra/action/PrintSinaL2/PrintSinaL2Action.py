# -*- coding: utf-8 -*-
from dHydra.core.Action import Action
from dHydra.core import util
from dHydra.app import PRODUCER_NAME, PRODUCER_HASH
from dHydra.core.Functions import *
import re
from datetime import datetime
import threading


class PrintSinaL2Action(Action):
	def __init__(self, **kwargs):

		if "raw" in kwargs.keys():
			self.raw = kwargs["raw"]
		else:
			self.raw = True

		super().__init__( **kwargs )
		self.logger.info(self._name +"初始化")
		self.count = 0
		if "to_dict" in kwargs.keys():
			self.to_dict = kwargs["to_dict"]
		else:
			self.to_dict = None

	# 需要重写的方法
	def handler(self, event):
		dt = datetime.now()
		if not self.raw:
			event.data = util.ws_parse( message = event.data, to_dict = self.to_dict )
		if isinstance(event.data, list):
			for data in event.data:
				self.count += 1
				print("PrintSinaL2:{}, \nCount:{},  Length: {}\n{}".format( dt,self.count, len(data),data ) )
		else:
			self.count += 1
			print("PrintSinaL2:{}, \nCount:{},  Length: {}\n{}".format( dt,self.count, len(event.data),event.data ) )

		# self.logger.info("线程退出")
