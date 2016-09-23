# -*- coding: utf-8 -*-
from dHydra.core.Worker import Worker
from dHydra.core.Functions import *
import dHydra.core.util as util
from datetime import datetime
from .connection import *
import time
import requests
import websockets
import getpass
import base64
import rsa
import binascii
import json
import asyncio
import threading
import functools
import re
import gc
import os


class SinaL2(Worker):

    def __init__(
        self,
        username=None,
        pwd=None,
        symbols=["sz000001"],
        hq='hq_pjb',
        query=['quotation', 'transaction'],
        # ['quotation', 'orders', 'transaction', 'info']
        to_mongo=False,
        **kwargs
    ):
        super().__init__(**kwargs)  # You are not supposed to change THIS

        self.sina_l2 = get_vendor(
            name="SinaL2",
            symbols=symbols,
            hq=hq,
            query=query,
            username=username,
            pwd=pwd,
            on_recv_data=self.on_recv_data
        )
        self.to_mongo = to_mongo
        self.total = 0
        self.count = 0

    def on_recv_data(self, message):
        parsed_msg = util.ws_parse(message, to_dict=True)
        self.publish(parsed_msg)
        if self.to_mongo:
            for data in parsed_msg:
                try:
                    self.total += 1
                    if data["data_type"] == "transaction":
                        self.count += 1
                        # 自己建立unique索引
                        result = self.mongo.stock.l2_deal.insert_one(data)
                    elif data["data_type"] == "quotation":
                        self.count += 1
                        result = self.mongo.stock.l2_quotation.insert_one(
                            data
                        )  # 自己建立unique索引
                except Exception as e:
                    self.logger.warning("Insert error:{}".format(e))
                    self.total += 1

    def __producer__(self):
        """
        """
        self.sina_l2.start()
        while True:
            time.sleep(30)

    def __before_termination__(self, sig):
        """
        It will be called when a TERM signal is received,
        right before sys.exit(0)
        """
        print(
            "Ahhhh! I'm going to be killed. My pid:{}, signal received:{}"
            .format(
                self.pid, sig
            )
        )
