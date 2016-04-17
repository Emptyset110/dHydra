# -*- coding: utf8 -*-
import time
# 高速行情接口
URL_QUOTATION = lambda symbols: "http://hq.sinajs.cn/?rn=%s&list=%s" % ( int( time.time() )*1000, symbols )

SINA_QUOTE_COLUMNS = [	'name', 'open'
					,	'pre_close', 'price', 'high', 'low', 'bid', 'ask', 'volume', 'amount'
					,	'b1_v',	'b1_p', 'b2_v', 'b2_p', 'b3_v', 'b3_p', 'b4_v', 'b4_p', 'b5_v', 'b5_p'
					,	'a1_v',	'a1_p', 'a2_v', 'a2_p', 'a3_v', 'a3_p', 'a4_v', 'a4_p', 'a5_v', 'a5_p'
					,	'date', 'time', 'ms']

SINA_QUOTE_COLUMNS_2 = [	'name', 'open'
					,	'pre_close', 'price', 'high', 'low', 'bid', 'ask', 'volume', 'amount'
					,	'b1_v',	'b1_p', 'b2_v', 'b2_p', 'b3_v', 'b3_p', 'b4_v', 'b4_p', 'b5_v', 'b5_p'
					,	'a1_v',	'a1_p', 'a2_v', 'a2_p', 'a3_v', 'a3_p', 'a4_v', 'a4_p', 'a5_v', 'a5_p'
					,	'date', 'time', 'ms', 'symbol']

DATA_LOGIN = lambda su,servertime,nonce,rsakv,sp: {
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
}

URL_CROSSDOMAIN = "http://login.sina.com.cn/sso/crossdomain.php"
URL_SSOLOGIN = "http://login.sina.com.cn/sso/login.php"
URL_SSOLOGOUT = "http://login.sina.com.cn/sso/logout.php"
URL_UPDATECOOKIE = "http://login.sina.com.cn/sso/updatetgt.php"
URL_PRELOGIN = "http://login.sina.com.cn/sso/prelogin.php"
URL_PINCODE = "http://login.sina.com.cn/cgi/pin.php"
URL_VFVALID = "http://weibo.com/sguide/vdun.php"
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
PARAM_L2HIST = lambda symbol,page,stime,etime: {
	"symbol"			:	symbol
,	"callback"			:	"jQuery17209838373235483986_" + str( int(time.time()*1000) )
,	"pageNum"			:	10000
,	"page"				:	page
,	"stime"				:	stime
,	"etime"				:	etime
,	"sign"				:	''
,	"num"				:	'20'
,	"_"					:	int(time.time()*1000)
}
HEADERS_LOGIN = {
	"Accept" : '*/*'
,	"Accept-Encoding" : 'gzip, deflate, sdch'
,	"Accept-Language" : 'en-US,en;q=0.8'
,	"Connection" : 'keep-alive'
,	"Host" : 'login.sina.com.cn'
,	"Referer" : 'http://finance.sina.com.cn/'
,	"User-Agent" : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'
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
HEADERS_CROSSDOMAIN = lambda host	:	{
	'Host'							:	host
,	'User-Agent'					:	'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'
,	'Accept'						: 	'*/*'
,	'Accept-Language'				:	'en-US,en;q=0.5'
,	'Accept-Encoding'				:	'gzip, deflate'
,	'Referer'						:	'http://finance.sina.com.cn/realstock/company/sz300204/l2.shtml'
,	'Connection'					:	'keep-alive'
}
CLIENT = "ssologin.js(v1.4.18)"
CROSSDOMAIN_HOST = [
	"passport.weibo.com"
,	"crosdom.weicaifu.com"
,	"passport.weibo.cn"
]
URL_L2HIST = 'http://stock.finance.sina.com.cn/stock/api/openapi.php/StockLevel2Service.getTransactionList'
# 获取
URL_API_MARKET_CENTER_GETHQNODEDATA = lambda node: "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?num=5000&sort=symbol&asc=0&node=%s&symbol=&_s_r_a=page&page=1" % node
# node = hs_a, hs_b
# 数据格式中key缺少双引号
# [	
# 	{
# 		symbol:"sh600006"
# 	,	code:"600006"
# 	,	name:"东风汽车"
# 	,	trade:"6.210"
# 	,	pricechange:"0.000"
# 	,	changepercent:"0.000"
# 	,	buy:"0.000"
# 	,	sell:"0.000"
# 	,	settlement:"6.210"
# 	,	open:"0.000"
# 	,	high:"0.000"
# 	,	low:"0.000"
# 	,	volume:0
# 	,	amount:0
# 	,	ticktime:"10:12:31"
# 	,	per:88.336
# 	,	pb:1.94
# 	,	mktcap:1242000
# 	,	nmc:1242000
# 	,	turnoverratio:0
# 	}
# ]