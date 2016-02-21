# -*- coding: utf8 -*-
import dHydra
import time as t
from datetime import datetime

# Get an instance of stock
stock = dHydra.Stock()

time = datetime.now()
while True:
	try:
		start = datetime.now()

		if (start.hour<9 or start.hour>15):
			print "It's Too Early or Too late", start
			t.sleep(360)
			continue
		time = stock.get_realtime( time )
		print "time cost:", (datetime.now()-start)
	except Exception,e:
		print e
