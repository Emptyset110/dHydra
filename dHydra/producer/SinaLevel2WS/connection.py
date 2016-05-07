# -*- coding: utf8 -*-
"""
新浪财经
FROM ssologin.js(v1.4.18)
"""
import time
import random

CLIENT = "ssologin.js(v1.4.18)"
CROSSDOMAIN_HOST = [
	"passport.weibo.com"
,	"crosdom.weicaifu.com"
,	"passport.weibo.cn"
]

HEADERS_LOGIN = {
	"Accept" : '*/*'
,	"Accept-Encoding" : 'gzip, deflate, sdch'
,	"Accept-Language" : 'en-US,en;q=0.8'
,	"Connection" : 'keep-alive'
,	"Host" : 'login.sina.com.cn'
,	"Referer" : 'http://finance.sina.com.cn/'
,	"User-Agent" : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'
}
PARAM_L2HIST = lambda symbol,page: {
	"symbol"			:	symbol
,	"callback"			:	"jQuery17209838373235483986_" + str( int(time.time()*1000) )
,	"pageNum"			:	10000
,	"page"				:	page
,	"stime"				:	'09:25:00'
,	"etime"				:	'15:05:00'
,	"sign"				:	''
,	"num"				:	'20'
,	"_"					:	int(time.time()*1000)
}
HEADERS_L2 = lambda symbol	: {
	'Host'				:	'stock.finance.sina.com.cn'
,	'Connection'		:	'keep-alive'
,	'Accept'			:	'*/*'
,	'User-Agent'		:	'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'
,	'Referer'			:	'http://vip.stock.finance.sina.com.cn/quotes_service/view/l2_tradedetail.php?symbol=%s' % symbol
,	'Accept-Encoding'	:	'gzip, deflate, sdch'
,	'Accept-Language'	:	'en-US,en;q=0.8'
}
HEADERS_WSKT_TOKEN = lambda 	:	{
	'Accept'					:	'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
,	'Accept-Encoding'			:	'gzip, deflate, sdch'
,	'Accept-Language'			:	'en-US,en;q=0.8'
,	'Connection'				:	'keep-alive'
,	'Host'						:	'current.sina.com.cn'
,	'User-Agent'				:	'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'
,	'Referer'					:	'http://finance.sina.com.cn/realstock/company/sz300204/l2.shtml'
}
HEADERS_CROSSDOMAIN = lambda host	:	{
	'Host'							:	host
,	'User-Agent'					:	'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'
,	'Accept'						: 	'*/*'
,	'Accept-Language'				:	'en-US,en;q=0.5'
,	'Accept-Encoding'				:	'gzip, deflate'
,	'Referer'						:	'http://finance.sina.com.cn/realstock/company/sz300204/l2.shtml'
,	'Connection'					:	'keep-alive'
}
PARAM_LOGIN = lambda : {
	"client" 		:	CLIENT
,	"_"				:	int(time.time()*1000)
}
PARAM_PRELOGIN = lambda su : {
	"entry"			:	"finance"
,	"callback"		:	"sinaSSOController.preloginCallBack"
,	"su"			:	su
,	"rsakt"			:	'mod'
,	"client"		:	CLIENT
,	"_"				:	int(time.time()*1000)
}
PARAM_WSKT_TOKEN = lambda ip, qlist, hq: {
	"query"	:	hq
,	"ip"	:	ip
,	"_"		:	random.uniform(0.1,0.2)
,	"kick"	:	1
,	"list"	:	qlist
}
DATA_LOGIN = lambda su,servertime,nonce,rsakv,sp,door: {
	"entry"			:	"finance"
,	"gateway"		:	1
,	"from"			:	""
,	"savestate" 	:	30
,	"useticket" 	:	0
,	"pagerefer" 	:	""
,	"vsnf"			:	"1"
,	"su"			:	su
,	"service"		:	"sso"
,	"servertime"	:	servertime
,	"nonce"			:	nonce
,	"pwencode"		:	"rsa2"
,	"rsakv"			:	rsakv
,	"sp"			:	sp
,	"sr" 			:	"1920*1080"
,	"encoding"		:	"UTF-8"
,	"cdult"			:	3
,	"domain"		:	"sina.com.cn"
,	"prelt"			:	72
,	"returntype"	:	"TEXT"
,	"door"			:	door
}

URL_CROSSDOMAIN = "http://login.sina.com.cn/sso/crossdomain.php"
URL_SSOLOGIN = "http://login.sina.com.cn/sso/login.php"
URL_SSOLOGOUT = "http://login.sina.com.cn/sso/logout.php"
URL_UPDATECOOKIE = "http://login.sina.com.cn/sso/updatetgt.php"
URL_PRELOGIN = "http://login.sina.com.cn/sso/prelogin.php"
URL_PINCODE = "http://login.sina.com.cn/cgi/pin.php"
URL_VFVALID = "http://weibo.com/sguide/vdun.php"

URL_L2HIST = 'http://stock.finance.sina.com.cn/stock/api/openapi.php/StockLevel2Service.getTransactionList'
URL_WSKT_TOKEN = 'https://current.sina.com.cn/auth/api/jsonp.php/var%20KKE_auth_OSfOoonMj=/AuthSign_Service.getSignCode'
SOCKET_BASE = 'ws://ff.sinajs.cn/wskt'