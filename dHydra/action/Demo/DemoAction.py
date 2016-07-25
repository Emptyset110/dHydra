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

# 以上是自动生成的 #
class DemoAction(Action):
	def __init__(self, name, **kwargs):
		super().__init__(name, **kwargs)
		print(self._name,"初始化")

	# 需要重写的方法
	def handler(self, event):
		print("DemoAction:", event.data)
