# -*- coding: utf-8 -*-
"""
Action类
每个Action自带一个Queue
Created on 03/30/2016
@author: Wen Gu
@contact: emptyset110@gmail.com
"""
import multiprocessing
import time
import threading
import logging
from dHydra.core.Globals import *
from dHydra.core.Functions import *
from dHydra.app import PRODUCER_NAME, PRODUCER_HASH
import dHydra.core.ThreadManager as ThreadManager
import dHydra.core.util as util
from abc import ABCMeta

class Action(threading.Thread):
	__metaclass__ = ABCMeta
	def __init__(	self
				,	name = None
				,	producer_list = list()
				,	num_start = 1
				,	num_min = 1
				,	num_max = 10
				,	need_new_thread = None
				,	cancel_thread = None
				,	on_finished = None
				,	set_daemon = True
				,	lower_threshold = 0
				,	upper_threshold = 3000	# 当消息队列数量超过upper_threshold时候，会动态添加
				,	log_level = "INFO" # "DEBUG","INFO","WARNING"
				,	**kwargs
				):
		super().__init__()
		self.logger = self.get_logger( level = log_level )
		self._name = name
		self._kwargs = kwargs
		self._queue = multiprocessing.Queue()
		self._producers = set()
		self._lock = multiprocessing.Lock()
		self._producer_list = producer_list

		self.lower_threshold = lower_threshold
		self.upper_threshold = upper_threshold

		self._manager = ThreadManager.Manager(	target = self.thread_target
											,   set_daemon = set_daemon				# 将线程设置为守护线程
											,   num_start = num_start				# 初始化action时候一次性创建的线程数
											,   num_min = num_min					# 允许最少用于执行handler的线程数
											,   num_max = num_max					# 允许用于执行handler最多线程数
											,   need_new_thread = self.need_new_thread	# 用于判断是否需要增加线程的函数，默认
											,   cancel_thread = self.cancel_thread		# 用于需要减少线程的判断函数，默认为
											,   on_finished = self.handler_callback		# handler的回调函数
											)

		# _running决定action是否开启“定时处理”
		# _active决定action是否会执行数据处理过程
		# -----------------------------------
		# 二者既不充分也不必要：
		# 	_running==False & _active==True		: "事件触发"状态
		#	_running==True & _active==True		: "定时触发"状态
		#	_running==True & _active==False		: 定时线程开启但是暂停处理数据
		#	_running==False & _active==False	: Action完全停止
		self._active = False		# _active表示：是否处理数据
		self._running = False		# _running表示：( Deprecated ) Action是否开启，这个flag无用
		self.mutex = threading.Lock()
		self._auto_load_producers()
		# 开启定时打印消息队列堆积数据量的线程
		t = threading.Thread(target=self.log_queue)
		t.setDaemon(True)
		t.start()

	def log_queue(self):
		while True:
			self.logger.debug( "消息队列中消息数量: {}".format( self._queue.qsize() ) )
			time.sleep(10)

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

	def handler_callback( self, result ):
		return None
		# print( result )

	def need_new_thread( self ):
		"""
		需要动态新增线程的判断函数
		--------
		return:	True/False
		"""
		if (self._queue.qsize() > self.upper_threshold):
			self.logger.info( "消息队列中消息数量: {}, 需要增加线程".format( self._queue.qsize() ) )
			return True
		else:
			return False

	# 需要减少线程的判断函数
	def cancel_thread( self ):
		"""
		需要动态减少线程的判断函数
		-------
		return:	True/False
		"""
		if ( self._queue.qsize() < self.lower_threshold ):
			self.logger.debug( "消息队列中消息数量: {}, 需要减少线程".format( self._queue.qsize() ) )
			return True
		else:
			return False

	# action订阅producer
	def _subscribe(self, instance):
		instance._add_subscriber(queue = self._queue)

	# action取消订阅producer
	def _unsubscribe(self, instance):
		instance._remove_subscriber(queue = self._queue)

	def _activate(self):
		self.logger.info('[激活Action]\t{}'.format( self._name ) )
		self._active = True

	def _deactivate(self):
		self._active = False
		for producer in list(self._producers):
			producer._remove_subscriber( self._queue )
		self.logger.info( '[暂停Action]\t{}'.format( self._name ) )

	# 运行action即相当于采用“定时处理”的模式
	def run(self):
		self._auto_start_producers()
		self._running = True
		self._activate()
		self.logger.info('[开启Action]\t{}'.format( self._name ) )
		self._manager.start()
		while self._running is True:
			if self._active is True:
				time.sleep(3)
		self._end()

	def is_active(self):
		return self._active

	def is_running(self):
		return self._running

	# 通知action进行一次数据处理，这是“事件触发”的模式
	def _notify(self):
		self._handler()

	def _end(self):
		for producer in list(self._producers):
			producer._remove_subscriber(self._queue)
		self.logger.info('[结束Action]\t{}'.format( self._name ) )

	def _stop(self):
		self._running = False

	# action根据self._producer_list来自动加载producers
	def _auto_load_producers(self):
		for kwargs in self._producer_list:
			instance = P(**kwargs)
			self._producers.add( instance )
			self._subscribe(instance)

	def _auto_start_producers(self):
		for producer in list(self._producers):
			if not producer.is_running():
				producer.start()

	def thread_target(self):
		try:
			event = self._queue.get(True, timeout = 10)
			result =self.handler(event = event)
			return result
		except Exception as e:
			# self.logger.error("{}".format(e) )
			return None

	# 需要在子类中重写的数据处理方法
	def handler(self, event):
		print( "event.data: {}".format( event.data ) )
		return
