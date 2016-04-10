# -*- coding: utf8 -*-
"""
全局变量在这里定义
"""
import traceback
import sys
import os

print("加载: Globals.py")
# sys.path.append(sys.path[0])	# 添加workspace的路径(demo.py)
# sys.path.append(os.path.split(os.path.realpath(__file__))[0][0:-5])	# 添加dHydra目录的根路径(app.py)的路径

# producer
PRODUCER_HASH = dict()
PRODUCER_NAME = dict()

actionDict = dict()
