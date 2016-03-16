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
	def l2_hist(self, symbol, date):
		# Start timing!
		global totalCount
		start = datetime.now()
		loop = asyncio.get_event_loop()
		if not(os.path.exists('data/stock_l2/%s/%s.csv' % (date,symbol) )):
			nextPage = True
			page = 1
			while (nextPage):
				async_req = loop.run_in_executor(None, functools.partial( self.session.get
					,	CON.URL_L2HIST
					,	params = CON.PARAM_L2HIST(symbol=symbol, page=page)
					,	headers = CON.HEADERS_L2(symbol=symbol)
				) )
				req = yield from async_req
				# print(req.url)
				data = req.text[90:-2]
				data = dict( json.loads(data) )
				count = data["result"]["data"]["count"]
				
				if (page==1):
					l2 = pd.DataFrame(data["result"]["data"]["data"])
				else:
					l2 = l2.append(pd.DataFrame(data["result"]["data"]["data"]), ignore_index=True)

				if (str(len(l2))==count):
					nextPage = False
				page+=1
			l2 = l2.convert_objects(convert_dates=False,convert_numeric=True,convert_timedeltas=False)
			if not(len(l2)==0):
				l2 = l2.set_index("index").sort_index("index")
			totalCount += 1
			print( "symbol = ",symbol, " 已完成： ", totalCount )
			l2.to_csv('data/stock_l2/%s/%s.csv' % (date,symbol) )
			# print( "Count: ",count )
			# print( "Time Cost: ", datetime.now() - start )

	# 获取逐笔数据
	def l2_hist_list(self, symbolList,loop):
		global totalCount
		totalCount = 0
		if (datetime.now().hour<7):
			date = str(datetime.now().date()-timedelta(days=1))
		else:
			date = str(datetime.now().date())
		os.makedirs( './data/stock_l2/%s' % date,exist_ok=True )
		print('已经创建目录./data/stock_l2/%s, 将在此目录下生成csv' % date)
		tasks = list()
		for symbol in symbolList:
			tasks.append( self.l2_hist(symbol,date) )

		if loop.is_running():
			loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		loop.run_until_complete( asyncio.wait(tasks) )

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
		# print( "token = ", req.text[45:-17] )
		token = req.text[45:-17]
		return token

	# 2cn_是3秒一条的Level2 10档行情
	# 2cn_symbol_0,2cn_symbol_1是逐笔数据
	# 2cn_symbol_orders是挂单数据
	# symbol_i是基本信息
	def generate_qlist(self,qlist,symbol):
		qlist = "2cn_%s,2cn_%s_0,2cn_%s_1,%s,%s_i,2cn_%s_orders" % (symbol,symbol,symbol,symbol,symbol,symbol)
		return qlist

	"""
	TODO: 目前websocket断开后的逻辑是重连。需要保持连接不断的逻辑与无缝重连的逻辑。
	"""
	@asyncio.coroutine
	def create_ws(self, qlist, symbol, loop, callback = None ):
		asyncio.set_event_loop(loop)
		# print("BEGINNING OF create_ws: ", qlist)
		token = yield from self.get_ws_token(qlist,symbol)

		url_ws = 'ws://ff.sinajs.cn/wskt?token=' + token + '&list=' + qlist
		url_wss = 'wss://ff.sinajs.cn/wskt?token=' + token + '&list=' + qlist

		# print("BEGINNING OF websockets.connect")
		start = datetime.now()
		ws = yield from websockets.connect(url_wss)
		# print("time cost: ", datetime.now()-start)
		# print("FINISHED websockts.connect")
		while True:
			try:
				message = yield from ws.recv()
				if callback == None:
					callback = self.print_websocket
				yield from callback(message)
			except Exception as e:
				ws.close()
				yield from self.create_ws(qlist,symbol,loop)
	
	@asyncio.coroutine
	def print_websocket(self, message):
		print( "< {}".format(message) )

	def start_ws(self, symbolList = None, loop = None, callback = None ):
		asyncio.set_event_loop(loop)
		qlist = ''
		for symbol in symbolList:
			qlist = self.generate_qlist(qlist=qlist,symbol=symbol)

		if loop.is_running():
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop( loop )
		loop.run_until_complete( self.create_ws(qlist,symbol=symbol, loop=loop, callback=callback) )
