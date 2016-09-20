# -*- coding: utf-8 -*-
import hashlib
import os
import sys
import tempfile
import time
from dHydra.core.Vendor import Vendor
import dHydra.core.util as util
import threading
from ctp.futures import ApiStruct, MdApi


class CTPMdApi(MdApi, Vendor):

    def __init__(
        self,
        instrument_ids=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.request_id = 0

        # Note (IMPORTANT):
        # broker_id, user_id, password, instrument_ids, market_front should
        # be bytes
        cfg = util.read_config(os.getcwd() + "/ctp.json")
        if "broker_id" in cfg:
            broker_id = cfg["broker_id"]
        if "password" in cfg:
            password = cfg["password"]
        if "user_id" in cfg:
            user_id = cfg["user_id"]
        if "market_front" in cfg:
            market_front = cfg["market_front"]
        if instrument_ids is None:
            self.logger.warning("没有初始化订阅的合约品种，将采用默认品种作为演示：")
            import pandas
            instrument_ids = list(pandas.DataFrame.from_csv(
                os.getcwd() + "/data/instruments.csv"
            ).index)
            self.logger.info("订阅品种：{}".format(instrument_ids))
        if (broker_id is None) or (user_id is None) or (password is None) \
                or (market_front is None):
            import sys
            self.logger.error("CTP连接信息不完整")
            sys.exit(0)
        self.broker_id = broker_id.encode()
        self.user_id = user_id.encode()
        self.password = password.encode()
        self.instrument_ids = list()
        self.market_front = market_front.encode()
        for i in instrument_ids:
            self.instrument_ids.append(i.encode())

        self.Create()
        self.RegisterFront(self.market_front)

        t = threading.Thread(target=self.start_listening)
        t.setDaemon(True)
        t.start()

    def start_listening(self):
        self.Init()
        try:
            while 1:
                time.sleep(10)
        except Exception as e:
            self.logger.warning(e)

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
        self.logger.info(data)
        self.logger.info(
            "Time:{}\nInstrument:{}\nPrice:{}\nVolume:{}"
            .format(
                data["UpdateTime"] + b"." +
                str(data["UpdateMillisec"]).encode(),
                data["InstrumentID"],
                data["LastPrice"],
                data["Volume"]
            )
        )

    def Create(self):
        """创建MdApi
        @param pszFlowPath 存贮订阅信息文件的目录，默认为当前目录
        @return 创建出的UserApi
        modify for udp marketdata
        """
        dir = b''.join((b'ctp.futures', self.broker_id, self.user_id))
        dir = hashlib.md5(dir).hexdigest()
        dir = os.path.join(tempfile.gettempdir(), dir, 'Md') + os.sep
        if not os.path.isdir(dir):
            os.makedirs(dir)
        MdApi.Create(self, os.fsencode(
            dir) if sys.version_info[0] >= 3 else dir)

    def GetApiVersion(self):
        """获取API的版本信息
        @retrun 获取到的版本号
        """
        return ''

    def Release(self):
        """删除接口对象本身
        @remark 不再使用本接口对象时,调用该函数删除接口对象
        """

    def RegisterFront(self, front):
        """注册前置机网络地址
        @param pszFrontAddress：前置机网络地址。
        @remark 网络地址的格式为：“protocol:
        ipaddress:port”，如：”tcp:
        127.0.0.1:17001”。
        @remark “tcp”代表传输协议，“127.0.0.1”代表服务器地址。”17001”代表服务器端口号。
        """
        if isinstance(front, bytes):
            return MdApi.RegisterFront(self, front)
        for front in front:
            MdApi.RegisterFront(self, front)

    def OnFrontConnected(self):
        """
        当客户端与交易后台建立起通信连接时（还未登录前），该方法被调用。
        """
        print('OnFrontConnected: Login...')
        req = ApiStruct.ReqUserLogin(
            BrokerID=self.broker_id, UserID=self.user_id, Password=self.password)
        self.request_id += 1
        self.ReqUserLogin(req, self.request_id)

    def OnFrontDisconnected(self, nReason):
        """当客户端与交易后台通信连接断开时，该方法被调用。当发生这个情况后，API会自动重新连接，客户端可不做处理。
        @param nReason 错误原因
                0x1001 网络读失败
                0x1002 网络写失败
                0x2001 接收心跳超时
                0x2002 发送心跳失败
                0x2003 收到错误报文
        """
        print('OnFrontDisconnected:', nReason)

    def OnHeartBeatWarning(self, nTimeLapse):
        """心跳超时警告。当长时间未收到报文时，该方法被调用。
        @param nTimeLapse 距离上次接收报文的时间
        """
        print('OnHeartBeatWarning:', nTimeLapse)

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """登录请求响应"""
        print('OnRspUserLogin:', pRspInfo)
        if pRspInfo.ErrorID == 0:  # Success
            self.SubscribeMarketData(self.instrument_ids)
            print('GetTradingDay:', self.GetTradingDay())

    def OnRspSubMarketData(
        self,
        pSpecificInstrument,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """订阅行情应答"""
        print('OnRspSubMarketData:', pRspInfo)

    def OnRspUnSubMarketData(
        self,
        pSpecificInstrument,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """取消订阅行情应答"""
        print('OnRspUnSubMarketData:', pRspInfo)

    def OnRspError(self, pRspInfo, nRequestID, bIsLast):
        """错误应答"""
        print('OnRspError:', pRspInfo)

    def OnRspUserLogout(self, pUserLogout, pRspInfo, nRequestID, bIsLast):
        print('OnRspUserLogout:', pRspInfo)

    def OnRspSubMarketData(
        self,
        pSpecificInstrument,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """订阅行情应答"""
        # self.logger.info(
        #     "订阅行情应答 -- pSpecificInstrument:{},pRspInfo:{},nRequestID:{},"
        #     "bIsLast:{}"
        #     .format(pSpecificInstrument, pRspInfo, nRequestID, bIsLast)
        # )

    def OnRspUnSubMarketData(
        self,
        pSpecificInstrument,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """取消订阅行情应答"""

    def OnRspSubForQuoteRsp(
        self,
        pSpecificInstrument,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """订阅询价应答"""

    def OnRspUnSubForQuoteRsp(
        self,
        pSpecificInstrument,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """取消订阅询价应答"""
