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
from dHydra.core.Producer import Producer
from dHydra.core.Event import Event
from dHydra.config import connection as CON
from dHydra.config import const as C
from dHydra.core.Functions import *
# --- 导入自定义配置

# 以上是自动生成的 #

class DemoProducer(Producer):
	def __init__(self, name = None, **kwargs):
		super().__init__( name=name, **kwargs )

	def handler(self):
		# handler是需要被重写的方法，以下demo每隔0.5秒产生一个数据
		# 并且把数据推送给它的订阅者
		import time
		i = 0
		while ( self._active ):
			i += 1
			event = Event(event_type = '这是Event.type', data = "这是Event.data:{}".format(i) )
			print("DemoProducer:", event.data)
			for q in self._subscriber:
				q.put(event)
			time.sleep(0.5)
