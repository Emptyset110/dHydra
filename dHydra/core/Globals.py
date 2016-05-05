# -*- coding: utf8 -*-
"""
全局变量在这里定义
"""
import traceback
import sys
import os
import json
# print("加载: Globals.py")

# producer
PRODUCER_HASH = dict()
PRODUCER_NAME = dict()

actionDict = dict()


# 读取配置
f_config = open( os.getcwd() + "/config.json" )
config = json.load( f_config )