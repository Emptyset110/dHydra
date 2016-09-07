# -*- coding: utf-8 -*-
import hashlib
import os
import sys
import tempfile
import time
from ctp.futures import ApiStruct, MdApi


class dHydraMdApi(MdApi):

    def __init__(self, brokerID, userID, password, instrumentIDs):
        self.requestID = 0
        self.brokerID = brokerID
        self.userID = userID
        self.password = password
        self.instrumentIDs = instrumentIDs
        self.Create()

    def Create(self):
        """创建MdApi
        @param pszFlowPath 存贮订阅信息文件的目录，默认为当前目录
        @return 创建出的UserApi
        modify for udp marketdata
        """
        dir = b''.join((b'ctp.futures', self.brokerID, self.userID))
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
            BrokerID=self.brokerID, UserID=self.userID, Password=self.password)
        self.requestID += 1
        self.ReqUserLogin(req, self.requestID)

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
            print('GetTradingDay:', self.GetTradingDay())
            self.SubscribeMarketData(self.instrumentIDs)

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

    def OnRtnDepthMarketData(self, pDepthMarketData):
        print(pDepthMarketData)

    def OnRspSubMarketData(
        self,
        pSpecificInstrument,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """订阅行情应答"""
        self.logger.info(
            "订阅行情应答 -- pSpecificInstrument:{},pRspInfo:{},nRequestID:{},"
            "bIsLast:{}"
            .format(pSpecificInstrument, pRspInfo, nRequestID, bIsLast)
        )

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
