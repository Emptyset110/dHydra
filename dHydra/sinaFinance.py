# -*- coding: utf8 -*-
"""
新浪接口：
 1. 模拟登录
 2. WebSocket接口获取实时推送
"""
from datetime import datetime, timedelta
import requests
import pandas as pd
import base64,binascii,rsa,json,time,logging,threading
import os
import websockets
import functools
from . import util
from .config import connection as CON
import asyncio
import getpass
import threading
import gc
import re

class SinaFinance:
	def __init__(self, username=None, pwd=None):
		if (username == None):
			self.username = input('请输入新浪登录帐号：')
		else:
			self.username=username
		if (pwd == None):
			self.pwd = getpass.getpass("输入登录密码（密码不会显示在屏幕上，输入后按回车确定）:")
		else:
			self.pwd = pwd
		self.rsaPubkey = '10001'
		self.ip = util._get_public_ip()
		self.session = requests.Session()
		self.isLogin = self.login()

	def login(self):
		self.session.get("http://finance.sina.com.cn/realstock/company/sz300204/l2.shtml")
		su = base64.b64encode(self.username.encode('utf-8'))

		preLogin = self.session.get(CON.URL_PRELOGIN, params = CON.PARAM_PRELOGIN( su ), headers = CON.HEADERS_LOGIN)
		preLogin = json.loads( preLogin.text[len("sinaSSOController.preloginCallBack("):-1] )

		sp = self.get_sp( self.pwd, preLogin["pubkey"], int(preLogin["servertime"]), preLogin["nonce"] )

		self.login = self.session.post(
			CON.URL_SSOLOGIN
		,	params = CON.PARAM_LOGIN()
		,	data = CON.DATA_LOGIN(
				su = su
			,	servertime = int( preLogin["servertime"] )
			,	nonce = preLogin["nonce"]
			,	rsakv = preLogin["rsakv"]
			,	sp = sp
			)
		,	headers = CON.HEADERS_LOGIN
		)
		if (self.login.json()["retcode"]=='0'):
			print( "登录成功: %s, uid = %s" % ( self.login.json()["nick"], self.login.json()["uid"]) )

			i = 0
			for url in self.login.json()["crossDomainUrlList"]:
				req = self.session.get( url,headers = CON.HEADERS_CROSSDOMAIN(CON.CROSSDOMAIN_HOST[i]) )
				# print(req.text)
				i += 1
			return True
		else:
			print( "Authentication Failed..." )
			print( self.login.json() )
			return False

	
	# RSA2 encoding
	def get_sp(self, passwd, pubkey, servertime, nonce):
		key = rsa.PublicKey(int(pubkey, 16), int('10001', 16))
		message = str(servertime) + '\t' + str(nonce) + '\n' + str(passwd)
		passwd = rsa.encrypt(message.encode('utf-8'), key)
		return binascii.b2a_hex(passwd).decode('ascii')

	# 获取单股票逐笔数据
	@asyncio.coroutine
	def l2_hist(self, symbol, date, loop):
		global totalCount
		start = datetime.now()
		if not(os.path.exists('data/stock_l2/%s/%s.csv' % (date,symbol) )):
			nextPage = True
			page = 1
			l2 = list()
			while (nextPage):
				async_req = loop.run_in_executor(None, functools.partial( self.session.get
					,	CON.URL_L2HIST
					,	params = CON.PARAM_L2HIST(symbol=symbol, page=page)
					,	headers = CON.HEADERS_L2(symbol=symbol)
				) )
				req = yield from async_req
				data = req.text[90:-2]
				data = dict( json.loads(data) )
				count = int( data["result"]["data"]["count"] )
				if ( data["result"]["data"]["data"] is not None ):
					l2.extend(data["result"]["data"]["data"])
				del req
				del data
				del async_req
				if ( len(l2) == count ):
					nextPage = False
				page+=1
			l2df = pd.DataFrame( l2 )
			del l2
			l2df = l2df.convert_objects(convert_dates=False,convert_numeric=True,convert_timedeltas=False)
			if not(len(l2df)==0):
				l2df = l2df.set_index("index").sort_index("index")
			totalCount += 1
			l2df.to_csv('data/stock_l2/%s/%s.csv' % (date,symbol) )
			del l2df
		print( "symbol = ",symbol, " 已完成： ", totalCount )
		return True

	# 获取逐笔数据
	def l2_hist_list(self, symbolList=None,loop=None):
		global totalCount
		totalCount = 0

		if loop is None:
			loop = asyncio.new_event_loop()

		asyncio.set_event_loop(loop)
		if (datetime.now().hour<8):
			date = str(datetime.now().date()-timedelta(days=1))
		else:
			date = str(datetime.now().date())
		os.makedirs( './data/stock_l2/%s' % date,exist_ok=True )
		print('已经创建目录./data/stock_l2/%s, 将在此目录下生成csv' % date)
		tasks = list()
		for symbol in symbolList:
			tasks.append( self.l2_hist( symbol,date,loop ) )
		step = 30
		taskList = [tasks[ i : i + step] for i in range(0, len(tasks), step)]
		for task in taskList:
			loop.run_until_complete( asyncio.wait(task) )
		loop.close()


	@asyncio.coroutine
	def get_ws_token(self,qlist,symbol):
		loop = asyncio.get_event_loop()
		async_req = loop.run_in_executor(None, functools.partial( self.session.get, 
			CON.URL_WSKT_TOKEN
		,	params 	=	CON.PARAM_WSKT_TOKEN(ip=self.ip,qlist=qlist)
		,	headers =	CON.HEADERS_WSKT_TOKEN()
		,	verify	=	True
		) )
		req = yield from async_req
		token = req.text[45:-17]
		return token

	# 2cn_是3秒一条的Level2 10档行情
	# 2cn_symbol_0,2cn_symbol_1是逐笔数据
	# 2cn_symbol_orders是挂单数据
	# symbol_i是基本信息
	def generate_qlist(self,qlist,symbol):
		if qlist == '':
			qlist = "2cn_%s,2cn_%s_0,2cn_%s_1,%s,%s_i,2cn_%s_orders" % (symbol,symbol,symbol,symbol,symbol,symbol)
		else:
			qlist = qlist + ',' + "2cn_%s,2cn_%s_0,2cn_%s_1,%s,%s_i,2cn_%s_orders" % (symbol,symbol,symbol,symbol,symbol,symbol)
		return qlist

	def send(self, message, ws ):
		print( "> {}".format(message) )
		yield from ws.send(message)

	"""
	TODO: 目前websocket断开后的逻辑是重连。需要保持连接不断的逻辑与无缝重连的逻辑。
	"""
	@asyncio.coroutine
	def create_ws(self, qlist, symbol, loop, callback = None, raw = False ):
		asyncio.set_event_loop(loop)
		token = yield from self.get_ws_token(qlist,symbol)

		url_ws = 'ws://ff.sinajs.cn/wskt?token=' + token + '&list=' + qlist
		url_wss = 'wss://ff.sinajs.cn/wskt?token=' + token + '&list=' + qlist

		# print("BEGINNING OF websockets.connect")
		start = datetime.now()
		ws = yield from websockets.connect(url_wss)
		while True:
			try:
				message = yield from ws.recv()
				if raw == False:
					message = self.ws_parse(message = message)
				if (callback is None):
					callback = self.print_websocket
				yield from callback(message)
				del message
				# print( "About to send: {}".format("*"+token) )
				# t = threading.Timer(30, self.send(message="*"+token, ws=ws) )
			except Exception as e:
				print(e)
				ws.close()
				yield from self.create_ws(qlist = qlist,symbol = symbol,loop=loop, callback = callback, raw=raw)
	
	@asyncio.coroutine
	def print_websocket(self, message):
		print( "< {}".format(message) )
		del message
		return True

	# @asyncio.coroutine
	# def print_websocket_df(self, message):
	# 	df = pd.DataFrame.from_records(message)
	# 	print(df)

	def start_ws(self, symbolList = None, loop = None, callback = None, raw = False ):
		asyncio.set_event_loop(loop)
		qlist = ''
		for symbol in symbolList:
			qlist = self.generate_qlist(qlist=qlist,symbol=symbol)

		if loop.is_running():
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop( loop )
		loop.run_until_complete( self.create_ws(qlist,symbol=symbol, loop=loop, callback=callback, raw = raw) )
		loop.close()

	def ws_parse(self, message):
		dataList = re.findall(r'(?:((?:2cn_)?((?:sh|sz)[\d]{6})(?:_0|_1|orders|_i)?)(?:=)(.*)(?:\n))',message)
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