# -*- coding: utf8 -*-
"""
股票接口类 
Created on 02/17/2016
@author: Wen Gu
@contact: emptyset110@gmail.com
"""
from pymongo import MongoClient
from datetime import datetime, timedelta
from pandas import DataFrame
import tushare as ts
import json
import pandas

class Stock:

	def __init__(self):
		# connect to mongodb named: stock
		client = MongoClient()
		self.db = client.stock
		self.updated = datetime.now()
		self.outstanding = list()
		# INITIALIZATION: CHECKING UPDATES
		print "Checking Updates..."
		lastUpdated = self.db.lastUpdated.find_one( {"list" : {"$exists":True, "$ne": None},"list" : {"$exists":True, "$ne": None} } )
		self.update_basic_info()
		[self.codeList, self.basicInfo] = self.fetch_basic_info()

	## NOT IN USE ##
	def fetch_classification(self):
		# 数据来源自新浪财经的行业分类/概念分类/地域分类
		print "Trying: get_today_all"
		today_all = ts.get_today_all() #一次性获取今日全部股价
		set_today_all = set(today_all.T.values[0])

		print "Trying: get_industry_classified"
		industry_classified = ts.get_industry_classified()
		set_industry_classified = set(industry_classified.T.values[0])

		print "Trying: get_area_classified"
		area_classified = ts.get_area_classified()
		set_area_classified = set(area_classified.T.values[0])

		print "Trying: get_concept_classified"
		concept_classified = ts.get_concept_classified()
		set_concept_classified = set(concept_classified.T.values[0])

		print "Trying: get_sme_classified"
		sme_classified = ts.get_sme_classified()
		set_sme_classified = set(sme_classified.T.values[0])

		return [
					today_all
				,	set_today_all
				,	industry_classified
				,	set_industry_classified
				,	area_classified
				,	set_area_classified
				,	concept_classified
				,	set_concept_classified
				,	sme_classified
				,	set_sme_classified
				]

	# Will automatically call "update_basic_info" if needed
	# @return [self.codeList, self.basicInfo]
	def fetch_basic_info(self):
		result = self.db.basicInfo.find_one( 
			{
				"lastUpdated": {"$exists":True, "$ne": None}
			} 
		)
		if (result != None):
			codeList = result["basicInfo"]["name"].keys()
		else:
			update_basic_info()
			[codeList, result] = self.fetch_basic_info()

		self.updated = datetime.now()
		return [codeList, result]

	# Update stock.basicInfo in mongodb
	def update_basic_info(self):
		update_necessary = False
		basicInfo = self.db.basicInfo.find_one( 
			{
				"lastUpdated": {"$exists":True, "$ne": None}
			} 
		)
		if (basicInfo == None):
			print "No record of basicInfo found. A new record is to be created......"
			update_necessary = True
		else:
			# Criteria For Updating
			if  ( basicInfo["lastUpdated"].date() < datetime.now().date() ):
				update_necessary = True
				print "Stock Basic Info last updated on: ", basicInfo["lastUpdated"].date(), "trying to update right now..."
			else:
				print "Stock Basic Info last updated on: ", basicInfo["lastUpdated"].date(), " NO NEED to update right now..."
			
		if (update_necessary):
			basicInfo = ts.get_stock_basics()
			
			result = self.db.basicInfo.update_one(
				{
					"lastUpdated": {"$exists": True, "$ne": None}
				},
				{
					"$set": {
						"lastUpdated": datetime.now(),
						"basicInfo": json.loads(ts.get_stock_basics().to_json()),
						"codeList": list(basicInfo.index)
					}
				},
				upsert = True
			)

	# fetch realtime data using TuShare
	#	Thanks to tushare.org
	def fetch_realtime(self):
		i = 0
		while ( self.codeList[i:i+500] != [] ):
			if (i==0):
				realtime = ts.get_realtime_quotes( self.codeList[i : i+500] )
			else:
				realtime = realtime.append( ts.get_realtime_quotes( self.codeList[i : i+500] ), ignore_index=True )
			i += 500

		# Get the datetime
		data_time = datetime.strptime( realtime.iloc[0]["date"] + " " + realtime.iloc[0]["time"] , '%Y-%m-%d %H:%M:%S')
		code = realtime["code"]
		num = len(realtime)
		realtime["time"] = data_time
		# Drop Useless colulmns
		realtime = realtime.drop( realtime.columns[[0,6,7,30]] ,axis = 1)
		# Convert string to float
		realtime = realtime.convert_objects(convert_dates=False,convert_numeric=True,convert_timedeltas=False)

		# TODO: UGLY HERE. Need a better logic for updating
		if ( ( self.updated.date() == datetime.now().date() ) & ( self.updated.hour >= 9 ) ):
			if ( self.outstanding == [] ):
				for i in range(0,num):
					self.outstanding.append( self.basicInfo["basicInfo"]["outstanding"][code[i]] )
		else:
			print "The basicInfo is outdated. Trying to update basicInfo..."
			[ self.codeList, self.basicInfo ] = self.fetch_basic_info()
			self.outstanding = list()
			for i in range(0,num):
				self.outstanding.append( self.basicInfo["basicInfo"]["outstanding"][code[i]] )

		# Compute turn_over_rate
		realtime["turn_over_rate"] = realtime["volume"]/self.outstanding/100
		realtime["code"] = code

		return realtime

	# First fetch_realtime, then insert it into mongodb
	def get_realtime(self,time):
		realtime = self.fetch_realtime()

		data_time = realtime.iloc[0]['time']
		if (data_time>time):
			time = data_time
		else:
			print "No need", time
			return data_time

		self.db.realtime.insert_many( realtime.iloc[0:2900].to_dict(orient='records') )
		print "data_time", data_time
		return time