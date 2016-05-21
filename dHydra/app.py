# -*- coding: utf-8 -*-
"""
主控制程序入口
"""
import traceback
import sys
import os

# print("加载：app.py")

from dHydra.core.Globals import *
from dHydra.core.Functions import *

def start_action(action_list, action_args = {}):
	for action in action_list:
		if action in action_args.keys():
			print(action_args[action])
			actionInstance = A(action, **action_args[action])
		else:
			actionInstance = A(action)
		action_dict[action] = actionInstance
	for action in action_list:
		action_dict[action].start()
	for action in action_list:
		action_dict[action].join()