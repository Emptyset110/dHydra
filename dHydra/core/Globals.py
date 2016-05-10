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
try:
	f_config = open( os.getcwd() + "/config.json" )
	config = json.load( f_config )
except Exception as e:
	print( "未能正确加载{}，请检查路径，json文档格式，或者\n可以忽略此警告（当不采用config.json来配置账号时）".format( os.getcwd() + "/config.json" ) )