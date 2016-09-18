# -*- coding: utf-8 -*-
from dHydra.core.Functions import get_vendor
from dHydra.core.Vendor import Vendor
import dHydra.core.util as util
import threading
from ctp.futures import ApiStruct
import os
import pandas


class EasyUncle(Vendor):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ctp = None
        self.stock = None

        self.ctp_position = list()
        self.ctp_position_detail = list()

    def init_ctp(self, account="ctp.json"):
        self.ctp = get_vendor("CTPTraderApi", account=account)
        # 初始化持仓情况
        self.ctp.OnRspQryInvestorPosition = self.OnRspQryInvestorPosition
        self.ctp.OnRspQryInvestorPositionDetail =\
            self.OnRspQryInvestorPositionDetail
        self.ctp.OnRspQryTradingAccount = self.OnRspQryTradingAccount
        self.ctp.OnRspQryOrder = self.OnRspQryOrder
        self.get_position_detail_ctp()
        self.get_position_ctp()

    def get_position_ctp(self):
        self.ctp.req_qry_investor_position()

    def get_position_detail_ctp(self):
        self.ctp.req_qry_investor_position_detail()

    def OnRspQryOrder(
        self,
        pOrder,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询报单响应"""
        order = self.ctp.to_dict(pOrder)
        order["StatusMsg"] = order["StatusMsg"].decode("gbk")
        self.logger.info(
            "OnRspQryOrder: Received"
            "order: {}\n"
            "is_last: {}"
            .format(order, bIsLast)
        )

    def OnRspQryTradingAccount(
        self,
        pTradingAccount,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询资金账户响应"""
        # pRspInfo is None
        trading_account = self.ctp.to_dict(pTradingAccount)
        for k in trading_account.keys():
            if isinstance(trading_account[k], bytes):
                trading_account[k] = trading_account[k].decode("utf-8")
        self.logger.info(
            "OnRspQryTradingAccount: Received"
            ", no operation is followed"
            "pTradingAccount:{}".format(json.dumps(trading_account, indent=2))
        )

    def OnRspQryInvestorPositionDetail(
        self,
        pInvestorPositionDetail,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询投资者持仓明细响应"""
        investor_position_detail = self.ctp.to_dict(pInvestorPositionDetail)
        if investor_position_detail != {}:
            self.ctp_position_detail.append(investor_position_detail)
        self.logger.info(
            "InvestorPositionDetail: {}".format(investor_position_detail)
        )
        if bIsLast is True:
            self.ctp_position_detail_df =\
                pandas.DataFrame(self.ctp_position_detail)
            print(self.ctp_position_detail_df)

    def OnRspQryInvestorPosition(
        self,
        pInvestorPosition,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询投资者持仓响应"""
        investor_position = self.ctp.to_dict(pInvestorPosition)
        if investor_position != {}:
            self.ctp_position.append(investor_position)

        self.logger.info(
            "OnRspQryInvestorPosition: Received"
            ", no operation is followed"
            "InvestorPosition:{}\n"
            "IsLast:{}".format(investor_position, bIsLast)
        )
        if bIsLast is True:
            self.ctp_position_df =\
                pandas.DataFrame(self.ctp_position)
            print(self.ctp_position_df)
