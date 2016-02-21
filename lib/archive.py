# -*- coding: utf8 -*-
from pymongo import MongoClient
import stock_init as stock
import tushare as ts
from datetime import datetime, timedelta
import json

client = MongoClient()
db = client.historyData
# @param	string	stock_code
# @return	datetime.date
def timeToMarket(code):

	d = stock.basicInfo["basicInfo"]["timeToMarket"][str(code)]
	if (d == 0): # To Avoid new stocks who have timeToMarket==0
		return datetime.now().date()
	else:
		return datetime.strptime( str(d) ,	'%Y%m%d' ).date()

# @param	string	stock_code
# Using ts.get_h_data to update (Maily used to create) history data for a stock
def updateHistoryData(code):
	update_necessary = True
	today = datetime.now().date()

	# If not exists, create a document
	record = db.lastUpdated.find_one(
		{
			"code": code
		}
	)

	# SKIP IT
	if ( ( record is not None ) and ( record["onUpdate"] ) ):
		if ( ( datetime.now()-record["onUpdate"] )<timedelta(minutes=1) ):
			return True
	else:
		db.lastUpdated.update_one(
			{
				"code": code
			},
			{
				"$set": {
					"onUpdate": datetime.now()
				}
			},
			upsert = True
		)

	if ( ( record is not None ) and ( record.get("lastUpdated") is not None ) ):
		lastUpdated = record.get("lastUpdated").date()
		startDate = lastUpdated
		# Check lastUpdated date:
		if ( lastUpdated <= today ):
			print code ,", lastUpdated on: ", lastUpdated, " Trying to update..."
		else:
			print code ,", lastUpdated on: ", lastUpdated, " No need to update..."
			update_necessary = False
	else:
		print code , "Trying to create..."
		startDate = timeToMarket(code)

	endDate = startDate
	while (endDate != today):
		if ( ( startDate + timedelta(days=1000) ) > today ):
			endDate = today
		else:
			endDate = startDate + timedelta(days=1000)

		if ( update_necessary == True ):
			forwardAuth = ts.get_h_data(str(code),autype='qfq', start=datetime.strftime(startDate,'%Y-%m-%d'),end=datetime.strftime(endDate,'%Y-%m-%d') )
			if ( forwardAuth is not None ):
				forwardAuth = forwardAuth.reset_index().sort_values('date')
				backwardAuth = ts.get_h_data(str(code), autype='hfq', start=datetime.strftime(startDate,'%Y-%m-%d'),end=datetime.strftime(endDate,'%Y-%m-%d') ).reset_index().sort_values('date')
				noAuth = ts.get_h_data(str(code), autype=None, start=datetime.strftime(startDate,'%Y-%m-%d'),end=datetime.strftime(endDate,'%Y-%m-%d') ).reset_index().sort_values('date')

				for i in range( 0, len(forwardAuth) ):
					pushForwardAuth = json.loads( forwardAuth[i:i+1].to_json( orient='records' ) )[0]
					pushBackwardAuth = json.loads( backwardAuth[i:i+1].to_json( orient='records' ) )[0]
					pushNoAuth = json.loads( noAuth[i:i+1].to_json( orient='records' ) )[0]

					date = datetime.fromtimestamp( int(pushForwardAuth["date"]/1000) ) - timedelta(hours=8)
					db.get_collection(str(code)).update_one(
						{
							"date": date
						},
						{
							"$set": {
								"date": date
							,	"volume": pushForwardAuth["volume"]
							,	"high_forwardAuth": pushForwardAuth["high"]
							,	"low_forwardAuth": pushForwardAuth["low"]
							,	"amount": pushForwardAuth["amount"]
							,	"close_forwardAuth": pushForwardAuth["close"]
							,	"open_forwardAuth": pushForwardAuth["open"]
							,	"high_backwardAuth": pushBackwardAuth["high"]
							,	"low_backwardAuth": pushBackwardAuth["low"]
							,	"close_backwardAuth": pushBackwardAuth["close"]
							,	"open_backwardAuth": pushBackwardAuth["open"]
							,	"high_noAuth": pushNoAuth["high"]
							,	"low_noAuth": pushNoAuth["low"]
							,	"close_noAuth": pushNoAuth["close"]
							,	"open_noAuth": pushNoAuth["open"]
							}
						},
						upsert = True
					)
		startDate = endDate

	db.lastUpdated.update_one(
		{
			"code": code
		},
		{
			"$set": {
				"code": code
			,	"lastUpdated": datetime.now()
			,	"onUpdate": False
			}
		}
	)
	print code," has been updated"

def updateHistoryDataAll():
	# Update/Create historyData USING ts.get_h_data
	for code in stock.codeList:
		updateHistoryData(code)

def updateHistoryDataHist():
	for code in stock.codeList:
		data = ts.get_hist_data( str(code) )

		record = db.lastUpdated.find_one(
			{
			"code": code
			}
		)
