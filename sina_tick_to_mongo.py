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
	console_handler.setLevel(logging.DEBUG)
	logger.addHandler(console_handler)

	if not os.path.exists('log'):
		os.makedirs('log')
	# 打开下面的输出到文件
	file_handler = logging.FileHandler('log/error.log',encoding='utf-8')
	file_handler.setLevel(logging.ERROR)
	file_handler.setFormatter(formatter)
	file_handler2 = logging.FileHandler('log/debug.log',encoding='utf-8')
	file_handler2.setLevel(logging.INFO)
	file_handler2.setFormatter(formatter)

	logger.addHandler(file_handler)
	logger.addHandler(file_handler2)

def main():
	"""
	初始化日志
	"""
	init_loger()

	"""
	读取数据处理模块(Action)列表
	"""
	action_list = ['SinaTickToMongo'] # 只开启一个叫PrintSinaL2的Action用于打印L2到屏幕
	action_args = {
		"SinaTickToMongo": {
			"producer_list": [
				{
					"name" : "SinaFreeQuote"
				,	"producer_name": "Demo.SinaFreeQuote"
				}
			]
		}
	}

	"""
	生成Action对象并开启actions
	"""
	start_action(action_list,action_args)

	"""
	嗯……只要这样就可以了
	"""

if __name__ == "__main__":
	main()
