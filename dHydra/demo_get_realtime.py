# -*- coding: utf8 -*-
import dHydra
import time as t
from datetime import datetime


stock = dHydra.Stock()

# time = datetime.now()
time = datetime(1999,1,1,10,0)

start = datetime.now()

time = stock.get_realtime( time )
print "time cost:", (datetime.now()-start)
