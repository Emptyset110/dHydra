# -*- coding: utf-8 -*-
# 以下是自动生成的 #
# --- 导入系统配置
from dHydra.app import PRODUCER_NAME, PRODUCER_HASH
import dHydra.core.util as util
from dHydra.core.Producer import Producer
from dHydra.core.Event import Event
from dHydra.config import connection as CON
from dHydra.config import const as C
from dHydra.core.Functions import *
from dHydra.core.Globals import *
# --- 导入自定义配置
from .connection import *
from .const import *
from .config import *
# 以上是自动生成的 #
from datetime import datetime
import time
import requests
import websockets
import getpass
import base64,rsa,binascii
import json
import asyncio
import threading
import functools
import re
import gc
import os

class SinaLevel2WSProducer(Producer):
	def __init__(self, name = None, username = None, pwd = None, symbols = None, hq = 'hq_pjb', query = ['quotation', 'orders', 'deal', 'info'], **kwargs):
		super().__init__( name=name, **kwargs )
		self.ip = util.get_client_ip()
		self.hq = hq
		self.query = query
		# 登录模块在V('Sina')中
		self.sina = V('Sina')
		self.is_login = self.login()
		if symbols is None:
			self.symbols = self.sina.get_symbols()
		else:
			self.symbols = symbols
		self.websockets = dict()

	def login(self, verify = False):
		return self.sina.login(verify = verify)

	@asyncio.coroutine
	def get_ws_token(self,qlist):
		loop = asyncio.get_event_loop()
		async_req = loop.run_in_executor(None, functools.partial( self.sina.session.get,
			URL_WSKT_TOKEN
		,	params 	=	PARAM_WSKT_TOKEN(ip=self.ip,qlist=qlist, hq = self.hq)
		,	headers =	HEADERS_WSKT_TOKEN()
		,	timeout =	5
		) )
		req = yield from async_req
		self.logger.info(req.text)
		response = re.findall(r'(\{.*\})',req.text)[0]
		response = json.loads( response.replace(',',',"').replace('{','{"').replace(':','":') )
		gc.collect()
		return response

	# 2cn_是3秒一条的Level2 10档行情
	# 2cn_symbol_0,2cn_symbol_1是逐笔数据
	# 2cn_symbol_orders是挂单数据
	# symbol_i是基本信息
	def generate_qlist(self,qlist,symbol):
		if 'quotation' in self.query:
			if qlist!='':
				qlist += ','
			qlist += "2cn_%s" % (symbol)
		if 'orders' in self.query:
			if qlist!='':
				qlist += ','
			qlist += "2cn_%s_orders" % (symbol)
		if 'deal' in self.query:
			if qlist!='':
				qlist += ','
			qlist += "2cn_%s_0,2cn_%s_1" % (symbol, symbol)
		if 'info' in self.query:
			if qlist!='':
				qlist += ','
			qlist += "%s_i" % (symbol)
		return qlist

	@asyncio.coroutine
	def create_ws(self, qlist, symbolList ):
		retry = True
		while retry:
			try:
				response = yield from self.get_ws_token(qlist)
				if response["msg_code"] == 1:
					token = response["result"]
					self.logger.info("成功获取到token, symbolList = {}".format(symbolList) )
					retry = False
				else:
					self.logger.info(response["result"])
			except Exception as e:
				self.logger.warning(e)

		url_wss = 'wss://ff.sinajs.cn/wskt?token=' + token + '&list=' + qlist

		while True:	# 建立websocket连接
			try:
				ws = yield from websockets.connect(url_wss)
				self.websockets[ symbolList[0] ] = dict()
				self.websockets[ symbolList[0] ]["ws"] = ws
				self.websockets[ symbolList[0] ]["qlist"] = qlist
				self.websockets[ symbolList[0] ]["token"] = token
				self.websockets[ symbolList[0] ]["renewed"] = datetime.now()
				self.websockets[ symbolList[0] ]["trialTime"] = 0
				self.logger.info("成功建立ws连接, {}, symbolList = {}".format(threading.current_thread().name, symbolList))
				break
			except Exception as e:
				self.logger.warning("重试 websockets.connect , {}, symbolList = {}".format(threading.current_thread().name, symbolList) )

		while self._active:
			try:
				message = yield from ws.recv()
				event = Event(event_type = 'SinaLevel2WS', data = message)

				for q in self._subscriber:
					q.put(event)
					# print( "Producer:\n{},{}".format( event.data,datetime.now() ) )

			except Exception as e:
				self.logger.error("{},{}".format(e, threading.current_thread().name) )
				ws.close()
				yield from self.create_ws(qlist = qlist, symbolList = symbolList)

	@asyncio.coroutine
	def renew_token(self, symbol):
		try:
			response = yield from self.get_ws_token( self.websockets[ symbol ]["qlist"] )
			if response["msg_code"] == 1:
				token = response["result"]
				self.websockets[ symbol ]["token"] = token
				self.websockets[ symbol ]["renewed"] = datetime.now()
				yield from self.websockets[ symbol ]["ws"].send("*"+token)
				self.websockets[ symbol ]["trialTime"] = 0
			else:
				self.websockets[ symbol ]["trialTime"] += 1
				self.logger.info(response["result"])
		except Exception as e:
			self.websockets[ symbol ]["trialTime"] += 1
			self.logger.warning("token获取失败第{}次，待会儿重试".format( self.websockets[ symbol ]["trialTime"] ))
		gc.collect()


	def websocket_creator(self):
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		# 首先从新浪获取股票列表
		symbolList = self.symbols
		# Cut symbolList
		weight = (len(self.query)+1) if ('deal' in self.query) else len(self.query)
		step = int(64/weight)
		symbolListSlice = [symbolList[ i : i + step] for i in range(0, len(symbolList), step)]

		tasks = list()
		for symbolList in symbolListSlice:
			qlist = ''
			for symbol in symbolList:
				qlist = self.generate_qlist(qlist=qlist,symbol=symbol)
			qlist = qlist.lower()
			tasks.append( self.create_ws(qlist,symbolList = symbolList) )

		loop.run_until_complete( asyncio.wait(tasks) )
		loop.close()

	# 用于定时发送空字符串
	def token_sender(self):
		while True:
			self.logger.info("开启话唠模式每55秒的定时与服务器聊天")
			start = datetime.now()
			tasks = list()
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop(loop)

			for symbol in self.websockets.keys():
				ws = self.websockets[ symbol ]["ws"]
				if ws.open:
					tasks.append( ws.send("*"+self.websockets[symbol]["token"]) )

			if len(tasks)>0:
				loop.run_until_complete( asyncio.wait(tasks) )
				loop.close()
			self.logger.info("消息全部发送完毕. 耗时：%s" % (datetime.now()-start).total_seconds() )
			time.sleep(55)

	# 持续检查一次更新token
	def token_renewer(self):
		while True:
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop(loop)
			tasks = list()
			for symbol in self.websockets.keys():
				ws = self.websockets[ symbol ]["ws"]
				if ws.open:
					if (datetime.now()-self.websockets[ symbol ]["renewed"]).total_seconds()>180:
						tasks.append( self.renew_token( symbol ) )

			if len(tasks)>0:
				loop.run_until_complete( asyncio.wait(tasks) )
				loop.close()
			time.sleep(1)
			gc.collect()


	def handler(self):
		# 开启token manager
		tokenRenewer = threading.Thread( target = self.token_renewer )
		tokenSender = threading.Thread( target = self.token_sender )

		websocketCreator = threading.Thread( target = self.websocket_creator )

		tokenRenewer.start()		# 用于更新token
		tokenSender.start()			# 用于定时发送token
		websocketCreator.start()	# 用于建立websocket并接收消息

		tokenRenewer.join()
		tokenSender.join()
		websocketCreator.join()
