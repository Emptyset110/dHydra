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


class SinaLevel2WSProducer(Producer):
	def __init__(self, name = None, username = None, pwd = None,raw = True, symbols = None, query = ['quotation', 'orders', 'deal', 'info'], **kwargs):
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
		self.raw = raw
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
		,	params 	=	PARAM_WSKT_TOKEN(ip=self.ip,qlist=qlist)
		,	headers =	HEADERS_WSKT_TOKEN()
		# ,	verify	=	True
		,	timeout =	5
		) )
		req = yield from async_req
		token = req.text[45:-17]
		return token

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
				token = yield from self.get_ws_token(qlist)
				retry = False
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
		renewToken = threading.Timer(40, util.thread_loop, (loopToken,tasks) )
		renewToken.start()
		self.logger.info("开启线程：{} 为 {} 更新token".format(renewToken.name, threading.current_thread().name) )

		while self._active:
			try:
				message = yield from ws.recv()
				# 如果要的不是原始数据
				if self.raw == False:
					message = self.ws_parse(message = message)

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
			yield from ws.send("*"+oldToken)
			retry = True
			while retry:
				try:
					token = yield from self.get_ws_token(qlist)
					oldToken = token
					retry = False
				except Exception as e:
					yield from ws.send("*"+oldToken)
					self.logger.warning("token获取失败，正重试 %s" % threading.current_thread().name)

			trial = 0
			while trial < 3:
				try:
					yield from ws.send("*"+token)
					yield from asyncio.sleep(40)
				except Exception as e:
					if trial == 2:
						trial += 1
					self.logger.error( "发送token失败, 原因： {} {}".format(e,threading.current_thread().name) )
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


	"""
	用于解析Sina l2的函数
	"""
	def ws_parse(self, message):
		dataList = re.findall(r'(?:((?:2cn_)?((?:sh|sz)[\d]{6})(?:_0|_1|_orders|_i)?)(?:=)(.*)(?:\n))',message)
		result = list()
		for data in dataList:
			if (len(data[0])==12):	# quotation
				wstype = 'quotation'
			elif ( (data[0][-2:]=='_0') | (data[0][-2:]=='_1') ):
				wstype = 'deal'
			elif ( data[0][-6:]=='orders' ):
				wstype = 'orders'
			elif ( (data[0][-2:]=='_i') ):
				wstype = 'info'
			else:
				wstype = 'unknown'
			result = self.ws_parse_to_list(wstype=wstype,symbol=data[1],data=data[2],result=result)
		return result

	def ws_parse_to_list(self,wstype,symbol,data,result):
		data = data.split(',')
		if (wstype == 'deal'):
			for d in data:
				x = list()
				x.append(wstype)
				x.append(symbol)
				x.extend( d.split('|') )
				result.append(x)
		else:
			x = list()
			x.append(wstype)
			x.append(symbol)
			x.extend(data)
			result.append(x)
		return result

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