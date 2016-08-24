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
	file_handler = logging.FileHandler('log/error.log')
	file_handler.setLevel(logging.ERROR)
	file_handler.setFormatter(formatter)
	file_handler2 = logging.FileHandler('log/debug.log')
	file_handler2.setLevel(logging.INFO)
	file_handler2.setFormatter(formatter)

	logger.addHandler(file_handler)
	logger.addHandler(file_handler2)

def main():
	"""
	初始化日志
	"""
	init_loger()

	sina = V("Sina")
	symbols = sina.get_symbols()	# 这里只获取新浪财经A股列表

	"""
	读取数据处理模块(Action)列表
	"""
	action_list = ['SinaL2ToMongo'] # 只开启一个叫PrintSinaL2的Action用于打印L2到屏幕
	action_args = {
		"SinaL2ToMongo": {
			"producer_list" : [
			{
				"name"	  :	"SinaLevel2WS"
			,   "producer_name"	 :   "L2.All"
			,   "query"	 :  ['quotation']	# 这里选择订阅的L2内容，quotation代表行情，deal代表逐笔，orders代表大单 这样['quotation','deal']
			,	"symbols":  symbols
			}
			]
			,"num_min" : 1				# 最低线程数
			,"num_max" : 20				# 最多线程数
			,"lower_threshold" : 0		# 当消息队列数量低于lower_threshold时候，会动态添加
			,"upper_threshold" : 3000	# 当消息队列数量超过upper_threshold时候，会动态添加
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
