# -*- coding: utf8 -*-
"""
Connection Settings
Created on 02/26/2016
@description:	Used for 
@author: 		Wen Gu
@contact: 		emptyset110@gmail.com
"""
import time
"""
雪球
"""
HEADERS_XUEQIU = {
	"Accept"			:	"application/json, text/javascript, */*; q=0.01"
,	"Accept-Encoding"	:	"gzip, deflate, sdch"
,	"Accept-Language"	:	"en-US,en;q=0.8"
,	"cache-control"		:	"no-cache"
,	"Connection"		:	"keep-alive"
,	"Host"				:	"xueqiu.com"
,	"Referer"			:	"https://xueqiu.com/hq"
,	"User-Agent"		:	"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36"
,	"Upgrade-Insecure-Requests"	: "1"
,	"X-Requested-With"	:	"XMLHttpRequest"
}

HEADERS_XUEQIU_INDEX = {
	"Accept"			:	"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
,	"Accept-Encoding"	:	"gzip, deflate, sdch"
,	"Accept-Language"	:	"en-US,en;q=0.8"
,	"Connection"		:	"keep-alive"
,	"Host"				:	"xueqiu.com"
,	"Upgrade-Insecure-Requests"	:	"1"
,	"User-Agent"		:	"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36"
}


URL_XUEQIU_HQ = "https://xueqiu.com/hq"
URL_XUEQIU_QUOTE_ORDER = lambda page,columns,stockType : "https://xueqiu.com/stock/quote_order.json?page=%s&size=90&order=desc&exchange=CN&stockType=%s&column=%s&orderBy=symbol&_=%s"	% ( page,stockType, columns,int(time.time()*1000) )
CONST_XUEQIU_QUOTE_ORDER_COLUMN = "symbol,name,current,chg,percent,last_close,open,high,low,volume,amount,market_capital,pe_ttm,high52w,low52w,hasexist"

# 用于获取k线
# fqType: before,normal,after,
# start,end: 13位时间戳
# period = 1day(1d),5day(5d),1week,1month
URL_XUEQIU_KLINE = lambda symbol,period,fqType,begin,end: "https://xueqiu.com/stock/forchartk/stocklist.json?symbol=%s&period=%s&type=%s&begin=%s&end=%s&_=%s" % ( symbol,period,fqType,begin,end,int(time.time()*1000) )
URL_XUEQIU_CHART = lambda symbol,period: "https://xueqiu.com/stock/forchart/stocklist.json?symbol=%s&period=%s&one_min=1&_%s" % ( symbol,period,int(time.time()*1000) )

# 用于获取基本面或者实时quote
# code可以取多个，用逗号分割
URL_XUEQIU_QUOTE = lambda symbols : "http://xueqiu.com/v4/stock/quote.json?code=%s&_=%s" % (symbols, int(time.time()*1000) )
CONST_XUEQIU_QUOTE_COLUMN = "symbol,exchange,code,name,current,percentage,change,open,high,low,close,last_close,high52week,low52week,volume,volumeAverage,marketCapital,eps,pe_ttm,pe_lyr_beta,totalShares,time,afterHours,afterHoursPct,afterHoursChg,updateAt,dividednd,yield,turnover_rate,instOwn,rise_stop,fall_stop,currency_unit,amount,net_assets,hasexist,has_warrant,type,flag,rest_day,amplitude,lot_size,tick_size,kzz_stock_symbol,kzz_stock_name,kzz_stock_current,kzz_convert_price,kzz_convert_value"
{	"SZ000001":
		{	
			"symbol"			:	"SZ000001"			# 代码
		,	"exchange"			:	"SZ"				# SZ/SH
		,	"code"				:	"000001"			# code
		,	"name"				:	"平安银行"			# 中文名	
		,	"current"			:	"10.59"				# 当前价
		,	"percentage"		:	"-1.21"				# 涨幅
		,	"change"			:	"-0.13"				# 与开盘价差值
		,	"open"				:	"10.72"				# 开盘价
		,	"high"				:	"10.73"				# 最高价
		,	"low"				:	"10.59"				# 最低价
		,	"close"				:	"8.27"				# 今日收盘价
		,	"last_close"		:	"10.72"				# 昨收盘价
		,	"high52week"		:	"19.8"				# 52周最高价
		,	"low52week"			:	"9.3"				# 52周最低价
		,	"volume"			:	"3.7771959E7"		# 成交量
		,	"volumeAverage"		:	"86076925"			# 
		,	"marketCapital"		:	"1.5152888031201E11"#
		,	"eps"				:	"1.56"				# 每股收益
		,	"pe_ttm"			:	"6.9302"			# 市盈率TTM
		,	"pe_lyr"			:	"6.9302"			# 市盈率LYR
		,	"beta"				:	"0.0"				# beta值		
		,	"totalShares"		:	"14308676139"		# 总股本
		,	"time"				:	"Thu Apr 07 15:14:55 +0800 2016"	# 时间
		,	"afterHours"		:	"0.0"
		,	"afterHoursPct"		:	"0.0"
		,	"afterHoursChg"		:	"0.0"
		,	"updateAt"			:	"1459944006501"		# 更新时间戳
		,	"dividend"			:	"0.174"				# 每股股息
		,	"yield"				:	"1.31"				# 振幅
		,	"turnover_rate"		:	"0.32"				# 换手率
		,	"instOwn"			:	"0.0"
		,	"rise_stop"			:	"11.79"				# 涨停
		,	"fall_stop"			:	"9.65"				# 跌停
		,	"currency_unit"		:	"CNY"				# 货币
		,	"amount"			:	"4.0194905057E8"	# 成交额
		,	"net_assets"		:	"11.2869"			# 
		,	"hasexist"			:	""
		,	"has_warrant"		:	"0"
		,	"type"				:	"11"				# 11=深A，12=沪A
		,	"flag"				:	"1"
		,	"rest_day"			:	""
		,	"amplitude"			:	"1.31"
		,	"lot_size"			:	"100"
		,	"min_order_quantity":	"0"
		,	"max_order_quantity":	"0"
		,	"tick_size"			:	"0.01"
		,	"kzz_stock_symbol"	:	""
		,	"kzz_stock_name"	:	""
		,	"kzz_stock_current"	:	"0.0"
		,	"kzz_convert_price"	:	"0.0"
		,	"kzz_covert_value"	:	"0.0"
		,	"kzz_cpr"			:	"0.0"
		,	"kzz_putback_price"	:	"0.0"
		,	"kzz_convert_time"	:	""
		,	"kzz_redempt_price"	:	"0.0"
		,	"kzz_straight_price":	"0.0"
		,	"kzz_stock_percent"	:	""
		,	"pb"				:	"0.94"
		,	"benefit_before_tax":	"0.0"
		,	"benefit_after_tax"	:	"0.0"
		,	"convert_bond_ratio":	""
		,	"totalissuescale"	:	""
		,	"outstandingamt"	:	""
		,	"maturitydate"		:	""
		,	"remain_year"		:	""
		,	"convertrate"		:	"0.0"
		,	"interestrtmemo"	:	""
		,	"release_date"		:	""
		,	"circulation"		:	"0.0"
		,	"par_value"			:	"0.0"
		,	"due_time"			:	"0.0"
		,	"value_date"		:	""
		,	"due_date"			:	""
		,	"publisher"			:	""
		,	"redeem_type"		:	"T"
		,	"issue_type"		:	""
		,	"bond_type"			:	""
		,	"warrant"			:	""
		,	"sale_rrg"			:	""
		,	"rate"				:	""
		,	"after_hour_vol"	:	"0"
		,	"float_shares"		:	"11804054528"	# 流通股数
		,	"float_market_capital":	"1.2493451188647E11"
		,	"disnext_pay_date"	:	""
		,	"convert_rate"		:	"0.0"
		,	"psr"				:	"1.5758"
		}
}


# 实时盘口
URL_XUEQIU_QUOTEC = lambda symbol : "http://xueqiu.com/v4/stock/quotec.json?code=%s&_=%s" % (symbol, int(time.time()*1000) )
URL_XUEQIU_PANKOU = lambda symbol : "https://xueqiu.com/stock/pankou.json?symbol=%s&_=%s" % (symbol, int(time.time()*1000) )
{	
	"symbol"	:	"SZ300061"
,	"time"		:	"Mar 18, 2016 10:38:12 AM"
,	"bp1"		:	21.4	,	"bc1"		:	15112
,	"bp2"		:	21.36	,	"bc2"		:	20
,	"bp3"		:	21.35	,	"bc3"		:	122
,	"bp4"		:	21.34	,	"bc4"		:	1
,	"bp5"		:	21.33	,	"bc5"		:	1
,	"bp6"		:	0.0		,	"bc6"		:	0
,	"bp7"		:	0.0		,	"bc7"		:	0
,	"bp8"		:	0.0		,	"bc8"		:	0
,	"bp9"		:	0.0		,	"bc9"		:	0
,	"bp10"		:	0.0		,	"bc10"		:	0
,	"current"	:	21.4	,	"sp1"		:	0.0
,	"sc1"		:	0		,	"sp2"		:	0.0
,	"sc2"		:	0		,	"sp3"		:	0.0
,	"sc3"		:	0		,	"sp4"		:	0.0
,	"sc4"		:	0		,	"sp5"		:	0.0
,	"sc5"		:	0		,	"sp6"		:	0.0
,	"sc6"		:	0		,	"sp7"		:	0.0
,	"sc7"		:	0		,	"sp8"		:	0.0
,	"sc8"		:	0		,	"sp9"		:	0.0
,	"sc9"		:	0		,	"sp10"		:	0.0
,	"sc10"		:	0		,	"buypct"	:	100.0
,	"sellpct"	:	0.0		,	"diff"		:	15256	
,	"ratio"		:	100.0
}
