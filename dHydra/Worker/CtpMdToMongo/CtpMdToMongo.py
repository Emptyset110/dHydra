# -*- coding: utf-8 -*-
from dHydra.core.Worker import Worker
from dHydra.core.Functions import get_vendor
import pickle
import dHydra.core.util as util
import os
from datetime import datetime, timedelta

class CtpMdToMongo(Worker):
    def __init__(
            self,
            config="CtpMd.json",
            **kwargs
    ):
        super().__init__(**kwargs)  # You ae not supposed to change THIS

        cfg = util.read_config(os.path.join("config", config))
        self.instrument_ids = cfg["instrument_ids"]
        self.__account__ = cfg["account"]

    def __data_handler__(self, msg):
        try:
            if msg["type"] == 'pmessage' or msg["type"] == "message":
                message = pickle.loads(msg["data"])
                if message["ExchangeID"] == "DCE":
                    # 大商所ActionDay错误
                    message["TradingTime"] = datetime(
                        int(message["TradingDay"][0:4]),
                        int(message["TradingDay"][4:6]),
                        int(message["TradingDay"][6:8]),
                        int(message["UpdateTime"][0:2]),
                        int(message["UpdateTime"][3:5]),
                        int(message["UpdateTime"][6:8]),
                        message["UpdateMillisec"]*1000
                    )
                    if message["TradingTime"].hour > 16:
                        message["ActionTime"] = message["TradingTime"] - timedelta(days=1)
                    else:
                        message["ActionTime"] = message["TradingTime"]
                elif message["ExchangeID"] == "CZCE":
                    # 郑商所TradingDay错误
                    message["ActionTime"] = datetime(
                        int(message["ActionDay"][0:4]),
                        int(message["ActionDay"][4:6]),
                        int(message["ActionDay"][6:8]),
                        int(message["UpdateTime"][0:2]),
                        int(message["UpdateTime"][3:5]),
                        int(message["UpdateTime"][6:8]),
                        message["UpdateMillisec"]*1000
                    )
                    if message["ActionTime"].hour > 16:
                        message["TradingTime"] = message["ActionTime"] + timedelta(days=1)
                else:
                    # 上期所是正确的
                    message["TradingTime"] = datetime(
                        int(message["TradingDay"][0:4]),
                        int(message["TradingDay"][4:6]),
                        int(message["TradingDay"][6:8]),
                        int(message["UpdateTime"][0:2]),
                        int(message["UpdateTime"][3:5]),
                        int(message["UpdateTime"][6:8]),
                        message["UpdateMillisec"]*1000
                    )
                    message["ActionTime"] = datetime(
                        int(message["ActionDay"][0:4]),
                        int(message["ActionDay"][4:6]),
                        int(message["ActionDay"][6:8]),
                        int(message["UpdateTime"][0:2]),
                        int(message["UpdateTime"][3:5]),
                        int(message["UpdateTime"][6:8]),
                        message["UpdateMillisec"]*1000
                    )
                message["ActionMinute"] = message["ActionTime"].strftime("%Y-%m-%d %H:%M")
                self.mongo.CtpMarketData.CtpMd.insert_one(message)
        except Exception as e:
            # self.logger.warning(e)
            pass

    def ensure_index(self):
        """
        初始化创建必要索引
        :return:
        """
        self.logger.info("创建索引")
        collection = self.mongo.CtpMarketData.get_collection("CtpMd")
        collection.create_index(
            [
                ("InstrumentID", 1),
                ("TradingTime", 1),
                ("ActionTime", 1)
            ],
            unique=True,
            drop_dups=True,
            name="basic_index"
        )

    def on_start(self):
        """
        进程开始时自动调用
        :return:
        """
        import threading
        self.ensure_index()

        t = threading.Thread(target=self.update_instrument_ids, daemon=True)
        t.start()
        # 订阅
        if self.instrument_ids == set([]):
            pass
        else:
            self.subscribe_instruments(instrument_ids=self.instrument_ids)

    def update_instrument_ids(self):
        import time
        while True:
            instrument_ids = self.__redis__.get(
                "dHydra.Worker.CtpMd.instrument_ids"
            )
            if instrument_ids is not None:
                instrument_ids = pickle.loads(instrument_ids)

            update_set = set(instrument_ids) - set(self.instrument_ids)
            self.instrument_ids = list(set(self.instrument_ids) | update_set)
            if len(update_set) > 0:
                self.subscribe_instruments(instrument_ids=list(update_set))
            time.sleep(60)

    def subscribe_instruments(self, instrument_ids=[]):
        for id in instrument_ids:
            self.subscribe(channel_name="dHydra.Worker.CtpMd."+id)
            print("CtpMdToMongo订阅合约行情:{}".format(id))

    def __producer__(self):
        pass

    def __before_termination__(self, sig):
        """
        It will be called when a TERM signal is received, right before
        sys.exit(0)
        """
        print(
            "CtpMdToMongo is closed. My pid:{}, signal received:{}"
            .format(
                self.pid,
                sig
            )
        )