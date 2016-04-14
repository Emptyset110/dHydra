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