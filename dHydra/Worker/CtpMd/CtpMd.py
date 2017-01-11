# -*- coding: utf-8 -*-
from dHydra.core.Worker import Worker
import os
import time
from ctp.futures import ApiStruct, MdApi
from .CtpMiniTrader import CtpMiniTrader
import pickle
import dHydra.core.util as util
from dHydra.core.Functions import get_vendor
import threading
import traceback


class CtpMd(Worker):

    def __init__(
        self,
        config="CtpMd.json",
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
        self.mdapi = None
        self.__config__ = config
        cfg = util.read_config(os.path.join("config", config))
        self.__account__ = cfg["account"]
        self.init_config_instrument_ids()

    def init_config_instrument_ids(self):
        cfg = util.read_config(os.path.join("config", self.__config__))
        self.instrument_ids = cfg["instrument_ids"]

    def check_instruments_update(self):
        while 1:
            try:
                instruments = list(self.ctp_mini_trader.instruments.InstrumentID)
                new_set = set([])
                for item in instruments:
                    if isinstance(item, str):
                        if "&" in item or " " in item:
                            continue
                        else:
                            new_set.add(item)
                    else:
                        print(
                            "check_instruments_update, warning: item = ",
                            item, instruments
                        )
                update_list = list(new_set - set(self.instrument_ids))

                self.instrument_ids.extend(update_list)
                self.__redis__.set(
                    "dHydra.Worker.CtpMd.instrument_ids",
                    pickle.dumps(self.instrument_ids)
                )
                if len(update_list) > 0:
                    for i in range(0, len(update_list)):
                        update_list[i] = update_list[i].encode()
                    # print("CtpMd Worker Subscribe", update_list)
                    self.mdapi.SubscribeMarketData(update_list)
            except Exception as e:
                traceback.print_exc()
                self.logger.warning(e)
            time.sleep(60)

    def on_start(self):
        # 初始化instrument_ids
        self.ctp_mini_trader = CtpMiniTrader(account=self.__account__)
        while not self.ctp_mini_trader.is_connected:
            time.sleep(1)
        while self.ctp_mini_trader.instruments_last_updated is None:
            self.ctp_mini_trader.prepare_instruments_info()
            time.sleep(1)

        # update_instruments and re-init
        t = threading.Thread(target=self.check_instruments_update,daemon=True)
        t.start()

        # 初始化mdapi
        self.init_mdapi()
        self.__redis__.set(
            "dHydra.Worker.CtpMd.instrument_ids",
            pickle.dumps(self.instrument_ids)
        )

    def init_mdapi(self):
        self.mdapi = get_vendor(
            "CtpMdApi",
            account=self.__account__,
            instrument_ids=self.instrument_ids
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

        self.__redis__.publish(
            "dHydra.Worker.CtpMd."+data["InstrumentID"],
            pickle.dumps(data)
        )