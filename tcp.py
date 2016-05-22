# -*- coding: utf-8 -*-
import logging
from dHydra.app import *
from dHydra.core.Globals import *

def init_loger():
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
	logger = logging.getLogger()
	logger.setLevel(logging.INFO)

	# 屏幕日志打印设置
	console_handler = logging.StreamHandler()
	console_handler.setFormatter(formatter)
	console_handler.setLevel(logging.INFO)
	logger.addHandler(console_handler)

	if not os.path.exists('log'):
		os.makedirs('log')
	# 打开下面的输出到文件
	file_handler = logging.FileHandler('log/error.log')
	file_handler.setLevel(logging.ERROR)
	file_handler.setFormatter(formatter)
	file_handler2 = logging.FileHandler('log/debug.log')
	file_handler2.setLevel(logging.INFO)
	file_handler2.setFormatter(formatter)

	logger.addHandler(file_handler)
	logger.addHandler(file_handler2)

"""
初始化日志
"""
init_loger()

"""
读取数据处理模块(Action)列表
"""
action_list = ['SinaL2TCP']
action_args = {
	"SinaL2TCP": {
		"producer_list" : [
		{
			"name"	  :	"SinaLevel2WS"
		,   "producer_name"	 :   "L2.Quotation"
		,   "query"	 :   ['quotation']
		,	"raw"	 :	True
		}
		]
	,	"addr": "127.0.0.1"
	,	"port": 9999
	}
}

"""
生成Action对象并开启actions
"""
start_action(action_list,action_args)

"""
嗯……只要这样就可以了
"""
