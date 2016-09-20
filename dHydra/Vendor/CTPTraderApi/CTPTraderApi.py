from ctp.futures import ApiStruct, TraderApi
from dHydra.core.Vendor import Vendor
import dHydra.core.util as util
import os
import json
import inspect


class CTPTraderApi(Vendor, TraderApi):

    def __init__(
        self,
        account="ctp.json",
        user_id=None,
        password=None,
        broker_id=None,
        investor_id=None,
        trade_front=None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # 将语义化的"buy","sell"映射到ApiStruct.D_Buy, ApiStruct.D_Sell
        self.direction_map = {
            "buy": ApiStruct.D_Buy,
            "sell": ApiStruct.D_Sell,
        }
        self.direction_inverse_map = {
            ApiStruct.D_Buy: "buy",
            ApiStruct.D_Sell: "sell",
        }
        # 将语义化的"open","close"映射到ApiStruct.OF_Open, ApiStruct.OF_Close
        self.offset_flag_map = {
            "open": ApiStruct.OF_Open,
            "close": ApiStruct.OF_Close,
        }
        self.offset_flag_inverse_map = {
            ApiStruct.OF_Open: "open",
            ApiStruct.OF_Close: "close",
        }

        # 重写传入的方法
        for item in kwargs.keys():
            if not getattr(self, item, None):
                setattr(self, item, kwargs[item])

        # Get Api Version
        self.api_version = self.GetApiVersion().decode("utf-8")
        self.logger.info("API Version:{}".format(self.api_version))
        self.trading_day = None

        self.request_id = 0              # 操作请求编号
        self.order_ref = 0

        self.is_connected = False       # 连接状态
        self.is_logined = False            # 登录状态

        if isinstance(account, dict):
            cfg = account
        else:
            if account[0] != '/':
                account = '/' + account
            account_path = os.getcwd() + "{}".format(account)
            cfg = util.read_config(account_path)
        try:
            if investor_id is None:
                self.investor_id = cfg["investor_id"].encode()
            if user_id is None:
                self.user_id = cfg["user_id"].encode()                # 账号
            if password is None:
                self.password = cfg["password"].encode()            # 密码
            if broker_id is None:
                self.broker_id = cfg["broker_id"].encode()            # 经纪商代码
            if trade_front is None:
                self.trade_front = cfg["trade_front"].encode()  # 服务器地址
        except Exception as e:
            self.logger.error(
                "没有从{}读取到正确格式的配置"
                .format(account_path)
            )
            return None

        self.front_id = None            # 前置机编号
        self.session_id = None          # 会话编号

        self.connect(
            self.user_id,
            self.password,
            self.broker_id,
            self.trade_front
        )

    def to_dict(self, o):
        if o is not None:
            return dict((k, getattr(o, k)) for k, t in o._fields_)
        else:
            return dict()

    def buy(self, instrument_id, volume, price):
        """
        买开=开多=buy
        """
        print("买开：{},{},{}".format(instrument_id, volume, price))

        if isinstance(instrument_id, str):
            instrument_id = instrument_id.encode()
        self.req_order_insert(
            instrument_id=instrument_id,
            price=price,
            volume=volume,
            direction=ApiStruct.D_Buy,
            offset_flag=ApiStruct.OFEN_Open
        )

        print("买开完毕：{},{},{}".format(instrument_id, volume, price))

    def cover(self, instrument_id, volume, price):
        """
        买平=平空=cover
        """
        if isinstance(instrument_id, str):
            instrument_id = instrument_id.encode()
        self.req_order_insert(
            instrument_id=instrument_id,
            price=price,
            volume=volume,
            direction=ApiStruct.D_Buy,
            offset_flag=ApiStruct.OFEN_Close
        )

    def short(self, instrument_id, volume, price):
        """
        卖开=开空=short
        """
        if isinstance(instrument_id, str):
            instrument_id = instrument_id.encode()
        self.req_order_insert(
            instrument_id=instrument_id,
            price=price,
            volume=volume,
            direction=ApiStruct.D_Sell,
            offset_flag=ApiStruct.OFEN_Open
        )

    def sell(self, instrument_id, volume, price):
        """
        卖平=平多=sell
        """
        if isinstance(instrument_id, str):
            instrument_id = instrument_id.encode()
        self.req_order_insert(
            instrument_id=instrument_id,
            price=price,
            volume=volume,
            direction=ApiStruct.D_Sell,
            offset_flag=ApiStruct.OFEN_Close
        )

    def connect(self, user_id, password, broker_id, trade_front):
        """初始化连接"""
        self.user_id = user_id                # 账号
        self.password = password            # 密码
        self.broker_id = broker_id            # 经纪商代码
        self.trade_front = trade_front              # 服务器地址

        # 如果尚未建立服务器连接，则进行连接
        if not self.is_connected:
            # 创建C++环境中的API对象，这里传入的参数是需要用来保存.con文件的文件夹路径
            self.Create(b"ctp_data")

            # 注册服务器地址
            self.RegisterFront(self.trade_front)

            # 订阅公共流
            self.SubscribePublicTopic(ApiStruct.TERT_RESTART)

            # 订阅私有流
            self.SubscribePrivateTopic(ApiStruct.TERT_RESTART)

            # 初始化连接，成功会调用OnFrontConnected
            self.Init()

            self.logger.info(
                "CTPTraderApi.connect: Initialization has completed."
            )

        # 若已经连接但尚未登录，则进行登录
        else:
            if not self.is_logined:
                self.req_user_login()

    def on_front_connected(self):
        pass

    def OnFrontConnected(self):
        """
        当客户端与交易后台建立起通信连接时（还未登录前），该方法被调用。
        """
        self.is_connected = True
        self.logger.info(
            "Successfully connected to the Trader Front, "
            "about to login."
        )

        # 对外暴露接口
        self.on_front_connected()

        self.req_user_login()

    def req_user_login(self):
        """连接服务器"""
        # 如果填入了用户名密码等，则登录
        if self.user_id and self.password and self.broker_id:
            pReqUserLogin = ApiStruct.ReqUserLogin(
                BrokerID=self.broker_id,
                UserID=self.user_id,
                Password=self.password
            )
            self.request_id += 1
            self.ReqUserLogin(
                pReqUserLogin=pReqUserLogin,
                nRequestID=self.request_id
            )

    def on_rsp_user_login(self, rsp_user_login, rsp_info, request_id, is_last):
        pass

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """登录请求响应"""
        rsp_user_login = self.to_dict(pRspUserLogin)
        rsp_info = self.to_dict(pRspInfo)

        if pRspInfo.ErrorID == 0:
            self.front_id = pRspUserLogin.FrontID
            self.session_id = pRspUserLogin.SessionID
            self.is_logined = True

            self.logger.info(
                "交易服务器登录完成:{}".format(pRspInfo.ErrorMsg.decode("gbk"))
            )

            # 对外接口
            self.on_rsp_user_login(
                rsp_user_login=rsp_user_login,
                rsp_info=rsp_info,
                request_id=nRequestID,
                is_last=bIsLast
            )

            # 确认结算信息
            self.request_id += 1
            req = ApiStruct.QrySettlementInfoConfirm(
                BrokerID=self.broker_id,
                InvestorID=self.investor_id,
            )
            self.ReqSettlementInfoConfirm(
                req,
                self.request_id
            )

        # 否则，推送错误信息
        else:
            self.logger.error(
                "error_id: {}, error_msg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )
            # 在某些情况下，会出现无法自动连接
            # 这里我们手动进行一下重连
            self.connect(
                self.user_id,
                self.trader.password,
                self.broker_id,
                self.trade_front
            )

    def req_qry_trading_account(self, currency_id=b"CNY"):
        """
        获取资金账户
        """
        pQryTradingAccount = ApiStruct.QryTradingAccount(
            BrokerID=self.broker_id,
            InvestorID=self.investor_id,
            CurrencyID=currency_id
        )
        self.request_id += 1
        self.ReqQryTradingAccount(
            pQryTradingAccount=pQryTradingAccount,
            nRequestID=self.request_id
        )
        self.logger.info(
            "CTPTraderApi.req_qry_trading_account: "
            "Finish sending request for trading account"
        )

    def on_rsp_qry_trading_account(self, trading_account, request_id, is_last):
        pass

    def OnRspQryTradingAccount(
        self,
        pTradingAccount,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询资金账户响应"""
        # pRspInfo is None
        trading_account = self.to_dict(pTradingAccount)
        for k in trading_account.keys():
            if isinstance(trading_account[k], bytes):
                trading_account[k] = trading_account[k].decode("gbk")
        self.logger.info(
            "OnRspQryTradingAccount: Received"
            ", no operation is followed"
            "pTradingAccount:{}\n"
            "nRequestID:{}\n, bIsLast:{}"
            .format(json.dumps(trading_account, indent=2), nRequestID, bIsLast)
        )
        self.on_rsp_qry_trading_account(
            trading_account=trading_account,
            request_id=nRequestID,
            is_last=bIsLast
        )

    def on_front_disconnected(self, reason):
        pass

    def OnFrontDisconnected(self, nReason):
        """当客户端与交易后台通信连接断开时，该方法被调用。当发生这个情况后，
        API会自动重新连接，客户端可不做处理。
        @param nReason 错误原因
                0x1001 网络读失败
                0x1002 网络写失败
                0x2001 接收心跳超时
                0x2002 发送心跳失败
                0x2003 收到错误报文
        """
        self.is_connected = False
        self.is_logined = False
        reason_map = {
            0x1001: "网络读失败",
            0x1002: "网络写失败",
            0x2001: "接收心跳超时",
            0x2002: "发送心跳失败",
            0x2003: "收到错误报文"
        }
        self.logger.warning(
            "交易服务器断开, {}"
            .format(
                reason_map[nReason]
            )
        )
        # 对外接口
        self.on_front_disconnected(reason_map[nReason])

    def on_heart_beat_warning(self, time_lapse):
        pass

    def OnHeartBeatWarning(self, nTimeLapse):
        """心跳超时警告。当长时间未收到报文时，该方法被调用。
        @param nTimeLapse 距离上次接收报文的时间
        """
        self.logger.warning(
            "心跳超时警告, 距离上次接收报文的时间:{}"
            .format(nTimeLapse)
        )
        # 对外接口
        self.on_heart_beat_warning(time_lapse=nTimeLapse)

    def req_authenticate(self):
        pass

    def OnRspAuthenticate(
        self,
        pRspAuthenticate,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """客户端认证响应"""
        if pRspInfo.ErrorID == 0:
            result = {
                "BrokerID": pRspAuthenticate.BrokerID,
                "UserID": pRspAuthenticate.UserID,
                "UserProductInfo": pRspAuthenticate.UserProductInfo
            }
            self.logger.info(
                "OnRspAuthenticate: Received, no operation is followed.\n"
                "pRspAuthenticate: {}".format(
                    json.dumps(result, indent=2)
                )
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspAuthenticate: ErrorID:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def req_user_logout(self):
        pUserLogout = ApiStruct.UserLogout(
            BrokerID=self.broker_id,
            UserID=self.user_id
        )
        self.request_id += 1
        self.ReqUserLogout(pUserLogout, self.request_id)
        self.logger.info(
            "req_user_logout: Request Sent"
            "with request_id:{}".format(self.request_id)
        )

    def OnRspUserLogout(self, pUserLogout, pRspInfo, nRequestID, bIsLast):
        """登出回报"""
        # 如果登出成功，推送日志信息
        if pRspInfo.ErrorID == 0:
            self.is_logined = False
            self.logger.info('OnRspUserLogout: Success')
            user_logout = self.to_dict(pUserLogout)
            self.logger.info(
                "pUserLogout: {}".format(user_logout)
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspUserLogout: ErrorID:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspUserPasswordUpdate(
        self,
        pUserPasswordUpdate,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """用户口令更新请求响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspUserPasswordUpdate: Received, no operation is followed."
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspUserPasswordUpdate:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspTradingAccountPasswordUpdate(
        self,
        pTradingAccountPasswordUpdate,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """资金账户口令更新请求响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspTradingAccountPasswordUpdate: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspTradingAccountPasswordUpdate:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def req_order_insert(
        self,
        instrument_id=b'',
        price=0.0,
        volume=0,
        direction=ApiStruct.D_Buy,
        offset_flag=ApiStruct.OFEN_Close,
    ):
        """
        CTP的下单种类
            普通限价单:
            order_price_type=ApiStruct.OPT_LimitPrice
        """
        self.request_id += 1
        self.order_ref += 1
        if isinstance(instrument_id, str):
            instrument_id = instrument_id.encode()
        pInputOrder = ApiStruct.InputOrder(
            InstrumentID=instrument_id,
            LimitPrice=price,
            VolumeTotalOriginal=volume,
            Direction=direction,  # 多空标志
            CombOffsetFlag=offset_flag,  # 开平标志
            RequestID=self.request_id,
            OrderRef=str(self.order_ref).encode(),
            BrokerID=self.broker_id,
            InvestorID=self.investor_id,
            UserID=self.user_id,
            OrderPriceType=ApiStruct.OPT_LimitPrice,  # 默认限价单
            CombHedgeFlag=ApiStruct.HF_Speculation,  # 投机单
            TimeCondition=ApiStruct.TC_GFD,  # 当日有效
            # ctp测试服务器下：
            #     TC_IOC 立即完成否则撤销（未知，始终撤销）
            #     TC_GFS 本节有效（不被支持的报单类型）
            #     TC_GFD 当日有效（可用）
            #     TC_GTC 撤销前有效
            #     TC_GFA 集合竞价有效
            #             GTDDate=gtd_date,
            VolumeCondition=ApiStruct.VC_AV,  #
            MinVolume=1,
            ContingentCondition=ApiStruct.CC_Immediately,
            #             StopPrice=0.0,
            #             ForceCloseReason=force_close_reason,
            IsAutoSuspend=0,
            #             BusinessUnit=business_unit,
            UserForceClose=0,  # 用户强平标志
            #             IsSwapOrder=is_swap_order,
        )
        self.ReqOrderInsert(
            pInputOrder=pInputOrder,
            nRequestID=self.request_id
        )

    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        """报单录入请求响应"""
        # pRspInfo is None
        input_order = self.to_dict(pInputOrder)
        self.logger.info(
            "OnRspOrderInsert: Received"
            ", no operation is followed"
            "InputOrder:{}".format(input_order)
        )

    def req_qry_investor_position_detail(self):
        """请求查询投资者持仓明细"""
        pQryInvestorPositionDetail = ApiStruct.QryInvestorPositionDetail(
            BrokerID=self.broker_id,
            InvestorID=self.investor_id
        )
        self.request_id += 1
        self.ReqQryInvestorPositionDetail(
            pQryInvestorPositionDetail=pQryInvestorPositionDetail,
            nRequestID=self.request_id
        )

    def OnRspQryInvestorPositionDetail(
        self,
        pInvestorPositionDetail,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询投资者持仓明细响应"""
        investor_position_detail = self.to_dict(pInvestorPositionDetail)
        self.logger.info(
            "InvestorPositionDetail: {}".format(investor_position_detail)
        )

    def req_qry_investor_position_combine_detail(self):
        pQryInvestorPositionCombineDetail =\
            ApiStruct.QryInvestorPositionCombineDetail(
                BrokerID=self.broker_id,
                InvestorID=self.investor_id
            )
        self.request_id += 1
        self.ReqQryInvestorPositionCombineDetail(
            pQryInvestorPositionCombineDetail,
            self.request_id
        )

    def OnRspQryInvestorPositionCombineDetail(
        self,
        pInvestorPositionCombineDetail,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        print(pInvestorPositionCombineDetail)
        """请求查询投资者持仓明细响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryInvestorPositionCombineDetail: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryInvestorPositionCombineDetail:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspParkedOrderInsert(
        self,
        pParkedOrder,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """预埋单录入请求响应"""
        if pRspInfo.ErrorID == 0:
            parked_order = self.to_dict(pParkedOrder)
            self.logger.info(
                "OnRspParkedOrderInsert: Received"
                ", no operation is followed"
                "ParkedOrder:{}".format(parked_order)
            )

    def OnRspParkedOrderAction(
        self,
        pParkedOrderAction,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """预埋撤单录入请求响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspParkedOrderAction: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspParkedOrderAction:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspOrderAction(
        self,
        pInputOrderAction,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """报单操作请求响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspOrderAction: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspOrderAction:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def req_query_max_order_volume(
        self,
        instrument_id,
        direction="buy",
        offset_flag="open",
    ):
        """查询最大报单数量请求"""
        if isinstance(instrument_id, str):
            instrument_id = instrument_id.encode()

        direction = self.direction_map[direction]
        offset_flag = self.offset_flag_map[offset_flag]

        pQueryMaxOrderVolume = ApiStruct.QueryMaxOrderVolume(
            BrokerID=self.broker_id,
            InvestorID=self.investor_id,
            InstrumentID=instrument_id,
            Direction=direction,
            OffsetFlag=offset_flag,
        )
        self.request_id += 1
        self.ReqQueryMaxOrderVolume(
            pQueryMaxOrderVolume=pQueryMaxOrderVolume,
            nRequestID=self.request_id
        )

    def OnRspQueryMaxOrderVolume(
        self,
        pQueryMaxOrderVolume,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """查询最大报单数量响应"""
        query_max_order_volume = self.to_dict(pQueryMaxOrderVolume)
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQueryMaxOrderVolume: Received"
                ", no operation is followed"
                "QueryMaxOrderVolume:{}"
                .format(query_max_order_volume)
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQueryMaxOrderVolume:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspSettlementInfoConfirm(
        self,
        pSettlementInfoConfirm,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """投资者结算结果确认响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspSettlementInfoConfirm: Received"
                ", no operation is followed"
            )
            settlement_info_confirm = self.to_dict(pSettlementInfoConfirm)
            print(pSettlementInfoConfirm)
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspSettlementInfoConfirm:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspRemoveParkedOrder(
        self,
        pRemoveParkedOrder,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """删除预埋单响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspRemoveParkedOrder: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspRemoveParkedOrder:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspRemoveParkedOrderAction(
        self,
        pRemoveParkedOrderAction,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """删除预埋撤单响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspRemoveParkedOrderAction: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspRemoveParkedOrderAction:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspExecOrderInsert(
        self,
        pInputExecOrder,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """执行宣告录入请求响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspExecOrderInsert: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspExecOrderInsert:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspExecOrderAction(
        self,
        pInputExecOrderAction,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """执行宣告操作请求响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspExecOrderAction: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspExecOrderAction:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspForQuoteInsert(
        self,
        pInputForQuote,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """询价录入请求响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspForQuoteInsert: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspForQuoteInsert:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQuoteInsert(
        self,
        pInputQuote,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """报价录入请求响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQuoteInsert: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQuoteInsert:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQuoteAction(
        self,
        pInputQuoteAction,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """报价操作请求响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQuoteAction: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQuoteAction:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspCombActionInsert(
        self,
        pInputCombAction,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """申请组合录入请求响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspCombActionInsert: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspCombActionInsert:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def req_qry_order(self):
        pQryOrder = ApiStruct.QryOrder(
            BrokerID=self.broker_id,
            InvestorID=self.investor_id
        )
        self.request_id += 1
        self.ReqQryOrder(pQryOrder=pQryOrder, nRequestID=self.request_id)

    def OnRspQryOrder(
        self,
        pOrder,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询报单响应"""
        order = self.to_dict(pOrder)
        if order:
            order["StatusMsg"] = order["StatusMsg"].decode("gbk")
        self.logger.info(
            "OnRspQryOrder: Received"
            "order: {}\n"
            "is_last: {}"
            .format(order, bIsLast)
        )

    def OnRspQryTrade(
        self,
        pTrade,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询成交响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryTrade: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryTrade:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def req_qry_investor_position(self):
        """
        查询持仓
        """
        pQryInvestorPosition = ApiStruct.QryInvestorPosition(
            BrokerID=self.broker_id,
            InvestorID=self.investor_id
        )
        self.request_id += 1
        self.ReqQryInvestorPosition(
            pQryInvestorPosition=pQryInvestorPosition,
            nRequestID=self.request_id
        )

    def OnRspQryInvestorPosition(
        self,
        pInvestorPosition,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询投资者持仓响应"""
        investor_position = self.to_dict(pInvestorPosition)

        self.logger.info(
            "OnRspQryInvestorPosition: Received"
            ", no operation is followed"
            "InvestorPosition:{}\n"
            "IsLast:{}".format(investor_position, bIsLast)
        )

    def OnRspQryInvestor(
        self,
        pInvestor,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询投资者响应"""
        self.logger.info(
            "OnRspQryInvestor: Received"
            ", no operation is followed"
        )

    def OnRspQryTradingCode(
        self,
        pTradingCode,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询交易编码响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryTradingCode: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryTradingCode:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryInstrumentMarginRate(
        self,
        pInstrumentMarginRate,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询合约保证金率响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryInstrumentMarginRate: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryInstrumentMarginRate:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryInstrumentCommissionRate(
        self,
        pInstrumentCommissionRate,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询合约手续费率响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryInstrumentCommissionRate: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryInstrumentCommissionRate:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryExchange(
        self,
        pExchange,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询交易所响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryExchange: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryExchange:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryProduct(self, pProduct, pRspInfo, nRequestID, bIsLast):
        """请求查询产品响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryProduct: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryProduct:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryInstrument(self, pInstrument, pRspInfo, nRequestID, bIsLast):
        """请求查询合约响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryInstrument: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryInstrument:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryDepthMarketData(
        self,
        pDepthMarketData,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询行情响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryDepthMarketData: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryDepthMarketData:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQrySettlementInfo(
        self,
        pSettlementInfo,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询投资者结算结果响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQrySettlementInfo: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQrySettlementInfo:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryTransferBank(
        self,
        pTransferBank,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询转帐银行响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryTransferBank: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryTransferBank:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryNotice(self, pNotice, pRspInfo, nRequestID, bIsLast):
        """请求查询客户通知响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryNotice: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryNotice:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQrySettlementInfoConfirm(
        self,
        pSettlementInfoConfirm,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询结算信息确认响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQrySettlementInfoConfirm: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQrySettlementInfoConfirm:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryCFMMCTradingAccountKey(
        self,
        pCFMMCTradingAccountKey,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """查询保证金监管系统经纪公司资金账户密钥响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryCFMMCTradingAccountKey: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryCFMMCTradingAccountKey:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryEWarrantOffset(
        self,
        pEWarrantOffset,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询仓单折抵信息响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryEWarrantOffset: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryEWarrantOffset:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryInvestorProductGroupMargin(
        self,
        pInvestorProductGroupMargin,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询投资者品种/跨品种保证金响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryInvestorProductGroupMargin: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryInvestorProductGroupMargin:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryExchangeMarginRate(
        self,
        pExchangeMarginRate,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询交易所保证金率响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryExchangeMarginRate: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryExchangeMarginRate:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryExchangeMarginRateAdjust(
        self,
        pExchangeMarginRateAdjust,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询交易所调整保证金率响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryExchangeMarginRateAdjust: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryExchangeMarginRateAdjust:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryExchangeRate(
        self,
        pExchangeRate,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询汇率响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryExchangeRate: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryExchangeRate:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQrySecAgentACIDMap(
        self,
        pSecAgentACIDMap,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询二级代理操作员银期权限响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQrySecAgentACIDMap: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQrySecAgentACIDMap:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryProductExchRate(
        self,
        pProductExchRate,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询产品报价汇率"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryProductExchRate: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryProductExchRate:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryOptionInstrTradeCost(
        self,
        pOptionInstrTradeCost,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询期权交易成本响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryOptionInstrTradeCost: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryOptionInstrTradeCost:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryOptionInstrCommRate(
        self,
        pOptionInstrCommRate,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询期权合约手续费响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryOptionInstrCommRate: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryOptionInstrCommRate:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryExecOrder(self, pExecOrder, pRspInfo, nRequestID, bIsLast):
        """请求查询执行宣告响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryExecOrder: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryExecOrder:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryForQuote(self, pForQuote, pRspInfo, nRequestID, bIsLast):
        """请求查询询价响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryForQuote: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryForQuote:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryQuote(self, pQuote, pRspInfo, nRequestID, bIsLast):
        """请求查询报价响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryQuote: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryQuote:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryCombInstrumentGuard(
        self,
        pCombInstrumentGuard,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询组合合约安全系数响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryCombInstrumentGuard: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryCombInstrumentGuard:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryCombAction(self, pCombAction, pRspInfo, nRequestID, bIsLast):
        """请求查询申请组合响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryCombAction: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryCombAction:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryTransferSerial(
        self,
        pTransferSerial,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询转帐流水响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryTransferSerial: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryTransferSerial:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryAccountregister(
        self,
        pAccountregister,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询银期签约关系响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryAccountregister: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryAccountregister:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspError(self, pRspInfo, nRequestID, bIsLast):
        """错误应答"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspError: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspError:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRtnOrder(self, pOrder):
        """报单通知"""
        order = self.to_dict(pOrder)
        order["StatusMsg"] = order["StatusMsg"].decode("gbk")
        self.logger.info(
            "OnRtnOrder: Received"
            ", no operation is followed\n"
            "order:{}"
            .format(order)
        )

    def OnRtnTrade(self, pTrade):
        """成交通知"""
        trade = self.to_dict(pTrade)
#         trade["StatusMsg"]=trade["StatusMsg"].decode("gbk")
        self.logger.info(
            "OnRtnTrade: Received"
            ", no operation is followed"
            "trade:{}".format(trade)
        )

    def OnErrRtnOrderInsert(self, pInputOrder, pRspInfo):
        """报单录入错误回报"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnErrRtnOrderInsert: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnErrRtnOrderInsert:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnErrRtnOrderAction(self, pOrderAction, pRspInfo):
        """报单操作错误回报"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnErrRtnOrderAction: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnErrRtnOrderAction:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRtnInstrumentStatus(self, pInstrumentStatus):
        """合约交易状态通知"""
        # instrument_status = self.to_dict(pInstrumentStatus)
        # self.logger.info(
        #     "OnRtnInstrumentStatus: {}".format(instrument_status)
        # )

    def OnRtnTradingNotice(self, pTradingNoticeInfo):
        """交易通知"""
        trading_notice_info = self.to_dict(pTradingNoticeInfo)
        self.logger.info("TradingNoticeInfo:{}".format(trading_notice_info))

    def OnRtnErrorConditionalOrder(self, pErrorConditionalOrder):
        """提示条件单校验错误"""
        print(pErrorConditionalOrder)

    def OnRtnExecOrder(self, pExecOrder):
        """执行宣告通知"""
        print(pExecOrder)

    def OnErrRtnExecOrderInsert(self, pInputExecOrder, pRspInfo):
        """执行宣告录入错误回报"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnErrRtnExecOrderInsert: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnErrRtnExecOrderInsert:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnErrRtnExecOrderAction(self, pExecOrderAction, pRspInfo):
        """执行宣告操作错误回报"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnErrRtnExecOrderAction: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnErrRtnExecOrderAction:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnErrRtnForQuoteInsert(self, pInputForQuote, pRspInfo):
        """询价录入错误回报"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnErrRtnForQuoteInsert: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnErrRtnForQuoteInsert:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRtnQuote(self, pQuote):
        """报价通知"""
        print(pQuote)

    def OnErrRtnQuoteInsert(self, pInputQuote, pRspInfo):
        """报价录入错误回报"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnErrRtnQuoteInsert: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnErrRtnQuoteInsert:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnErrRtnQuoteAction(self, pQuoteAction, pRspInfo):
        """报价操作错误回报"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnErrRtnQuoteAction: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnErrRtnQuoteAction:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRtnForQuoteRsp(self, pForQuoteRsp):
        """询价通知"""
        print(pForQuoteRsp)

    def OnRtnCFMMCTradingAccountToken(self, pCFMMCTradingAccountToken):
        """保证金监控中心用户令牌"""
        print(pCFMMCTradingAccountToken)

    def OnRtnCombAction(self, pCombAction):
        """申请组合通知"""
        print(pCombAction)

    def OnErrRtnCombActionInsert(self, pInputCombAction, pRspInfo):
        """申请组合录入错误回报"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnErrRtnCombActionInsert: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnErrRtnCombActionInsert:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryContractBank(
        self,
        pContractBank,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询签约银行响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryContractBank: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryContractBank:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryParkedOrder(self, pParkedOrder, pRspInfo, nRequestID, bIsLast):
        """请求查询预埋单响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryParkedOrder: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryParkedOrder:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryParkedOrderAction(
        self,
        pParkedOrderAction,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询预埋撤单响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryParkedOrderAction: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryParkedOrderAction:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryTradingNotice(
        self,
        pTradingNotice,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询交易通知响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryTradingNotice: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryTradingNotice:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryBrokerTradingParams(
        self,
        pBrokerTradingParams,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询经纪公司交易参数响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryBrokerTradingParams: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryBrokerTradingParams:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQryBrokerTradingAlgos(
        self,
        pBrokerTradingAlgos,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询经纪公司交易算法响应"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQryBrokerTradingAlgos: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQryBrokerTradingAlgos:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRspQueryCFMMCTradingAccountToken(
        self,
        pQueryCFMMCTradingAccountToken,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询监控中心用户令牌"""
        if pRspInfo.ErrorID == 0:
            self.logger.info(
                "OnRspQueryCFMMCTradingAccountToken: Received"
                ", no operation is followed"
            )
        # 否则，推送错误信息
        else:
            self.logger.error(
                "OnRspQueryCFMMCTradingAccountToken:{}, ErrorMsg:{}"
                .format(
                    pRspInfo.ErrorID,
                    pRspInfo.ErrorMsg.decode('gbk')
                )
            )

    def OnRtnFromBankToFutureByBank(self, pRspTransfer):
        """银行发起银行资金转期货通知"""
        print(pRspTransfer)

    def OnRtnFromFutureToBankByBank(self, pRspTransfer):
        """银行发起期货资金转银行通知"""
        print(pRspTransfer)

    def OnRtnRepealFromBankToFutureByBank(self, pRspRepeal):
        """银行发起冲正银行转期货通知"""
        print(pRspRepeal)

    def OnRtnRepealFromFutureToBankByBank(self, pRspRepeal):
        """银行发起冲正期货转银行通知"""

    def OnRtnFromBankToFutureByFuture(self, pRspTransfer):
        """期货发起银行资金转期货通知"""

    def OnRtnFromFutureToBankByFuture(self, pRspTransfer):
        """期货发起期货资金转银行通知"""

    def OnRtnRepealFromBankToFutureByFutureManual(self, pRspRepeal):
        """系统运行时期货端手工发起冲正银行转期货请求，银行处理完毕后报盘发回的通知"""

    def OnRtnRepealFromFutureToBankByFutureManual(self, pRspRepeal):
        """系统运行时期货端手工发起冲正期货转银行请求，银行处理完毕后报盘发回的通知"""

    def OnRtnQueryBankBalanceByFuture(self, pNotifyQueryAccount):
        """期货发起查询银行余额通知"""

    def OnErrRtnBankToFutureByFuture(self, pReqTransfer, pRspInfo):
        """期货发起银行资金转期货错误回报"""

    def OnErrRtnFutureToBankByFuture(self, pReqTransfer, pRspInfo):
        """期货发起期货资金转银行错误回报"""

    def OnErrRtnRepealBankToFutureByFutureManual(self, pReqRepeal, pRspInfo):
        """系统运行时期货端手工发起冲正银行转期货错误回报"""

    def OnErrRtnRepealFutureToBankByFutureManual(self, pReqRepeal, pRspInfo):
        """系统运行时期货端手工发起冲正期货转银行错误回报"""

    def OnErrRtnQueryBankBalanceByFuture(self, pReqQueryAccount, pRspInfo):
        """期货发起查询银行余额错误回报"""

    def OnRtnRepealFromBankToFutureByFuture(self, pRspRepeal):
        """期货发起冲正银行转期货请求，银行处理完毕后报盘发回的通知"""

    def OnRtnRepealFromFutureToBankByFuture(self, pRspRepeal):
        """期货发起冲正期货转银行请求，银行处理完毕后报盘发回的通知"""

    def OnRspFromBankToFutureByFuture(
        self,
        pReqTransfer,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """期货发起银行资金转期货应答"""

    def OnRspFromFutureToBankByFuture(
        self,
        pReqTransfer,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """期货发起期货资金转银行应答"""

    def OnRspQueryBankAccountMoneyByFuture(
        self,
        pReqQueryAccount,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """期货发起查询银行余额应答"""

    def OnRtnOpenAccountByBank(self, pOpenAccount):
        """银行发起银期开户通知"""

    def OnRtnCancelAccountByBank(self, pCancelAccount):
        """银行发起银期销户通知"""

    def OnRtnChangeAccountByBank(self, pChangeAccount):
        """银行发起变更银行账号通知"""
