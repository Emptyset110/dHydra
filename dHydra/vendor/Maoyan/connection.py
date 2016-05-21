# -*- coding: utf-8 -*-
"""
Config
Created on 03/08/2016
@description:	Connection for movie.py
@author: 		Wen Gu
@contact: 		emptyset110@gmail.com
"""

HEADERS_MAOYAN = {
	'Accept' : '*/*'
,	'Accept-Encoding'	:	'gzip, deflate, sdch'
,	'Accept-Language'	:	'en-US,en;q=0.8'
,	'Connection'		:	'keep-alive'
,	'Host'				:	'pf.maoyan.com'
,	'Referer'			:	'http://pf.maoyan.com/'
,	'User-Agent'		:	'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36'
,	'X-Requested-With'	:	'XMLHttpRequest'
}

URL_MAOYAN_DATE = 'http://pf.maoyan.com/history/date/box.json'
URL_MAOYAN_MOVIE = 'http://pf.maoyan.com/history/movie/box.json'

URL_MAOYAN_BASEINFO = 'http://pf.maoyan.com/movie/baseinfo.json'
#http://pf.maoyan.com/movie/baseinfo.json?movie=246286
URL_MAOYAN_BOXINFO = 'http://pf.maoyan.com/movie/boxinfo.json'
#http://pf.maoyan.com/movie/boxinfo.json?movie=246286

URL_MAOYAN_SEATRANK = 'http://pf.maoyan.com/show/seatRank.json'

# 返回特定城市
URL_MAOYAN_SHOWRATE = "http://pf.maoyan.com/show/rate/rank.json?periodType=0&cityType=0&cityName=%E6%9D%AD%E5%B7%9E"

# 返回所有城市
URL_MAOYAN_SHOWRANK = 'http://pf.maoyan.com/show/rate/city/rank.json'

# http://pf.maoyan.com/show/rate/city/rank.json?showDate=2015-01-15&periodType=0
URL_MAOYAN_ATTENDRANK = 'http://pf.maoyan.com/attend/rate/rank.json'

URL_MAOYAN_WISH_DATE = 'http://pf.maoyan.com/movie/wish/date.json'
URL_MAOYAN_WISH_CITY = 'http://pf.maoyan.com/movie/wish/city.json'

PARAM_WISH = lambda movie: {
	"movie"		:	movie
}

PARAM_DATE = lambda date: {
	"date"	:	date
,	"cnt"	:	10
}

PARAM_MOVIEID = lambda movie: {
	"movie"		:	movie
,	"offset"	:	0
,	"limit"		:	10000
}

PARAM_SEATRANK = lambda showDate, periodType, cityType, cityName: {
	"showDate"		:	showDate
,	"periodType"	:	periodType
,	"cityType"		:	cityType
,	"cityName"		:	cityName
}