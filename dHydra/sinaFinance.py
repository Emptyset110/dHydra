# -*- coding: utf8 -*-
"""
新浪接口：
 1. 模拟登录
 2. WebSocket接口获取实时推送
"""
from datetime import datetime
import requests
import pandas as pd
import base64,binascii,rsa,json,time,logging,threading
# from autobahn.asyncio.websocket import WebSocketClientProtocol, WebSocketClientFactory
import socket
import os
import websockets
import functools
### The incompatibility between python 2 & 3 is HOLY BULLSHIT ###
try:
   input = raw_input
except NameError:
   pass
try:
	import dHydra.util as util
except:
	import util
try:
	import dHydra.config.connection as CON
except:
	from config import connection as CON
try:
    import asyncio
except ImportError:
    import trollius as asyncio
### The incompatibility between python 2 & 3 is HOLY BULLSHIT ###

class SinaFinance:
	def __init__(self, username=None, pwd=None):
		if (username == None):
			self.username = input('Please input username to login sina:')
		else:
			self.username=username
		if (pwd == None):
			self.pwd = input('Please input pwd to login sina:')
		else:
			self.pwd = pwd
		self.rsaPubkey = '10001'
		self.ip = util._get_public_ip()
		self.session = requests.Session()
		self.login()
		self.host = socket.gethostbyname('ff.sinajs.cn')
		# self.loop = asyncio.get_event_loop()
		self.count = 0

	def login(self):

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
			print( "Successfully Logged in as %s, uid = %s" % ( self.login.json()["nick"], self.login.json()["uid"]) )

			i = 0
			for url in self.login.json()["crossDomainUrlList"]:
				req = self.session.get( url,headers = CON.HEADERS_CROSSDOMAIN(CON.CROSSDOMAIN_HOST[i]) )
				# print(req.text)
				i += 1
		else:
			print( "Authentication Failed... Please Check Your USERNAME and PASSWORD" )
			print( self.login.json() )

	
	# RSA2 encoding
	def get_sp(self, passwd, pubkey, servertime, nonce):
		key = rsa.PublicKey(int(pubkey, 16), int('10001', 16))
		message = str(servertime) + '\t' + str(nonce) + '\n' + str(passwd)
		passwd = rsa.encrypt(message.encode('utf-8'), key)
		return binascii.b2a_hex(passwd).decode('ascii')

	# 获取逐笔数据
	def l2_hist(self, codeList):
		totalCount = 0
		date = str(datetime.now().date())
		try:
		    os.makedirs( './data/stock_l2/%s' % date,exist_ok=True )
		    os.makedirs('./data/stock_l2/tmp',exist_ok=True)
		except:
			try:
			    os.makedirs( './data/stock_l2/%s' % date )
			    os.makedirs('./data/stock_l2/tmp' )
			except:
				pass

		for code in codeList:
			time.sleep(0.001)
			# 这样做可以同时打开N个进程并发进行，加快获取速度
			if ( os.path.exists("data/stock_l2/tmp/%s"%str(code)) ):
				print("data/stock_l2/tmp/%s"%str(code)+' exists')
				continue
			f = open("data/stock_l2/tmp/%s"%str(code),'w')
			f.close()

			totalCount += 1
			# Start timing!
			start = datetime.now()

			symbol = util._code_to_symbol(code)
			print( "symbol = ",symbol )
			if not(os.path.exists('data/stock_l2/%s/%s.csv' % (date,symbol) )):
				nextPage = True
				page = 1
				while (nextPage):
					
					req = self.session.get( 
							CON.URL_L2HIST
						,	params = CON.PARAM_L2HIST(symbol=symbol, page=page)
						,	headers = CON.HEADERS_L2(symbol=symbol)
						)
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
				l2.to_csv('data/stock_l2/%s/%s.csv' % (date,symbol) )
				print( "Count: ",count )
				print( "Time Cost: ", datetime.now() - start )


	@asyncio.coroutine
	def get_ws_token(self,qlist,symbol):
		# self.session.get('http://finance.sina.com.cn/realstock/company/sz300204/l2.shtml')
		# req = self.session.get(
		# 	CON.URL_WSKT_TOKEN
		# ,	params 	=	CON.PARAM_WSKT_TOKEN(ip=self.ip,qlist=qlist)
		# ,	headers =	CON.HEADERS_WSKT_TOKEN()
		# ,	verify	=	True
		# )
		loop = asyncio.get_event_loop()
		async_req = loop.run_in_executor(None, functools.partial( self.session.get, 
			CON.URL_WSKT_TOKEN
		,	params 	=	CON.PARAM_WSKT_TOKEN(ip=self.ip,qlist=qlist)
		,	headers =	CON.HEADERS_WSKT_TOKEN()
		,	verify	=	True
		) )
		req = yield from async_req
		# print( req.text[25:-3] )
		print( "token = ", req.text[45:-17] )
		token = req.text[45:-17]
		return token

	# 2cn_是3秒一条的Level2 10档行情
	def generate_qlist(self,qlist,symbol):
		if qlist!='':
			qlist = qlist + ",2cn_%s,2cn_%s_0,2cn_%s_1,%s" % (symbol,symbol,symbol,symbol)
		else:
			qlist = "2cn_%s,2cn_%s_0,2cn_%s_1,%s" % (symbol,symbol,symbol,symbol)
		return qlist

	@asyncio.coroutine
	def create_ws(self, qlist, symbol, loop):
		asyncio.set_event_loop(loop)
		print("BEGINNING OF create_ws: ", qlist)
		token = yield from self.get_ws_token(qlist,symbol)

		url_ws = 'ws://ff.sinajs.cn/wskt?token=' + token + '&list=' + qlist
		url_wss = 'wss://ff.sinajs.cn/wskt?token=' + token + '&list=' + qlist

		print("BEGINNING OF websockets.connect")
		start = datetime.now()
		ws = yield from websockets.connect(url_wss)
		print("time cost: ", datetime.now()-start)
		print("FINISHED websockts.connect")
		while True:
			try:
				message = yield from ws.recv()
				print( "< {}".format(message) )
				self.count += 1
				print( "Count", self.count )
			except Exception as e:
				print(e)
				ws.close()
				yield from self.create_ws(qlist,symbol,loop)
				

	def start_ws(self, symbolList = None, loop = None ):
		asyncio.set_event_loop(loop)
		qlist = ''
		for symbol in symbolList:
			qlist = self.generate_qlist(qlist=qlist,symbol=symbol)

		if loop.is_running():
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop( loop )
		loop.run_until_complete( self.create_ws(qlist,symbol=symbol, loop=loop) )
