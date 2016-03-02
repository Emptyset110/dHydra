# -*- coding: utf8 -*-
"""
新浪接口：
 1. 模拟登录
 2. WebSocket接口获取实时推送
"""
from datetime import datetime
import os
import asyncio, requests
import config.connection as CON
import pandas as pd
import base64,binascii,rsa,json,time,logging,threading
from autobahn.asyncio.websocket import WebSocketClientProtocol, WebSocketClientFactory
import util
import tushare as ts

class SinaFinance:

	def __init__(self, username=None, pwd=None):
		if (username == None):
			self.username = raw_input('Please input username to login sina:')
		if (pwd == None):
			self.pwd = raw_input('Please input pwd to login sina:')
		self.rsaPubkey = '10001'
		self.ip = util._get_public_ip()
		self.session = requests.Session()
		self.login()

	def login(self):
		# GET http://login.sina.com.cn/sso/prelogin.php
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
				print(req.text)
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
		os.makedirs('../data/stock/stock_l2/%s' % date,exists_ok=True )
		os.makedirs('../data/stock/stock_l2/tmp',exists_ok=True)
		for code in codeList:
			time.sleep(0.001)
			# 这样做可以同时打开N个进程并发进行，加快获取速度
			if ( os.path.exists("../data/stock_l2/tmp/%s"%str(code)) ):
				print("../data/stock_l2/tmp/%s"%str(code)+' exists')
				continue
			f = open("../data/stock_l2/tmp/%s"%str(code),'w')
			f.close()

			totalCount += 1
			# Start timing!
			start = datetime.now()

			symbol = util._code_to_symbol(code)
			print( "symbol = ",symbol )
			if not(os.path.exists('../data/stock_l2/%s/%s.csv' % (date,symbol) )):
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
				l2.to_csv('../data/stock_l2/%s/%s.csv' % (date,symbol) )
				print( "Count: ",count )
				print( "Time Cost: ", datetime.now()-start )


	def wskt_token(self):
		self.session.get('http://finance.sina.com.cn/realstock/company/sz300204/l2.shtml')
		symbol = 'sz300204'
		qlist = '2cn_sz300204,2cn_sz300204_orders,2cn_sz300204_0,2cn_sz300204_1,sz300204_i,sz300204'
		req = self.session.get(
			CON.URL_WSKT_TOKEN
		,	params 	=	CON.PARAM_WSKT_TOKEN(ip=self.ip,qlist=qlist)
		,	headers =	CON.HEADERS_WSKT_TOKEN()
		,	verify	=	True
		)
		# print( req.json() )
		print( req.text[25:-3] )
		print( req.text[45:-17] )
		token = req.text[45:-17]
		return token

	def wskt(self, token):
		pass