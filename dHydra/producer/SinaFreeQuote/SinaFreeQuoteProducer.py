# -*- coding: utf-8 -*-
"""
# Created on 2016/04/12
# @author: Emptyset
# @contact: Emptyset110@gmail.com
"""
# 以下是自动生成的 #
# --- 导入系统配置
from dHydra.app import PRODUCER_NAME, PRODUCER_HASH
import dHydra.core.util as util
from dHydra.core.Producer import Producer
from dHydra.core.Event import Event
from dHydra.config import connection as CON
from dHydra.config import const as C
from dHydra.core.Functions import *
# --- 导入自定义配置

# 以上是自动生成的 #
import threading
import time
import asyncio
import functools
from datetime import datetime

class SinaFreeQuoteProducer(Producer):
	def __init__(self, name = None, symbols = None ,**kwargs):
		super().__init__( name=name, **kwargs )
		self.sina = V('Sina')
		if symbols is None:
			self.symbols = self.sina.get_symbols()
		else:
			self.symbols = symbols
		[self.szSymbols, self.shSymbols] = util.split_symbols(self.symbols)
		self.szTime = datetime(1970,1,1)
		self.shTime = datetime(1970,1,1)

	# 定时器触发的函数
	def thread_target(self, loop):
		asyncio.set_event_loop(loop)
		retry = True
		update = True
		sz = None
		sh = None
		while retry:
			try:
				[ szTime, shTime ] = self.sina.get_ticktime()
				if (szTime > self.szTime) & (len(self.szSymbols)>0):
					self.szTime = szTime
					szUpdate = True
				else:
					szUpdate = False

				if (shTime > self.shTime) & (len(self.shSymbols)>0):
					self.shTime = shTime
					shUpdate = True
				else:
					shUpdate = False
				if szUpdate and shUpdate:
					[ sz ,sh ] = self.sina.get_realtime_quotes( symbols = self.symbols , dataframe=True, loop = loop, split = True )
				elif szUpdate:
					sz = self.sina.get_realtime_quotes( symbols = self.szSymbols , dataframe=True, loop = loop )
				elif shUpdate:
					sh = self.sina.get_realtime_quotes( symbols = self.shSymbols , dataframe=True, loop = loop )
				retry = False
			except Exception as e:
				print(e)
		# print( time.time() - start )
		if sz is not None:
			eventSZ = Event( event_type = 'SinaFreeQuote', data = sz )
			eventSZ.time = szTime
			eventSZ.localtime = time.time()
			eventSZ.exchange = 'SZ'
			for q in self._subscriber:
				q.put(eventSZ)
		if sh is not None:
			eventSH = Event( event_type = 'SinaFreeQuote', data = sh )
			eventSH.time = shTime
			eventSH.localtime = time.time()
			eventSH.exchange = 'SH'
			for q in self._subscriber:
				q.put(eventSH)

	def handler(self):
		while self._active:
			loop = asyncio.new_event_loop()
			t = threading.Thread( target = functools.partial( self.thread_target, loop ) )
			t.start()
			time.sleep(1)
