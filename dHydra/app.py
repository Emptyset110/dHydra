# -*- coding: utf8 -*-
"""
主控制程序入口
"""
import traceback
import sys
import os

# print("加载：app.py")

from dHydra.core.Globals import *
from dHydra.core.Functions import *

def start_action(actionList, actionArgs = {}):
	for action in actionList:
		if action in actionArgs.keys():
			print(actionArgs[action])
			actionInstance = A(action, **actionArgs[action])
		else:
			actionInstance = A(action)
		actionDict[action] = actionInstance
	for action in actionList:
		actionDict[action].start()
	for action in actionList:
		actionDict[action].join()