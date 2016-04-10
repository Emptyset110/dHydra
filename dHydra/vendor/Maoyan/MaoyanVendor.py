# -*- coding:utf-8 -*-
"""
dHydra电影数据接口接口：
Created on 03/08/2016
@author: Wen Gu
@contact: emptyset110@gmail.com
"""
import requests
from . import connection as CON
from pandas import DataFrame as df
import pandas
import re

"""
猫眼电影数据
"""
class Maoyan:
	def __init__(self):
		self.session = requests.Session()
		self.get_cities()
		pass

	"""
	初始化获取城市表
	"""
	def get_cities(self):
		self.city = self.session.get("http://pf.maoyan.com/getAllCity.json").json()
		self.allCities = list()
		for key in self.city["allCity"].keys():
			self.allCities += self.city["allCity"][key]
		self.allCities = pandas.DataFrame(self.allCities).set_index("id")
		self.cityTier = self.city["cityTier"]
		self.hotCities = self.city["hotCity"]

	"""
	按日期获取电影票房数据
	"""
	def get_box(self, date):
		self.box = self.session.get(CON.URL_MAOYAN_DATE, params = CON.PARAM_DATE(date) ,headers = CON.HEADERS_MAOYAN)
		return self.box

	"""
	按日期获取电影票房数据，返回dataframe
	"""
	def get_box_dataframe(self, date):
		box_dict = self.get_box(date)
		box_df = df.from_dict(box_dict["data"])
		return box_df

	"""
	按日期获取电影票房数据并导出到csv文件
	"""
	def export_box_csv(self, date):
		box_df = self.get_box_dataframe(date)
		box_df.to_csv( '%s.csv'% date )

	"""
	按电影id获取电影票房数据
	"""
	def get_movie(self, movie):
		movie = self.session.get(CON.URL_MAOYAN_MOVIE, params = CON.PARAM_MOVIEID(movie), headers = CON.HEADERS_MAOYAN)
		return movie.json()

	def get_movie_dataframe(self, movie):
		movie_dict = self.get_movie(movie)
		movie_df = df.from_dict(movie_dict["data"])
		return movie_df

	def export_movie_csv(self, movie):
		movie_dict = self.get_movie(movie)
		df.from_dict(movie_dict).to_csv( "%s-%s-%s.csv" % (movie_dict["releaseDate"], movie_dict["movieName"],str(movie) ) )

	def get_movie_basics(self, movie):
		return self.get_movie(movie)["movieName"]


	"""
	通过电影名/导演/演员名字获取电影id
	Arguments:
	---
		name:	查询关键词
	---
	返回:	默认返回dict，如果设置dataframe=True，则返回DataFrame
	---
		movieid
	"""
	def search_movie_id(self, name):
		response = self.session.get("http://pf.maoyan.com/search?_v_=yes&key=%s&page=1&size=1000"%name).text
		movieid = re.findall(r'<article class=\"indentInner canTouch\" data-url=\"\/movie\/(.*)\">',response)
		return movieid


	"""
	按电影获取它受众比例
	---
	arguments:
		---
		movie:	电影id(可以为空)
		name:	电影名/导演名/演员名字
	---
	return:
		---
		womanRate		:	女性比例
		manRate			:	男性比例
		age_11_15_Rate	:	11-15岁
		age_16_20_Rate	:	16-20岁
		age_21_25_Rate	:	21-25岁
		age_26_30_Rate	:	26-30岁
		age_31_35_Rate	:	31-35岁
		age_36_40_Rate	:	36-40岁
		age_41_50_Rate	:	41-50岁
		updateTime		:	数据更新时间
	---
	e.g.:
		movie.audience_distribution(name="夏洛特烦恼",dataframe=True)
		---
			    womanRate age_11_15_Rate age_16_20_Rate manRate age_31_35_Rate  \
		movieId                                                                  
		246082       57.9            0.3           7.65    42.1          13.62   

		        age_26_30_Rate age_41_50_Rate age_36_40_Rate            updateTime  \
		movieId                                                                      
		246082            33.4           2.67           5.82  2016年03月09日 01:05:41   

		        age_21_25_Rate  
		movieId                 
		246082           36.54
	"""
	def audience_distribution(self, movie=None, name=None, dataframe=False):
		if movie == None:
			movieid = self.search_movie_id(name)
			if len(movieid)==0:
				print("没有填入电影id，且没有查询到与\"%s\"有关的电影"%name)
				return None

		if dataframe:
			result = None
		else:
			result = list()

		for movie in movieid:
			data = self.session.get(
				"http://pf.maoyan.com/movie/viewerStatistic.json?movieId=%s"%movie
			,	headers = CON.HEADERS_MAOYAN
			).json()["data"]
			if data == "":
				continue

			if dataframe:
				data_df = pandas.DataFrame(data, index = [data["movieId"]])
				if (result == None):
					result = data_df
				else:
					result = result.append(data_df)
			else:
				result.append(data)
		print("共找到%d个与\"%s\"相关的电影"%(len(movieid),name))
		print("共找到%d个与\"%s\"相关的电影数据"%(len(movieid),name))
		return result

	"""
	想看指数：按城市，按日期两种排序方式
	"""
	def wish(self,movie=None,name=None,wish_type="date", dataframe=False):
		if movie == None:
			movieid = self.search_movie_id(name)
			if len(movieid)==0:
				print("没有填入电影id，且没有查询到与\"%s\"有关的电影"%name)
				return None

		if dataframe:
			result = None
		else:
			result = list()

		# if (wish_type=="date"):
		# 	data = self.session.get()
		# elif (wish_type=="city"):
		# 	