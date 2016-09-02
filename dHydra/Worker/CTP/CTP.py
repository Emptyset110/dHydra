# -*- coding: utf-8 -*-
from dHydra.core.Worker import Worker
from .dHydraMdApi import dHydraMdApi
import hashlib
import os
import sys
import tempfile
import time
from ctp.futures import ApiStruct, MdApi
import json
import dHydra.core.util as util


class CTP(Worker):

    def __init__(
        self,
        broker_id=None,
        user_id=None,
        password=None,
        instrument_ids=None,
        register_front=None,
        **kwargs
    ):
        super().__init__(**kwargs)  # You are not supposed to change THIS

        # The following is customized:
        # In this case, the worker is listening to itself.
        self.__listener__.subscribe([self.redis_key + "Pub"])

        # Note (IMPORTANT):
        # broker_id, user_id, password, instrument_ids, register_front should
        # be bytes
        cfg = util.read_config(os.getcwd() + "/ctp.json")
        if "broker_id" in cfg:
            broker_id = cfg["broker_id"]
        if "password" in cfg:
            password = cfg["password"]
        if "user_id" in cfg:
            user_id = cfg["user_id"]
        if "register_front" in cfg:
            register_front = cfg["register_front"]
        if instrument_ids is None:
            self.logger.warning("没有初始化订阅的合约品种，将采用默认品种作为演示：")
            instrument_ids = [
                'IF1609', 'IF1612', 'IF1703', 'IC1609',
                'IF1610', 'IC1610', 'IC1612', 'IC1703'
            ]
            self.logger.warning("{}".format(instrument_ids))
        if (broker_id is None) or (user_id is None) or (password is None) \
                or (register_front is None):
            import sys
            self.logger.error("CTP连接信息不完整")
            sys.exit(0)
        self.broker_id = broker_id.encode()
        self.user_id = user_id.encode()
        self.password = password.encode()
        self.instrument_ids = list()
        self.register_front = register_front.encode()
        for i in instrument_ids:
            self.instrument_ids.append(i.encode())

    # def __data_handler__(self, msg):
    #     if msg["type"] == "message" or msg["type"] == "pmessage":
    #         print( msg["data"] )

    def __producer__(self):
        mdapi = dHydraMdApi(self.broker_id, self.user_id,
                            self.password, self.instrument_ids)
        mdapi.RegisterFront(self.register_front)
        mdapi.OnRtnDepthMarketData = self.OnRtnDepthMarketData
        mdapi.Init()
        try:
            while 1:
                time.sleep(10)
        except Exception as e:
            self.logger.warning(e)

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
            'ActionDay', 'AskPrice1', 'AskPrice2', 'AskPrice3',
            'AskPrice4', 'AskPrice5', 'AskVolume1', 'AskVolume2',
            'AskVolume3', 'AskVolume4', 'AskVolume5', 'AveragePrice',
            'BidPrice1', 'BidPrice2', 'BidPrice3', 'BidPrice4',
            'BidPrice5', 'BidVolume1', 'BidVolume2',  'BidVolume3',
            'BidVolume4', 'BidVolume5', 'ClosePrice',  'CurrDelta',
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
