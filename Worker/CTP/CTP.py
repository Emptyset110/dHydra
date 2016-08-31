# -*- coding: utf-8 -*-
from dHydra.core.Worker import Worker
from .dHydraMdApi import dHydraMdApi
import hashlib, os, sys, tempfile, time
from ctp.futures import ApiStruct, MdApi
import json

class CTP(Worker):
    def __init__(self,broker_id = None, user_id = None, password = None, instrument_ids = None, register_front = None, **kwargs):
        super().__init__(**kwargs)  # You ae not supposed to change THIS

        # The following is customized:
        # In this case, the worker is listening to itself.
        self.__listener__.subscribe( [ self.redis_key + "Pub" ] )

        # Note (IMPORTANT):
        # broker_id, user_id, password, instrument_ids, register_front should be bytes
        # load stuff from CTP.json
        self.broker_id = broker_id
        self.user_id = user_id
        self.password = password
        self.instrument_ids = instrument_ids

    def __data_handler__(self, msg):
        if msg["type"] == "message":
            print( eval(msg["data"]) )

    def __producer__(self):
        mdapi = dHydraMdApi(b'9999', b'068246', b'dHydra110!', [b"IF1608", b"IF1609", b"IF1612", b"IF1703", b"IC1608", b"IC1609", b"IC1612", b"IC1703"])
        mdapi.RegisterFront(b'tcp://180.168.146.187:10010')
        mdapi.OnRtnDepthMarketData = self.OnRtnDepthMarketData
        mdapi.Init()
        try:
            while 1:
                time.sleep(10)
        except Exception as e:
            self.logger.warning(e)

    def __before_termination__(self, sig):
        """
        It will be called when a TERM signal is received, right before sys.exit(0)
        """
        print("Ahhhh! I'm going to be killed. My pid:{}, signal received:{}".format(self.pid, sig ) )

    def OnRtnDepthMarketData(self, pDepthMarketData):
        data = dict()
        fields = ['ActionDay', 'AskPrice1', 'AskPrice2', 'AskPrice3', \
        'AskPrice4', 'AskPrice5', 'AskVolume1', 'AskVolume2', 'AskVolume3', \
        'AskVolume4', 'AskVolume5', 'AveragePrice', 'BidPrice1', 'BidPrice2', \
        'BidPrice3', 'BidPrice4', 'BidPrice5', 'BidVolume1', 'BidVolume2', \
        'BidVolume3', 'BidVolume4', 'BidVolume5', 'ClosePrice', 'CurrDelta', \
        'ExchangeID', 'ExchangeInstID', 'HighestPrice', 'InstrumentID', \
        'LastPrice', 'LowerLimitPrice', 'LowestPrice', 'OpenInterest', \
        'OpenPrice', 'PreClosePrice', 'PreDelta', 'PreOpenInterest', \
        'PreSettlementPrice', 'SettlementPrice', 'TradingDay', 'Turnover', \
        'UpdateMillisec', 'UpdateTime', 'UpperLimitPrice', 'Volume']
        for k in fields:
            data[k] = eval("pDepthMarketData."+k)
        self.publish(data)
