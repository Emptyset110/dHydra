# -*- coding: utf-8 -*-
import logging
from dHydra.app import *

def init_loger():
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)

	# 屏幕日志打印设置
	console_handler = logging.StreamHandler()
	console_handler.setFormatter(formatter)
	console_handler.setLevel(logging.ERROR)
	logger.addHandler(console_handler)

	if not os.path.exists('log'):
		os.makedirs('log')
	# 打开下面的输出到文件
	file_handler = logging.FileHandler('log/error.log')
	file_handler.setLevel(logging.ERROR)
	file_handler.setFormatter(formatter)
	file_handler2 = logging.FileHandler('log/debug.log')
	file_handler2.setLevel(logging.DEBUG)
	file_handler2.setFormatter(formatter)

	logger.setLevel(logging.INFO)
	logger.addHandler(file_handler)
	logger.addHandler(file_handler2)

"""
初始化日志
"""
init_loger()
