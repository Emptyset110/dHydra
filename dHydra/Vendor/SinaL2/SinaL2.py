# -*- coding: utf-8 -*-
try:
    from dHydra.core.Vendor import Vendor
except ImportError:
    from .Vendor import Vendor
try:
    from dHydra.core.Functions import *
except ImportError:
    pass
try:
    import dHydra.core.util as util
except ImportError:
    pass
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


class SinaL2(Vendor):

    def __init__(
        self,
        username=None,
        pwd=None,
        symbols=None,
        hq='hq_pjb',
        query=['quotation', 'transaction'],
        # ['quotation', 'orders', 'transaction', 'info']
        on_recv_data=None,   # 收到数据以后的回调函数
        use_logger=True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.on_recv_data = on_recv_data  # 回调函数
        self.ip = util.get_client_ip()
        self.hq = hq
        self.query = query

        # 如果是dHydra框架内调用，则直接用框架内的Sina类，
        # 否则作为独立的类在外部调用
        try:
            self.sina = get_vendor('Sina')
        except Exception as e:
            self.sina = Sina()
        self.is_login = self.login()

        if symbols is None:
            self.symbols = self.sina.get_symbols()
        else:
            self.symbols = symbols
        self.websockets = dict()

    def login(self, verify=False):
        return self.sina.login(verify=verify)

    @asyncio.coroutine
    def get_ws_token(self, qlist):
        req = self.sina.session.get(
            URL_WSKT_TOKEN,
            params=PARAM_WSKT_TOKEN(
                ip=self.ip,
                qlist=qlist,
                hq=self.hq
            ),
            headers=HEADERS_WSKT_TOKEN(),
            timeout=5
        )
        response = re.findall(r'(\{.*\})', req.text)[0]
        response = json.loads(
            response
            .replace(',', ',"')
            .replace('{', '{"')
            .replace(':', '":')
        )
        return response

    # 2cn_是3秒一条的Level2 10档行情
    # 2cn_symbol_0,2cn_symbol_1是逐笔数据
    # 2cn_symbol_orders是挂单数据
    # symbol_i是基本信息
    def generate_qlist(self, qlist, symbol):
        if 'quotation' in self.query:
            if qlist != '':
                qlist += ','
            qlist += "2cn_%s" % (symbol)
        if 'orders' in self.query:
            if qlist != '':
                qlist += ','
            qlist += "2cn_%s_orders" % (symbol)
        if 'transaction' in self.query:
            if qlist != '':
                qlist += ','
            qlist += "2cn_%s_0,2cn_%s_1" % (symbol, symbol)
        if 'info' in self.query:
            if qlist != '':
                qlist += ','
            qlist += "%s_i" % (symbol)
        return qlist

    @asyncio.coroutine
    def create_ws(self, qlist, symbol_list):
        retry = True
        while retry:
            try:
                response = yield from self.get_ws_token(qlist)
                if response["msg_code"] == 1:
                    token = response["result"]
                    self.logger.info(
                        "成功获取到token, symbol_list = {}".format(symbol_list))
                    retry = False
                else:
                    self.logger.warning("{},{}".format(response, qlist))
                    if response["msg_code"] == -11:
                        time.sleep(2)
                        self.logger.warning("尝试重新登录新浪")
                        self.sina.login(verify=False)

            except Exception as e:
                self.logger.warning(e)

        url_wss = 'wss://ff.sinajs.cn/wskt?token=' + token + '&list=' + qlist

        while True:  # 建立websocket连接
            try:
                ws = yield from websockets.connect(url_wss)
                self.websockets[symbol_list[0]] = dict()
                self.websockets[symbol_list[0]]["ws"] = ws
                self.websockets[symbol_list[0]]["qlist"] = qlist
                self.websockets[symbol_list[0]]["token"] = token
                self.websockets[symbol_list[0]]["renewed"] = datetime.now()
                self.websockets[symbol_list[0]]["trial_times"] = 0
                self.logger.info(
                    "成功建立ws连接, {}, symbol_list = {}".format(
                        threading.current_thread().name,
                        symbol_list
                    )
                )
                break
            except Exception as e:
                self.logger.warning(
                    "重试 websockets.connect , {}, symbol_list = {}"
                    .format(
                        threading.current_thread().name,
                        symbol_list
                    )
                )

        while True:
            try:
                message = yield from ws.recv()
                if self.on_recv_data is None:
                    print(message)
                else:
                    self.on_recv_data(message)

            except Exception as e:
                self.logger.error(
                    "{},{}"
                    .format(
                        e,
                        threading.current_thread().name,
                    )
                )
                ws.close()
                yield from self.create_ws(qlist=qlist, symbol_list=symbol_list)

    @asyncio.coroutine
    def renew_token(self, symbol):
        try:
            response = yield from self.get_ws_token(
                self.websockets[symbol]["qlist"]
            )
            if response["msg_code"] == 1:
                token = response["result"]
                self.websockets[symbol]["token"] = token
                self.websockets[symbol]["renewed"] = datetime.now()
                yield from self.websockets[symbol]["ws"].send("*" + token)
                self.websockets[symbol]["trial_times"] = 0
            else:
                self.websockets[symbol]["trial_times"] += 1
                self.logger.info(response["result"])
        except Exception as e:
            self.websockets[symbol]["trial_times"] += 1
            self.logger.warning("token获取失败第{}次，待会儿重试".format(
                self.websockets[symbol]["trial_times"]))

    def websocket_creator(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # 首先从新浪获取股票列表
        symbol_list = self.symbols
        # Cut symbol_list
        weight = (len(self.query) +
                  1) if ('transaction' in self.query) else len(self.query)
        step = int(64 / weight)
        symbol_list_slice = [symbol_list[i: i + step]
                             for i in range(0, len(symbol_list), step)]

        tasks = list()
        for symbol_list in symbol_list_slice:
            qlist = ''
            for symbol in symbol_list:
                qlist = self.generate_qlist(qlist=qlist, symbol=symbol)
            qlist = qlist.lower()
            tasks.append(self.create_ws(qlist, symbol_list=symbol_list))

        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()

    # 用于定时发送空字符串
    def token_sender(self):
        while True:
            self.logger.info("开启话唠模式每55秒的定时与服务器聊天")
            start = datetime.now()
            tasks = list()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            for symbol in self.websockets.keys():
                ws = self.websockets[symbol]["ws"]
                if ws.open:
                    tasks.append(
                        ws.send("*" + self.websockets[symbol]["token"]))

            if len(tasks) > 0:
                loop.run_until_complete(asyncio.wait(tasks))
                loop.close()
            self.logger.info(
                "消息全部发送完毕. 耗时：%s" %
                (datetime.now() - start).total_seconds()
            )
            time.sleep(55)

    # 持续检查一次更新token
    def token_renewer(self):
        while True:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tasks = list()
            for symbol in self.websockets.keys():
                ws = self.websockets[symbol]["ws"]
                if ws.open:
                    if (
                        datetime.now() - self.websockets[symbol]["renewed"]
                    ).total_seconds() > 180:
                        tasks.append(self.renew_token(symbol))

            if len(tasks) > 0:
                loop.run_until_complete(asyncio.wait(tasks))
                loop.close()
            time.sleep(1)

    def start(self):
        """
        """
        # 开启token manager
        tokenRenewer = threading.Thread(target=self.token_renewer)
        tokenSender = threading.Thread(target=self.token_sender)

        websocketCreator = threading.Thread(target=self.websocket_creator)

        tokenRenewer.start()		# 用于更新token
        tokenSender.start()			# 用于定时发送token
        websocketCreator.start()  # 用于建立websocket并接收消息

        tokenRenewer.join()
        tokenSender.join()
        websocketCreator.join()
