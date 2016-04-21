# -*- coding: utf8 -*-
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
from abc import ABCMeta

class Action(threading.Thread):
	__metaclass__ = ABCMeta
	def __init__(self, name, **kwargs):
		super().__init__()
		self.logger = self.get_logger()
		self._name = name
		self._kwargs = kwargs
		self._queue = multiprocessing.Queue()
		self._producers = set()

		# 在子类中被重写
		# self._producerList = []

		# _running决定action是否开启“定时处理”
		# _active决定action是否会执行数据处理过程
		# -----------------------------------
		# 二者既不充分也不必要：
		# 	_running==False & _active==True		: "事件触发"状态
		#	_running==True & _active==True		: "定时触发"状态
		#	_running==True & _active==False		: 定时线程开启但是暂停处理数据
		#	_running==False & _active==False	: Action完全停止
		self._active = False
		self._running = False
		self._auto_load_producers()

	def get_logger(self):
		logger = logging.getLogger(self.__class__.__name__)
		return logger

	# action订阅producer
	def _subscribe(self, instance):
		instance._add_subscriber(queue = self._queue)

	# action取消订阅producer
	def _unsubscribe(self, instance):
		instance._remove_subscriber(queue = self._queue)

	def _activate(self):
		print('[激活Action]\t', self._name)
		self._active = True

	def _deactivate(self):
		self._active = False
		for producer in list(self._producers):
			producer._remove_subscriber(self._queue)
		print('[暂停Action]\t', self._name)

	# 运行action即相当于采用“定时处理”的模式
	def run(self):
		self._auto_start_producers()
		self._running = True
		self._activate()
		print('[开启Action]\t', self._name)
		while self._running:
			if self._active:
				t = threading.Thread( target=self.handler )
				t.start()
				# t.join()
			time.sleep(self._interval)
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
		print('[结束Action]\t', self._name)

	def _stop(self):
		self._running = False

	# action根据self._producerList来自动加载producers
	def _auto_load_producers(self):
		for kwargs in self._producerList:
			instance = P(**kwargs, **self._kwargs)
			self._producers.add( instance )
			self._subscribe(instance)

	def _auto_start_producers(self):
		for producer in list(self._producers):
			if not producer.is_running():
				producer.start()

	# 需要在子类中重写的数据处理方法
	def handler(self):
		pass