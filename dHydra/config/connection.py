# -*- coding: utf8 -*-
"""
Connection Settings
Created on 02/26/2016
@description:	Used for 
@author: 		Wen Gu
@contact: 		emptyset110@gmail.com
"""

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
,	"Referer"			:	"http://xueqiu.com/hq"
,	"User-Agent"		:	"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36"
,	"X-Requested-With"	:	"XMLHttpRequest"
}

CONST_XUEQIU_QUOTE_ORDER_COLUMN = "symbol,name,current,chg,percent,last_close,open,high,low,volume,amount,market_capital,pe_ttm,high52w,low52w,hasexist"
CONST_XUEQIU_QUOTE_COLUMN = "symbol,exchange,code,name,current,percentage,change,open,high,low,close,last_close,high52week,low52week,volume,volumeAverage,marketCapital,eps,pe_ttm,pe_lyr_beta,totalShares,time,afterHours,afterHoursPct,afterHoursChg,updateAt,dividednd,yield,turnover_rate,instOwn,rise_stop,fall_stop,currency_unit,amount,net_assets,hasexist,has_warrant,type,flag,rest_day,amplitude,lot_size,tick_size,kzz_stock_symbol,kzz_stock_name,kzz_stock_current,kzz_convert_price,kzz_convert_value"
URL_XUEQIU_HQ = "https://xueqiu.com/hq"
URL_XUEQIU_QUOTE_ORDER = lambda page,columns,stockType : "http://xueqiu.com/stock/quote_order.json?page=%s&size=90&order=desc&exchange=CN&stockType=%s&column=%s&orderBy=symbol&_=%s"	% ( page,stockType, columns,int(time.time()*1000) )
URL_XUEQIU_QUOTE = lambda symbol : "http://xueqiu.com/v4/stock/quote.json?code=%s&_=%s" % (symbol, int(time.time()*1000) )
URL_XUEQIU_PANKOU = lambda symbol : "http://xueqiu.com/stock/pankou.json?symbol=%s&_=%s" % (symbol, int(time.time()*1000) )
#"{"symbol":"SZ300061","time":"Mar 18, 2016 10:38:12 AM","bp1":21.4,"bc1":15112,"bp2":21.36,"bc2":20,"bp3":21.35,"bc3":122,"bp4":21.34,"bc4":1,"bp5":21.33,"bc5":1,"bp6":0.0,"bc6":0,"bp7":0.0,"bc7":0,"bp8":0.0,"bc8":0,"bp9":0.0,"bc9":0,"bp10":0.0,"bc10":0,"current":21.4,"sp1":0.0,"sc1":0,"sp2":0.0,"sc2":0,"sp3":0.0,"sc3":0,"sp4":0.0,"sc4":0,"sp5":0.0,"sc5":0,"sp6":0.0,"sc6":0,"sp7":0.0,"sc7":0,"sp8":0.0,"sc8":0,"sp9":0.0,"sc9":0,"sp10":0.0,"sc10":0,"buypct":100.0,"sellpct":0.0,"diff":15256,"ratio":100.0}"

"""
tushare
"""
URL_TUSHARE_BASICS = "http://218.244.146.57/static/all.csv"