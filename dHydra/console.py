# -*- coding: utf-8 -*-
import logging
from dHydra.core.Functions import *

def init_loger():
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)

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
	file_handler2.setLevel(logging.DEBUG)
	file_handler2.setFormatter(formatter)

	logger.setLevel(logging.INFO)
	logger.addHandler(file_handler)
	logger.addHandler(file_handler2)

def start_worker(worker_name = None, nickname = None, **kwargs):
    msg = { "type":"sys", "operation_name":"start_worker", "kwargs": { "worker_name": worker_name } }
    if nickname is not None:
        msg["kwargs"]["nickname"] = nickname[0]
    for k in kwargs.keys():
        msg["kwargs"][k] = kwargs[k]
    __redis__.publish( "dHydra.Command", msg )

"""
初始化日志
"""
init_loger()
__redis__ = get_vendor("DB").get_redis()
