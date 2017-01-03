# -*- coding: utf-8 -*-
from dHydra.core.Worker import Worker
import os
import sys
import time
from ctp.futures import ApiStruct, MdApi
import pickle
import dHydra.core.util as util
from dHydra.core.Functions import get_vendor
import threading
import traceback


class CtpMd(Worker):

    def __init__(
        self,
        account="ctp_real.json",
        config="CtpMd.json",
        instrument_ids=[],  # 如果有传入instrument_ids，以传入的为准
        simnow=False,       # 如果account配置的是simnow的debug账户，请务必将这个flag设置为True
                            # 以免扰乱依赖此Worker广播数据的数据处理模块
        **kwargs
    ):
        """
        行情源
        :param account:
        :param config:
        :param instrument_ids:
        :param simnow:
        :param kwargs:
        """
        super().__init__(**kwargs)  # You are not supposed to change THIS
        self.simnow = simnow
        self.mdapi = None
        if instrument_ids == []:
            cfg = util.read_config(os.path.join("config",config))
            self.instrument_ids = cfg["instrument_ids"]
        else:
            self.instrument_ids = instrument_ids
        self.__account__ = account

    def get_all_instruments(self):
        trader = get_vendor("CtpTraderApi", account=self.__account__)
        result = list()
        instruments = list()
        while instruments == list():
            time.sleep(3)
            try:
                instruments = list(trader.instruments.InstrumentID)
            except Exception as e:
                trader.prepare_instruments_info()
                print("获取instruments失败，1秒后重试")
        trader.Release()
        for item in instruments:
            if ("&" in item) or (" " in item):
                continue
            else:
                result.append(item)
        # 确保我们配置文件中规定的instruments必须在列表中
        result = list(set(result) | set(self.instrument_ids))

        return result

    def on_start(self):
        # update_instruments and re-init
        t = threading.Thread(target=self.restart_thread,daemon=True)
        t.start()

    def restart_thread(self):
        from datetime import datetime
        if self.mdapi is None:
            self.init_mdapi()
        else:
            while True:
                now = datetime.now()
                if now.hour == 8 and now.minute == 55:
                    self.logger.info("重启MdApi")
                    self.init_mdapi()
                else:
                    self.logger.info("{}".format(now))
                time.sleep(60)


    def init_mdapi(self):
        if self.mdapi is not None:
            try:
                self.mdapi.Release()
            except Exception as e:
                self.logger.error("MdApi Release Failed: {}".format(e))

        instrument_ids = self.get_all_instruments()
        self.logger.info(
            "成功获取Instruments: {}".format(
                len(instrument_ids)
            )
        )
        self.mdapi = get_vendor(
            "CtpMdApi",
            account=self.__account__,
            instrument_ids=instrument_ids
        )
        self.mdapi.OnRtnDepthMarketData = self.OnRtnDepthMarketData
        self.logger.info("开启CtpMd")
        self.mdapi.Init()

    def __producer__(self):
        # 订阅rb1701用如下方式
        # self.subscribe(channel_name="dHydra.Worker.CtpMd.rb1701")
        #
        # 这里是为了 Join
        try:
            while 1:
                time.sleep(10)
        except Exception as e:
            traceback.print_exc()
            self.logger.warning(e)


    def __data_handler__(self, msg):
        # 以下是测试时的代码
        # if msg["type"] == 'pmessage' or msg["type"] == "message":
        #     message = pickle.loads(msg["data"])
        pass

    def __before_termination__(self, sig):
        """
        It will be called when a TERM signal is received
        , right before sys.exit(0)
        """
        print(
            "CtpMd is going to be closed. My pid:{}, signal received:{}"
            .format(
                self.pid, sig
            )
        )

    def OnRtnDepthMarketData(self, pDepthMarketData):
        data = {
            'TradingDay': pDepthMarketData.TradingDay.decode(),
            'InstrumentID': pDepthMarketData.InstrumentID.decode(),
            'ExchangeID': pDepthMarketData.ExchangeID.decode(),
            'ExchangeInstID': pDepthMarketData.ExchangeInstID.decode(),
            'LastPrice': pDepthMarketData.LastPrice,
            'PreSettlementPrice': pDepthMarketData.PreSettlementPrice,
            'PreClosePrice': pDepthMarketData.PreClosePrice,
            'PreOpenInterest': pDepthMarketData.PreOpenInterest,  # 昨持仓量, double
            'OpenPrice': pDepthMarketData.OpenPrice,
            'HighestPrice': pDepthMarketData.HighestPrice,
            'LowestPrice': pDepthMarketData.LowestPrice,
            'Volume': pDepthMarketData.Volume,
            'Turnover': pDepthMarketData.Turnover,
            'OpenInterest': pDepthMarketData.OpenInterest,
            'ClosePrice': pDepthMarketData.ClosePrice,
            'SettlementPrice': pDepthMarketData.SettlementPrice,
            'UpperLimitPrice': pDepthMarketData.UpperLimitPrice,
            'LowerLimitPrice': pDepthMarketData.LowerLimitPrice,
            'PreDelta': pDepthMarketData.PreDelta,
            'CurrDelta': pDepthMarketData.CurrDelta,
            'UpdateTime': pDepthMarketData.UpdateTime.decode(),
            'UpdateMillisec': pDepthMarketData.UpdateMillisec,
            'BidPrice1': pDepthMarketData.BidPrice1,
            'BidVolume1': pDepthMarketData.BidVolume1,
            'BidPrice2': pDepthMarketData.BidPrice2,
            'BidVolume2': pDepthMarketData.BidVolume2,
            'BidPrice3': pDepthMarketData.BidPrice3,
            'BidVolume3': pDepthMarketData.BidVolume3,
            'BidPrice4': pDepthMarketData.BidPrice4,
            'BidVolume4': pDepthMarketData.BidVolume4,
            'BidPrice5': pDepthMarketData.BidPrice5,
            'BidVolume5': pDepthMarketData.BidVolume5,
            'AskPrice1': pDepthMarketData.AskPrice1,
            'AskVolume1': pDepthMarketData.AskVolume1,
            'AskPrice2': pDepthMarketData.AskPrice2,
            'AskVolume2': pDepthMarketData.AskVolume2,
            'AskPrice3': pDepthMarketData.AskPrice3,
            'AskVolume3': pDepthMarketData.AskVolume3,
            'AskPrice4': pDepthMarketData.AskPrice4,
            'AskVolume4': pDepthMarketData.AskVolume4,
            'AskPrice5': pDepthMarketData.AskPrice5,
            'AskVolume5': pDepthMarketData.AskVolume5,
            'AveragePrice': pDepthMarketData.AveragePrice,
            'ActionDay': pDepthMarketData.ActionDay.decode(),
        }

        if self.simnow==True:
            data["simnow"] = True
        self.__redis__.publish(
            "dHydra.Worker.CtpMd."+data["InstrumentID"],
            pickle.dumps(data)
        )