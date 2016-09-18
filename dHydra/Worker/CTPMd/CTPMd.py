# -*- coding: utf-8 -*-
from dHydra.core.Worker import Worker
import hashlib
import os
import sys
import tempfile
import time
from ctp.futures import ApiStruct, MdApi
import json
import dHydra.core.util as util
from dHydra.core.Functions import *


class CTPMd(Worker):

    def __init__(
        self,
        instrument_ids=["rb1701", "j1701", "i1701"],
        **kwargs
    ):
        super().__init__(**kwargs)  # You are not supposed to change THIS
        self.instrument_ids = instrument_ids

        self.mdapi = get_vendor("CTPMdApi", instrument_ids=self.instrument_ids)
        self.mdapi.OnRtnDepthMarketData = self.OnRtnDepthMarketData

        # self.subscribe(worker_name="CTPMd")

    def __producer__(self):
        self.logger.info("开启CTPMd")
        self.mdapi.Init()
        try:
            while 1:
                time.sleep(10)
        except Exception as e:
            self.logger.warning(e)

    def __data_handler__(self, msg):
        if msg["type"] == 'pmessage' or msg["type"] == "message":
            message = eval(msg["data"])
            print(message)

    def __before_termination__(self, sig):
        """
        It will be called when a TERM signal is received
        , right before sys.exit(0)
        """
        print(
            "Ahhhh! I'm going to be killed. My pid:{}, signal received:{}"
            .format(
                self.pid, sig
            )
        )

    def OnRtnDepthMarketData(self, pDepthMarketData):
        data = dict()
        fields = [
            'ActionDay', 'AskPrice1', 'AskVolume1', 'AveragePrice',
            'BidPrice1', 'BidVolume1', 'ClosePrice',  'CurrDelta',
            'ExchangeID', 'ExchangeInstID', 'HighestPrice',
            'InstrumentID', 'LastPrice', 'LowerLimitPrice',
            'LowestPrice', 'OpenInterest', 'OpenPrice', 'PreClosePrice',
            'PreDelta', 'PreOpenInterest', 'PreSettlementPrice',
            'SettlementPrice', 'TradingDay', 'Turnover',
            'UpdateMillisec', 'UpdateTime', 'UpperLimitPrice', 'Volume'
        ]
        for k in fields:
            data[k] = eval("pDepthMarketData." + k)
        self.publish(data)
