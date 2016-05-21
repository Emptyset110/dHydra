# -*- coding: utf-8 -*-
"""
# Created on 2016/04/12
# @author:
# @contact:
"""
# 以下是自动生成的 #
# --- 导入系统配置
import dHydra.core.util as util
from dHydra.core.Vendor import Vendor
from dHydra.config import connection as CON
from dHydra.config import const as C
from dHydra.core.Globals import *
# --- 导入自定义配置
from .connection import *
from .const import *
from .config import *
# 以上是自动生成的 #

import requests
import re
from pandas import DataFrame
import pandas as pd
import asyncio
import functools
from datetime import datetime
import json
import base64,binascii,rsa
import getpass


class SinaVendor(Vendor):
	def __init__(self, username = None, pwd = None):
		super().__init__()
		if (username is None):
			if "sinaUsername" in config.keys():
				self.username = config["sinaUsername"]
			else:
				self.username = input('请输入新浪登录帐号：')
		else:
			self.username=username
		if (pwd is None):
			if "sinaPassword" in config.keys():
				self.pwd = config["sinaPassword"]
			else:
				self.pwd = getpass.getpass("输入登录密码（密码不会显示在屏幕上，输入后按回车确定）:")
		else:
			self.pwd = pwd
		self.rsa_pubkey = '10001'
		self.ip = util.get_client_ip()
		self.session = requests.Session()
		self.quote = None
		self.is_login = False
		self.symbols = self.get_symbols()

	def get_verify_code(self):
		verify_code_response = self.session.get("http://login.sina.com.cn/cgi/pin.php")
		# 保存验证码
		image_path = os.path.join(os.getcwd(), 'vcode.png')
		with open(image_path, 'wb') as f:
			f.write(verify_code_response.content)
		verifyCode = input( "验证码图片保存在{}，\n请输入验证码：".format(image_path) )
		return verifyCode

	def login(self, verify = False):
		self.session.get("http://finance.sina.com.cn/realstock/company/sz300204/l2.shtml")
		su = base64.b64encode(self.username.encode('utf-8'))

		preLogin = self.session.get( URL_PRELOGIN, params = PARAM_PRELOGIN( su ), headers = HEADERS_LOGIN)
		preLogin = json.loads( preLogin.text[len("sinaSSOController.preloginCallBack("):-1] )

		sp = self.get_sp( self.pwd, preLogin["pubkey"], int(preLogin["servertime"]), preLogin["nonce"] )

		if verify:
			verifyCode = self.get_verify_code()
		else:
			verifyCode = ''

		self.loginResponse = self.session.post(
			URL_SSOLOGIN
		,	params = PARAM_LOGIN()
		,	data = DATA_LOGIN(
				su = su
			,	servertime = int( preLogin["servertime"] )
			,	nonce = preLogin["nonce"]
			,	rsakv = preLogin["rsakv"]
			,	sp = sp
			,	door = verifyCode
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
		elif (self.loginResponse.json()["retcode"] == '4049'):
			print( self.loginResponse.json() )
			self.is_login = self.login(verify = True)
			if self.is_login:
				return True
			else:
				return False
		else:
			print( self.loginResponse.json() )
			return False

	# RSA2 encoding
	def get_sp(self, passwd, pubkey, servertime, nonce):
		key = rsa.PublicKey(int(pubkey, 16), int('10001', 16))
		message = str(servertime) + '\t' + str(nonce) + '\n' + str(passwd)
		passwd = rsa.encrypt(message.encode('utf-8'), key)
		return binascii.b2a_hex(passwd).decode('ascii')

	def get_deal(self, symbol, stime = None, etime = None):
		while not self.is_login:
			self.is_login = self.login()

		if stime is None:
			stime = "09:25:00"
		if etime is None:
			etime = "15:05:00"
		nextPage = True
		page = 1
		l2 = list()
		while (nextPage):
			data = self.session.get(	URL_L2HIST
						,	params 	= 	PARAM_L2HIST(symbol=symbol, page=page, stime=stime, etime=etime)
						,	headers = 	HEADERS_L2(symbol=symbol)
			)
			data = data.text[90:-2]
			data = dict( json.loads(data) )
			count = int( data["result"]["data"]["count"] )
			if ( data["result"]["data"]["data"] is not None ):
				l2.extend(data["result"]["data"]["data"])
			if ( len(l2) == count ):
				nextPage = False
			page+=1
		l2df = pd.DataFrame( l2 )
		l2df = l2df.convert_objects(convert_dates=False,convert_numeric=True,convert_timedeltas=False)
		if not(len(l2df)==0):
			l2df = l2df.set_index("index").sort_index("index")
		return l2df



	# sz,sh的时间戳不同，强烈建议分开调用
	# 如果开启split = True, 则会返回
	def get_realtime_quotes(self, symbols = None, dataframe = True, loop = None, split = False):
		self.quote = None
		if symbols is None:
			symbols = self.symbols
		if loop is None:
			loop = asyncio.get_event_loop()
		else:
			asyncio.set_event_loop(loop)

		if isinstance(symbols, str):
			symbolList = symbols.split(',')
		else:
			symbolList = list(symbols)
		[ symbols_sz, symbols_sh ] = util.split_symbols(symbolList)
		symbolListSlice = util.slice_list(step = 800, dataList = symbols_sz)
		symbolListSlice.extend( util.slice_list(step = 800, dataList = symbols_sh) )
		loop.run_until_complete( self.get_quote_task(symbolListSlice=symbolListSlice, dataframe = dataframe) )
		if dataframe:
			self.quote = self.quote.drop( 'ms', axis = 1 )
			self.quote.convert_objects(convert_dates=False,convert_numeric=True,convert_timedeltas=False)
		if split:
			quote_sz = self.quote[ self.quote.symbol > 'sz' ]
			quote_sh = self.quote[ self.quote.symbol < 'sz' ]
			return [ quote_sz, quote_sh ]
		return self.quote

	@asyncio.coroutine
	def get_quote_task(self, symbolListSlice, dataframe):
		for symbolList in symbolListSlice:
			quote = yield from self.get_quote_coroutine(symbols = symbolList, dataframe=dataframe)
			if self.quote is None:
				self.quote = quote
			else:
				if dataframe:
					self.quote = self.quote.append(quote, ignore_index=True)
				else:
					self.quote.extend(quote)


	@asyncio.coroutine
	def get_quote_coroutine(self, symbols, dataframe):
		loop = asyncio.get_event_loop()
		if isinstance(symbols, list) or isinstance(symbols, set) or isinstance(symbols, tuple):
			symbolList = list(symbols)
		elif isinstance(symbols, str):
			symbolList = symbols.split(',')
		symbols = util.symbols_to_string(symbols)
		url = URL_QUOTATION(symbols)

		retry = True
		while retry:
			try:
				async_req = loop.run_in_executor(None, functools.partial( self.session.get
				,	URL_QUOTATION(symbols)
				,	timeout = 0.1
				) )
				quote = yield from async_req
				retry = False
			except:
				pass
		quote = quote.text
		quote = re.findall(r'\"(.*)\"', quote)

		for i in range( 0, len(quote) ):
			quote[i] = quote[i].split(',')

		if dataframe:
			quote = DataFrame( quote, columns = SINA_QUOTE_COLUMNS )
			quote["symbol"] = symbolList
			quote["time"] = datetime.strptime( quote.iloc[0]["date"] + " " + quote.iloc[0]["time"] , '%Y-%m-%d %H:%M:%S')
		return quote

	# 新浪获取当前全部股票的接口
	# 如果 dataframe = True， 则返回panda.DataFrame格式，
	# 否则 返回list格式，每个list中是一个dict
	def get_today_all(self, node = 'hs_a', dataframe = True):
		import json
		import time

		# start = time.time()
		retry = True
		while retry:
			try:
				response = self.session.get(
					URL_API_MARKET_CENTER_GETHQNODEDATA(node)
				,	timeout = 3
					).text
				retry = False
			except:
				print("获取数据超时，正在重试")
		# 因为返回的json不标准，需要给key加上引号
		response = response.replace(
			"symbol","\"symbol\""
			).replace(
			"code","\"code\""
			).replace(
			"name","\"name\""
			).replace(
			"trade","\"trade\""
			).replace(
			"pricechange","\"pricechange\""
			).replace(
			"pricepercent","\"pricepercent\""
			).replace(
			"buy","\"buy\""
			).replace(
			"sell","\"sell\""
			).replace(
			"settlement","\"settlement\""
			).replace(
			"open","\"open\""
			).replace(
			"high","\"high\""
			).replace(
			"low","\"low\""
			).replace(
			"volume","\"volume\""
			).replace(
			"amount","\"amount\""
			).replace(
			"ticktime","\"ticktime\""
			).replace(
			"per","\"per\""
			).replace(
			"pb","\"pb\""
			).replace(
			"mktcap","\"mktcap\""
			).replace(
			"nmc","\"nmc\""
			).replace(
			"turnoverratio","\"turnoverratio\""
			).replace("change\"per\"cent","\"changepercent\"")
		# print(time.time()-start)
		todayAll = json.loads( response )
		if dataframe:
			todayAll = DataFrame(todayAll)
		return todayAll

	"""
	用于获取当日股票列表
	返回： list
	参数：
		（可选）stockTypeList:
			类型：list
			默认：["hs_a","hs_b"] 代表获取全部沪深AB代码
	"""
	def get_symbols(self, stockTypeList = ["hs_a","hs_b"]):
		symbolList = list()
		for node in stockTypeList:
			symbols = list(self.get_today_all(node = node)["symbol"])
			symbolList.extend(symbols)
		return symbolList

	def get_quote(self, symbols, dataframe = True):
		if isinstance(symbols, list) or isinstance(symbols, set) or isinstance(symbols, tuple):
			symbolList = list(symbols)
		elif isinstance(symbols, str):
			symbolList = symbols.split(',')
		symbols = util.symbols_to_string(symbols)
		url = URL_QUOTATION(symbols)
		retry = True
		while retry:
			try:
				quote  =self.session.get(
						URL_QUOTATION(symbols)
					,	timeout = 0.1
					).text
				retry = False
			except:
				pass
		quoteList = re.findall(r'\"(.*)\"', quote)
		if dataframe:
			for i in range( 0, len(quoteList) ):
				quoteList[i] = quoteList[i].split(',')
		else:
			for i in range( 0, len(quoteList) ):
				quoteList[i] = quoteList[i].split(',')
				quoteList[i].append( symbolList[i] )

		if dataframe:
			df_quote = DataFrame( quoteList, columns = SINA_QUOTE_COLUMNS )
			df_quote = df_quote.drop( 'ms', axis = 1 )
			df_quote["symbol"] = symbolList
			return df_quote
		else:
			return quoteList

	def get_ticktime(self):
		quote = self.get_quote(symbols= ["sz000001","sh600000"])
		szTime = datetime.strptime( quote.iloc[0]["date"] + " " + quote.iloc[0]["time"] , '%Y-%m-%d %H:%M:%S')
		shTime = datetime.strptime( quote.iloc[1]["date"] + " " + quote.iloc[1]["time"] , '%Y-%m-%d %H:%M:%S')
		return [szTime, shTime]
