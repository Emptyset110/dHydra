# -*- coding: utf-8 -*-
"""
Action类
每个Action自带一个Queue
Created on 03/30/2016
@author: Wen Gu
@contact: emptyset110@gmail.com
"""
import multiprocessing
import threading
import time
import logging
import redis
import pymongo
import json
# from dHydra.core.Globals import *
# from dHydra.core.Functions import *
# from dHydra.app import PRODUCER_NAME, PRODUCER_HASH
# import dHydra.core.ThreadManager as ThreadManager
# import dHydra.core.util as util
from abc import ABCMeta

class Worker(multiprocessing.Process):
	__metaclass__ = ABCMeta
	def __init__(	self
				,	singleton = True	# 单例模式
				,	name = "Default"	# Worker的自定义名字
				,	description = "No Description"	# 备注说明
				,	log_level = "INFO" # "DEBUG","INFO","WARNING"
				,	heart_beat_interval = 3	# 默认3秒心跳
				,	**kwargs
				):
		self.__name__ = name
		self.__singleton__ = singleton
		self.__description__ = description
		self.__heart_beat_interval__ = heart_beat_interval
		self.__threads__ = dict()	# 被监控的线程
		"""
		self.__threads__ = {
			"description"	: "该线程功能备注说明",
			"name"			: "该线程的名字",
			"target"		: "该线程的target"
			"restart_mode"	: "重启模式，可以为 manual/auto/remove;manual则代表允许管理员发送命令手工重启线程,auto则一旦线程关闭立即自动开启，remove则代表一旦线程结束就从监控列表移除",
			"restart_func"	: "自动/手动重启时调用的方法",

		}
		"""
		self.logger = self.get_logger( level = log_level )
		if self.check_prerequisites() is True:
			super().__init__()
		else:
			exit(0)

	def __auto_restart_thread__( self ):
		# Worker内置的默认自动重启线程方法

	def command_handler(self, cli):
		# cli


	def monitor_add_thread( self, thread, description = "No Description", restart_mode = "manual", restart_func = self.__auto_restart_thread__ ):
		# 将该线程加入管理员监控范围

	def monitor_remove_thread(self, thread):
		# 取消管理员对线程thread的监控

	def check_prerequisites(self):
		"""
		检查是否满足开启进程的条件
		"""
		# 检测redis, mongodb连接

		# 如果是单例，检测是否重复开启
		return True

	def __heart_beat__(self):
		# 心跳线程
		while True:
			time.sleep(self.__heart_beat_interval__)


	def run(self):
		"""
		初始化Worker
		"""
		# 开启心跳线程，并且加入线程监控
		self.__thread_heart_beat__ = threading.Thread( target = self.__heart_beat__ )
		self.__thread_heart_beat__.setDaemon(True)
		self.monitor_add_thread( thread = self.__thread_heart_beat__, description = "Heart Beat", restart_mode = "auto", restart_func = self.__thread_auto_restart__ )
		self.__thread_heart_beat__.start( restart_mode = "auto", restart_func = self.__thread_auto_restart__ )

		# 开启监听命令线程
		self.__thread_listen_command__ = threading.Thread( target =  )

		# 检查初始化设置，按需开启
		#### PUB线程

	def get_logger(self, level):
		logger = logging.getLogger(self.__class__.__name__)
		if level is "DEBUG":
			logger.setLevel(10)
		elif level is "INFO":
			logger.setLevel(20)
		elif level is "WARNING":
			logger.setLevel(30)
		elif level is "ERROR":
			logger.setLevel(40)
		elif level is "CRITICAL":
			logger.setLevel(50)
		else:
			logger.setLevel(20)
		return logger


	def subscribe(self, worker_name):
		"""
		订阅Worker
		"""
		# Step 1 : 检查Worker是否存在
		# Step 2 : 检查Worker是否开启


	def unsubscribe(self, worker_name):
		"""
		退订Worker
		"""



	def _end(self):
		for producer in list(self._producers):
			producer._remove_subscriber(self._queue)
		self.logger.info('[结束Action]\t{}'.format( self._name ) )

	def _stop(self):
		self._running = False

	# 需要在子类中重写的数据处理方法
	def handler(self, event):
		print( "event.data: {}".format( event.data ) )
		return
