# -*- coding: utf-8 -*-
from dHydra.core.Worker import Worker
from dHydra.core.Functions import *
import dHydra.core.util as util
import time
import pickle
import threading


class SinaL2(Worker):

    def __init__(
        self,
        symbols=["sz000001"],
        hq='hq_pjb',
        query=['quotation', 'transaction', "orders"],
        # ['quotation', 'orders', 'transaction', 'info']
        # to_mongo=False,
        **kwargs
    ):
        super().__init__(**kwargs)  # You are not supposed to change THIS
        self.symbols = symbols
        self.hq = hq
        self.query = query

        self.count_transaction = 0
        self.count_quotation = 0
        self.count_orders = 0
        self.trading_date = util.get_trading_date()

    def init_sina_l2(self):
        self.sina_l2 = get_vendor(
            name="SinaL2",
            symbols=self.symbols,
            hq=self.hq,
            query=self.query,
            on_recv_data=self.on_recv_data
        )

    def start_sina_l2(self):
        self.init_sina_l2()
        self.sina_l2.start()

    def on_start(self):
        self.logger.info("Trading Date: {}".format(self.trading_date))
        # 启动一个线程，来更新trading_date
        self.thread_update_trading_date = threading.Thread(
            target=self.update_trading_date,
            daemon=True
        )
        self.thread_update_trading_date.start()

    def update_trading_date(self):
        while True:
            try:
                time.sleep(600)
                trading_date = util.get_trading_date()
                if len(trading_date) == 10 and trading_date != self.trading_date:
                    self.logger.info("更新交易日：{}".format(trading_date))
                    self.trading_date = trading_date
            except Exception:
                pass

    def on_recv_data(self, message):
        parsed_msg = util.ws_parse(
            message,
            trading_date = self.trading_date,
            to_dict=True
        )

        # 更新redis中行情内容
        for data in parsed_msg:
            try:
                if data["data_type"] == "orders":
                    self.publish(
                        data = pickle.dumps(data),
                        channel_name = "dHydra.SinaL2." +
                                       data["symbol"] + ".orders"
                    )
                elif data["data_type"] == "quotation":
                    self.publish(
                        data = pickle.dumps(data),
                        channel_name = "dHydra.SinaL2." +
                                       data["symbol"] + ".quotation"
                    )
                elif data["data_type"] == "transaction":
                    self.publish(
                        data = pickle.dumps(data),
                        channel_name = "dHydra.SinaL2." +
                                       data["symbol"] + ".transaction"
                    )
            except Exception as e:
                self.logger.error(e)

        self.publish(pickle.dumps(parsed_msg))

    def __producer__(self):
        """
        """
        import datetime
        import threading
        thread_sina_l2 = threading.Thread(
            target=self.start_sina_l2,
            daemon=True
        )
        thread_sina_l2.start()

        while True:
            time.sleep(60)
            current = datetime.datetime.now()
            if current.time() > datetime.time(15, 0, 0)\
                    or current.time() < datetime.time(9, 0, 0):
                if self.sina_l2 is not None:
                    if not self.sina_l2.stopped:
                        self.logger.info("非盘中，暂停收行情")
                        self.sina_l2.stop()
            elif current.time() > datetime.time(9,0,0) \
                    and current.date() == datetime.date(
                        int(self.trading_date[0:4]),
                        int(self.trading_date[5:7]),
                        int(self.trading_date[8:10])
                    ):
                # 除非指数的日期与今天的日期相同，才会开启
                if (self.sina_l2 is None) or (self.sina_l2.terminated == True):
                    self.logger.info("开启SinaL2: {}".format(self.trading_date))
                    thread_sina_l2 = threading.Thread(
                        target=self.start_sina_l2,
                        daemon=True
                    )
                    thread_sina_l2.start()

    def __before_termination__(self, sig):
        """
        It will be called when a TERM signal is received,
        right before sys.exit(0)
        """
        print(
            "I'm going to be killed. My pid:{}, signal received:{}"
            .format(
                self.pid, sig
            )
        )
