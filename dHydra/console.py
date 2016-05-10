# -*- coding: utf8 -*-
import logging
from dHydra.app import *

def init_loger():
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)

	# 屏幕日志打印设置
	consoleHandle = logging.StreamHandler()
	consoleHandle.setFormatter(formatter)
	consoleHandle.setLevel(logging.ERROR)
	logger.addHandler(consoleHandle)

	if not os.path.exists('log'):
		os.makedirs('log')
	# 打开下面的输出到文件
	fileHandler = logging.FileHandler('log/error.log')
	fileHandler.setLevel(logging.ERROR)
	fileHandler.setFormatter(formatter)
	fileHandler2 = logging.FileHandler('log/log.log')
	fileHandler2.setLevel(logging.INFO)
	fileHandler2.setFormatter(formatter)
	
	logger.setLevel(logging.INFO)
	logger.addHandler(fileHandler)
	logger.addHandler(fileHandler2)

"""
初始化日志
"""
init_loger()

