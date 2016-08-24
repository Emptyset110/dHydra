# -*- coding: utf-8 -*-
import time
# 登录
URL_LOGIN = "https://www.jisilu.cn/account/ajax/login_process/"
HEADERS_LOGIN = {
	"Accept"			:	"application/json, text/javascript, */*; q=0.01"
,	"Accept-Encoding"	:	"gzip, deflate"
,	"Accept-Language"	:	"en-US,en;q=0.8"
,	"Connection"		:	"keep-alive"
,	"Content-Length"	:	"96"
,	"Content-Type"		:	"application/x-www-form-urlencoded; charset=UTF-8"
,	"Host"				:	"www.jisilu.cn"
,	"Origin"			:	"https://www.jisilu.cn"
,	"Referer"			:	"https://www.jisilu.cn/login/"
,	"User-Agent"		:	"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.86 Safari/537.36"
,	"X-Requested-With"	:	"XMLHttpRequest"
}
DATA_LOGIN = lambda username, pwd : {
	"return_url"	:	"https://www.jisilu.cn/"
,	"user_name"		:	username
,	"password"		:	pwd
,	"net_auto_login":	'1'
,	"_post_type"	:	"ajax"
}

HEADERS = {
	"Accept"			:	"application/json, text/javascript, */*; q=0.01"
,	"Accept-Encoding"	:	"gzip, deflate"
,	"Accept-Language"	:	"en-US,en;q=0.8"
,	"Connection"		:	"keep-alive"
,	"Content-Type"		:	"application/x-www-form-urlencoded; charset=UTF-8"
,	"Host"				:	"www.jisilu.cn"
,	"Origin"			:	"https://www.jisilu.cn"
,	"Referer"			:	"https://www.jisilu.cn/data/sfnew/"
,	"User-Agent"		:	"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.86 Safari/537.36"
,	"X-Requested-With"	:	"XMLHttpRequest"
}

# 分级A的接口
URL_FUNDA = "https://www.jisilu.cn/data/sfnew/funda_list/?___t=%s" % int( time.time()*1000 )


# 分级B的接口
URL_FUNDB = "https://www.jisilu.cn/data/sfnew/fundb_list/?___t=%s" % int( time.time()*1000 )

# 母基金接口
URL_FUNDM = "https://www.jisilu.cn/data/sfnew/fundm_list/?___t=%s" % int( time.time()*1000 )

# 分级套利的接口
URL_FUNDAB = 'https://www.jisilu.cn/data/sfnew/arbitrage_vip_list/?___t=%s' % int( time.time()*1000 )
DATA_FUNDAB = {
	"is_search"	:	"0"
,	"avolume"	:	"100"
,	"bvolume"	:	"100"
,	"market"	:	["sh","sz"]
,	"ptype"		:	"price"
,	"rp"		:	"50"
}

# 集思路股指期货接口
URL_FUTURE = lambda future_type : 'https://www.jisilu.cn/data/index_future/if_list/%s?___t=%s' % ( future_type, int( time.time()*1000 ) )
