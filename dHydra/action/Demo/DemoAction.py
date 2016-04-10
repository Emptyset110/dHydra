# -*- coding: utf8 -*-
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

# 以上是自动生成的 #
class DemoAction(Action):
	def __init__(self, name, **kwargs):
		# 用户自定义自动加载的_producerList
		self._producerList = [
			{	
				"name"	:	"Demo"
			,	"pName"	:	"Demo.Demo"		#这是在action内部给producer起的自定义名字，可随意。一般最好遵守<actionName.producerName>
			}
		]
		# 设置进程检查消息队列的间隔
		self._interval = 0.5
		super().__init__(name, **kwargs)
		print(self._name,"初始化")

	# 需要重写的方法
	def handler(self):

		while not self._queue.empty():
			event = self._queue.get(True)
			print("DemoAction:", event.data)
			# 当收到数字15时，就停止action
			if event.data == 15:
				self._stop()
			
			