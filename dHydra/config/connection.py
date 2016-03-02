# -*- coding: utf8 -*-
"""
Connection Settings
Created on 02/26/2016
@description:	Used for 
@author: 		Wen Gu
@contact: 		emptyset110@gmail.com
"""

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
,	"callback"			:	"jQuery17203851605022791773_" + str( int(time.time()*1000) )
,	"pageNum"			:	10000
,	"page"				:	page
,	"stime"				:	'09%3A15%3A00'
,	"etime"				:	'15%3A05%3A00'
,	"sign"				:	''
,	"num"				:	'0'
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
# ,	'Cookie'					:	'UOR=,finance.sina.com.cn,; SINAGLOBAL=117.85.56.181_1456667771.258251; vjuids=-4299b1d0a.153282a4536.0.63624093; SGUID=1456667772264_5d5aafd5; U_TRS1=000000b5.5238d9b.56d2fc7c.5af26a8b; ArtiFSize=14; Apache=117.85.56.88_1456806197.633755; vjlast=1456806198; U_TRS2=00000058.d1ea15a2.56d51935.3cc94184; usrmdpool=usrmdinst_0; ULV=1456806345873:5:3:5:117.85.56.88_1456806197.633755:1456806197600; lxlrtst=1456805122_o; lxlrttp=1456805122; hqEtagMode=1; rotatecount=3; SUS=SID-3341633314-1456806370-GZ-wck24-f647a5bf3fe1d6a5766967dbe671074f; SUE=es%3Ded2e5ba93a533a1cf83ad410ee550905%26ev%3Dv1%26es2%3Ddf44eccbfbe464fd125e505f48f1efdd%26rs0%3DU0HiSYFUZ5vC6qlR96izRwkKcWVOBTnhyk2cxcOqZSxh373q%252FYlrpMaW%252Blfrp20Cd1NwEWUjmileZc0wK7pu1XTEddS0CVPHoVt7CAKfCFVssA2YJI51HdbKBAXZUEkq4xWvxGyiy4qNcb%252Bp0VpgN2dIYFDQK6K4BxumfmsAAmc%253D%26rv%3D0; SUP=cv%3D1%26bt%3D1456806370%26et%3D1456892770%26d%3D40c3%26i%3D074f%26us%3D1%26vf%3D0%26vt%3D0%26ac%3D2%26st%3D0%26lt%3D1%26uid%3D3341633314%26user%3D13373635073%26ag%3D1%26name%3D13373635073%26nick%3DOriginal_Emptyset%26sex%3D%26ps%3D0%26email%3D%26dob%3D%26ln%3D13373635073%26os%3D%26fmp%3D%26lcp%3D; SUB=_2A2570WmyDeRxGeVN71MX8y3PyjiIHXVYp9x6rDV_PUNbuNBeLWHFkW9LHetfmk0CtFgTSk0cCVYqIlFYxMW7Xg..; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9Wh0iz-ugMVN5EgRvkEg4y1X; ALF=1488342370; sso_info=v02m6alo5qztY-cpqWnmpa5oZuFvYWbl4G0npeNpZ2CmbWalpC9jLOMtIyTmLOMs4yxjYDAwA==;theone=current56d5193b6f421'
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
PARAM_WSKT_TOKEN = lambda ip, qlist: {
	"query"	:	"hq_pjb"
,	"ip"	:	ip
,	"_"		:	random.uniform(0.1,0.2)
,	"kick"	:	1
,	"list"	:	qlist
}
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

URL_L2HIST = 'http://stock.finance.sina.com.cn/stock/api/openapi.php/StockLevel2Service.getTransactionList'
URL_WSKT_TOKEN = 'https://current.sina.com.cn/auth/api/jsonp.php/var%20KKE_auth_OSfOoonMj=/AuthSign_Service.getSignCode'
SOCKET_BASE = 'ws://ff.sinajs.cn/wskt'
