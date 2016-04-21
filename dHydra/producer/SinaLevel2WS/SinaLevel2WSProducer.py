# -*- coding: utf8 -*-
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

# 如果是标准版用户可以设置hq = 'A_hq'
class SinaLevel2WSProducer(Producer):
	def __init__(self, name = None, username = None, pwd = None, hq = 'hq_pjb', symbols = None, query = ['quotation', 'orders', 'deal', 'info'], **kwargs):
		super().__init__( name=name, **kwargs )
		if (username == None):
			self.username = input('请输入新浪登录帐号：')
		else:
			self.username=username
		if (pwd == None):
			self.pwd = getpass.getpass("输入登录密码（密码不会显示在屏幕上，输入后按回车确定）:")
		else:
			self.pwd = pwd
		self.rsaPubkey = '10001'
		self.ip = util.get_client_ip()
		self.session = requests.Session()
		a = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=100)
		self.session.mount("https://",a)
		self.isLogin = self.login()

		self.hq = hq
		self.query = query
		if symbols is None:
			sina = V('Sina')
			self.symbols = sina.get_symbols()
		else:
			self.symbols = symbols

	def login(self):
		self.session.get("http://finance.sina.com.cn/realstock/company/sz300204/l2.shtml")
		su = base64.b64encode(self.username.encode('utf-8'))

		preLogin = self.session.get( URL_PRELOGIN, params = PARAM_PRELOGIN( su ), headers = HEADERS_LOGIN)
		preLogin = json.loads( preLogin.text[len("sinaSSOController.preloginCallBack("):-1] )

		sp = self.get_sp( self.pwd, preLogin["pubkey"], int(preLogin["servertime"]), preLogin["nonce"] )

		self.loginResponse = self.session.post(
			URL_SSOLOGIN
		,	params = PARAM_LOGIN()
		,	data = DATA_LOGIN(
				su = su
			,	servertime = int( preLogin["servertime"] )
			,	nonce = preLogin["nonce"]
			,	rsakv = preLogin["rsakv"]
			,	sp = sp
			)
		,	headers = HEADERS_LOGIN
		)
		if (self.loginResponse.json()["retcode"]=='0'):
			print( "登录成功: %s, uid = %s" % ( self.loginResponse.json()["nick"], self.loginResponse.json()["uid"]) )

			i = 0
			for url in self.loginResponse.json()["crossDomainUrlList"]:
				req = self.session.get( url,headers = HEADERS_CROSSDOMAIN( CROSSDOMAIN_HOST[i] ) )
				i += 1
			return True
		else:
			print( "Authentication Failed..." )
			print( self.loginResponse.json() )
			return False

	# RSA2 encoding
	def get_sp(self, passwd, pubkey, servertime, nonce):
		key = rsa.PublicKey(int(pubkey, 16), int('10001', 16))
		message = str(servertime) + '\t' + str(nonce) + '\n' + str(passwd)
		passwd = rsa.encrypt(message.encode('utf-8'), key)
		return binascii.b2a_hex(passwd).decode('ascii')

	@asyncio.coroutine
	def get_ws_token(self,qlist):
		loop = asyncio.get_event_loop()
		async_req = loop.run_in_executor(None, functools.partial( self.session.get, 
			URL_WSKT_TOKEN
		,	params 	=	PARAM_WSKT_TOKEN(ip=self.ip,qlist=qlist, hq = self.hq)
		,	headers =	HEADERS_WSKT_TOKEN()
		,	timeout =	10
		) )
		req = yield from async_req
		self.logger.info(req.text)
		response = re.findall(r'(\{.*\})',req.text)[0]
		response = json.loads( response.replace(',',',"').replace('{','{"').replace(':','":') )
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
			qlist += "2cn_%s_i" % (symbol)		
		return qlist

	@asyncio.coroutine
	def create_ws(self, qlist, symbol, loop ):
		asyncio.set_event_loop(loop)
		retry = True
		while retry:
			try:
				response = yield from self.get_ws_token(qlist)
				if response["msg_code"] == 1:
					token = response["result"]
					retry = False
				else:
					self.logger.error(response["result"])
			except Exception as e:
				self.logger.warning(e)

		url_wss = 'wss://ff.sinajs.cn/wskt?token=' + token + '&list=' + qlist

		start = datetime.now()
		retry = True
		while retry:
			try:
				ws = yield from websockets.connect(url_wss)
				retry = False
			except Exception as e:
				self.logger.warning("重试 websockets.connect , %s " % threading.current_thread().name )

		# 另开一个线程每40秒更新一次token，新建一个event_loop防止这个操作阻塞websocket
		loopToken = asyncio.new_event_loop()
		tasks = [ self.renew_token(ws, qlist, token) ]
		renewToken = threading.Timer(20, util.thread_loop, (loopToken,tasks) )
		renewToken.start()
		self.logger.info("开启线程：{} 为 {} 更新token".format(renewToken.name, threading.current_thread().name) )

		while self._active:
			try:
				message = yield from ws.recv()
				# 如果要的不是原始数据
				event = Event(eventType = 'SinaLevel2WS', data = message)
				
				for q in self._subscriber:
					q.put(event)

			except Exception as e:
				self.logger.error("{},{}".format(e, threading.current_thread().name) )
				ws.close()
				yield from self.create_ws(qlist = qlist,symbol = symbol,loop=loop)
	
	"""
	用于更新token的coroutine
	"""
	@asyncio.coroutine
	def renew_token(self, ws, qlist, oldToken):
		while True:
			yield from ws.send("")
			self.logger.info("websocket Send:")
			retry = True
			while retry:
				try:
					response = yield from self.get_ws_token(qlist)
					if response["msg_code"] == 1:
						token = response["result"]
						retry = False
					else:
						self.logger.info(response["result"])
						yield from ws.send("")
						self.logger.info("Sent:")
				except Exception as e:
					yield from ws.send("")
					self.logger.info("Sent:")
					self.logger.warning("token获取失败，正重试 %s" % threading.current_thread().name)

			trial = 0
			while trial < 3:
				try:
					yield from ws.send("*"+token)
					self.logger.info("Sent:*"+token)
					yield from asyncio.sleep(40)
				except ConnectionClosed as e:
					if trial == 2:
						trial += 1
					self.logger.error( "发送token失败第{}次, 原因： {} {}".format(trial,e,threading.current_thread().name) )
				trial += 1
			if trial == 4:	#说明3次发送都失败了，目测是websocket也关闭了，因此这个线程没有继续运行的必要了
				break

	"""
	供线程调用的开启新浪WebSocket的方法
	"""
	def start_ws(self, symbolList = None, loop = None ):
		asyncio.set_event_loop(loop)
		qlist = ''
		for symbol in symbolList:
			qlist = self.generate_qlist(qlist=qlist,symbol=symbol)

		qlist = qlist.lower()
		if loop.is_running():
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop( loop )
		loop.run_until_complete( self.create_ws(qlist,symbol=symbol, loop=loop) )
		loop.close()

	def handler(self):
		# 首先从新浪获取股票列表
		symbolList = self.symbols
		# symbolList = ['SZ300204,SZ000001']
		threads = []
		# Cut symbolList
		weight = (len(self.query)+1) if ('deal' in self.query) else len(self.query)
		step = int(64/weight)
		symbolListSlice = [symbolList[ i : i + step] for i in range(0, len(symbolList), step)]
		for symbolList in symbolListSlice:
			loop = asyncio.new_event_loop()
			t = threading.Thread(target = self.start_ws,args=(symbolList,loop) )
			threads.append(t)
		for t in threads:
			t.setDaemon(True)
			t.start()
			self.logger.info("开启线程： %s" % t.name)
			time.sleep(0.3)		# 开启线程的时候温柔一点，因为每个线程都会发出获取token的请求，挤在一起容易出错
		for t in threads:
			t.join()