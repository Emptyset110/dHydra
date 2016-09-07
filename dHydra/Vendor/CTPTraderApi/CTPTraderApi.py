from ctp.futures import ApiStruct, TraderApi
from dHydra.core.Vendor import Vendor
import dHydra.core.util as util
import os


class CTPTraderApi(TraderApi, Vendor):

    def __init__(
        self,
        user_id=None,
        password=None,
        broker_id=None,
        investor_id=None,
        trade_front=None,
        **kwargs
    ):
        super().__init__(**kwargs)

        # Get Api Version
        self.api_version = self.GetApiVersion().decode("utf-8")
        self.logger.info("API Version:{}".format(self.api_version))
        self.trading_day = None

        self.req_id = 0              # 操作请求编号

        self.is_connected = False       # 连接状态
        self.is_login = False            # 登录状态

        cfg = util.read_config(os.getcwd() + "/ctp.json")
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
                .format(os.getcwd() + "/ctp.json")
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
            self.SubscribePrivateTopic(ApiStruct.TERT_RESTART)

            # 订阅私有流
            self.SubscribePrivateTopic(ApiStruct.TERT_RESTART)

            # 初始化连接，成功会调用OnFrontConnected
            self.Init()

            self.logger.info(
                "CTPTraderApi.connect: Initialization has completed."
            )

        # 若已经连接但尚未登录，则进行登录
        else:
            if not self.is_login:
                self.req_user_login()

    def req_user_login(self):
        """连接服务器"""
        # 如果填入了用户名密码等，则登录
        if self.user_id and self.password and self.broker_id:
            req = ApiStruct.ReqUserLogin(
                BrokerID=self.broker_id,
                UserID=self.user_id,
                Password=self.password
            )
            self.req_id += 1
            self.ReqUserLogin(req, self.req_id)

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """登录请求响应"""
        if pRspInfo.ErrorID == 0:
            self.front_id = pRspUserLogin.FrontID
            self.session_id = pRspUserLogin.SessionID
            self.is_login = True

            self.logger.info(
                "交易服务器登录完成:{}".format(pRspInfo.ErrorMsg.decode("gbk"))
            )

            # 确认结算信息
            self.req_id += 1
            req = ApiStruct.QrySettlementInfoConfirm(
                BrokerID=self.broker_id,
                InvestorID=self.investor_id,
            )
            self.ReqSettlementInfoConfirm(
                req,
                self.req_id
            )

        # 否则，推送错误信息
        else:
            self.logger.error(
                "error_id: {}, error_msg:{}"
                .format(
                    error.ErrorID,
                    error.ErrorMsg.decode('gbk')
                )
            )

    def req_qry_trading_account(self):
        """
        获取资金账户
        """
        req = ApiStruct.QryTradingAccount(
            BrokerID=self.broker_id,
            InvestorID=self.investor_id,
            CurrencyID=b"CNY"
        )
        self.req_id += 1
        self.ReqQryTradingAccount(req, self.req_id)
        self.logger.info(
            "CTPTraderApi.req_qry_trading_account: "
            "Finish sending request for trading account"
        )

    def OnFrontConnected(self):
        """当客户端与交易后台建立起通信连接时（还未登录前），该方法被调用。"""
        self.is_connected = True
        self.logger.info(
            "Successfully connected to the Trader Front, "
            "about to login."
            )
        self.login()

    def OnFrontDisconnected(self, nReason):
        """当客户端与交易后台通信连接断开时，该方法被调用。当发生这个情况后，API会自动重新连接，客户端可不做处理。
        @param nReason 错误原因
                0x1001 网络读失败
                0x1002 网络写失败
                0x2001 接收心跳超时
                0x2002 发送心跳失败
                0x2003 收到错误报文
        """
        self.is_connected = False
        self.is_login = False

        self.logger.warning(
            "交易服务器断开, {}"
            .format(
                nReason
            )
        )

    def OnHeartBeatWarning(self, nTimeLapse):
        """心跳超时警告。当长时间未收到报文时，该方法被调用。
        @param nTimeLapse 距离上次接收报文的时间
        """
        self.logger.warning(
            "心跳超时警告, 距离上次接收报文的时间:{}"
            .format(nTimeLapse)
        )

    def OnRspAuthenticate(
        self,
        pRspAuthenticate,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """客户端认证响应"""
        self.logger.info("OnRspAuthenticate: {}".format(pRspAuthenticate))


    def OnRspUserLogout(self, pUserLogout, pRspInfo, nRequestID, bIsLast):
        """登出回报"""
        # 如果登出成功，推送日志信息
        if pRspInfo.ErrorID == 0:
            self.is_login = False

            self.logger.info(u'交易服务器登出完成')

        # 否则，推送错误信息
        else:
            self.logger.error(
                "登出错误：ErrorID:{}, ErrorMsg:{}"
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

    def OnRspTradingAccountPasswordUpdate(
        self,
        pTradingAccountPasswordUpdate,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """资金账户口令更新请求响应"""

    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        """报单录入请求响应"""

    def OnRspParkedOrderInsert(
        self,
        pParkedOrder,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """预埋单录入请求响应"""

    def OnRspParkedOrderAction(
        self,
        pParkedOrderAction,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """预埋撤单录入请求响应"""

    def OnRspOrderAction(
        self,
        pInputOrderAction,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """报单操作请求响应"""

    def OnRspQueryMaxOrderVolume(
        self,
        pQueryMaxOrderVolume,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """查询最大报单数量响应"""

    def OnRspSettlementInfoConfirm(
        self,
        pSettlementInfoConfirm,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """投资者结算结果确认响应"""

    def OnRspRemoveParkedOrder(
        self,
        pRemoveParkedOrder,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """删除预埋单响应"""

    def OnRspRemoveParkedOrderAction(
        self,
        pRemoveParkedOrderAction,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """删除预埋撤单响应"""

    def OnRspExecOrderInsert(
        self,
        pInputExecOrder,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """执行宣告录入请求响应"""

    def OnRspExecOrderAction(
        self,
        pInputExecOrderAction,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """执行宣告操作请求响应"""

    def OnRspForQuoteInsert(
        self,
        pInputForQuote,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """询价录入请求响应"""

    def OnRspQuoteInsert(
        self,
        pInputQuote,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """报价录入请求响应"""

    def OnRspQuoteAction(
        self,
        pInputQuoteAction,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """报价操作请求响应"""

    def OnRspCombActionInsert(
        self,
        pInputCombAction,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """申请组合录入请求响应"""

    def OnRspQryOrder(
        self,
        pOrder,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询报单响应"""

    def OnRspQryTrade(
        self,
        pTrade,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询成交响应"""

    def OnRspQryInvestorPosition(
        self,
        pInvestorPosition,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询投资者持仓响应"""

    def OnRspQryTradingAccount(
        self,
        pTradingAccount,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询资金账户响应"""

    def OnRspQryInvestor(
        self,
        pInvestor,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询投资者响应"""

    def OnRspQryTradingCode(
        self,
        pTradingCode,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询交易编码响应"""

    def OnRspQryInstrumentMarginRate(
        self,
        pInstrumentMarginRate,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询合约保证金率响应"""

    def OnRspQryInstrumentCommissionRate(
        self,
        pInstrumentCommissionRate,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询合约手续费率响应"""

    def OnRspQryExchange(
        self,
        pExchange,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询交易所响应"""

    def OnRspQryProduct(self, pProduct, pRspInfo, nRequestID, bIsLast):
        """请求查询产品响应"""

    def OnRspQryInstrument(self, pInstrument, pRspInfo, nRequestID, bIsLast):
        """请求查询合约响应"""

    def OnRspQryDepthMarketData(
        self,
        pDepthMarketData,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询行情响应"""

    def OnRspQrySettlementInfo(
        self,
        pSettlementInfo,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询投资者结算结果响应"""

    def OnRspQryTransferBank(
        self,
        pTransferBank,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询转帐银行响应"""

    def OnRspQryInvestorPositionDetail(
        self,
        pInvestorPositionDetail,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询投资者持仓明细响应"""

    def OnRspQryNotice(self, pNotice, pRspInfo, nRequestID, bIsLast):
        """请求查询客户通知响应"""

    def OnRspQrySettlementInfoConfirm(
        self,
        pSettlementInfoConfirm,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询结算信息确认响应"""

    def OnRspQryInvestorPositionCombineDetail(
        self,
        pInvestorPositionCombineDetail,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询投资者持仓明细响应"""

    def OnRspQryCFMMCTradingAccountKey(
        self,
        pCFMMCTradingAccountKey,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """查询保证金监管系统经纪公司资金账户密钥响应"""

    def OnRspQryEWarrantOffset(
        self,
        pEWarrantOffset,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询仓单折抵信息响应"""

    def OnRspQryInvestorProductGroupMargin(
        self,
        pInvestorProductGroupMargin,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询投资者品种/跨品种保证金响应"""

    def OnRspQryExchangeMarginRate(
        self,
        pExchangeMarginRate,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询交易所保证金率响应"""

    def OnRspQryExchangeMarginRateAdjust(
        self,
        pExchangeMarginRateAdjust,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询交易所调整保证金率响应"""

    def OnRspQryExchangeRate(
        self,
        pExchangeRate,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询汇率响应"""

    def OnRspQrySecAgentACIDMap(
        self,
        pSecAgentACIDMap,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询二级代理操作员银期权限响应"""

    def OnRspQryProductExchRate(
        self,
        pProductExchRate,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询产品报价汇率"""

    def OnRspQryOptionInstrTradeCost(
        self,
        pOptionInstrTradeCost,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询期权交易成本响应"""

    def OnRspQryOptionInstrCommRate(
        self,
        pOptionInstrCommRate,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询期权合约手续费响应"""

    def OnRspQryExecOrder(self, pExecOrder, pRspInfo, nRequestID, bIsLast):
        """请求查询执行宣告响应"""

    def OnRspQryForQuote(self, pForQuote, pRspInfo, nRequestID, bIsLast):
        """请求查询询价响应"""

    def OnRspQryQuote(self, pQuote, pRspInfo, nRequestID, bIsLast):
        """请求查询报价响应"""

    def OnRspQryCombInstrumentGuard(
        self,
        pCombInstrumentGuard,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询组合合约安全系数响应"""

    def OnRspQryCombAction(self, pCombAction, pRspInfo, nRequestID, bIsLast):
        """请求查询申请组合响应"""

    def OnRspQryTransferSerial(
        self,
        pTransferSerial,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询转帐流水响应"""

    def OnRspQryAccountregister(
        self,
        pAccountregister,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询银期签约关系响应"""

    def OnRspError(self, pRspInfo, nRequestID, bIsLast):
        """错误应答"""

    def OnRtnOrder(self, pOrder):
        """报单通知"""

    def OnRtnTrade(self, pTrade):
        """成交通知"""

    def OnErrRtnOrderInsert(self, pInputOrder, pRspInfo):
        """报单录入错误回报"""

    def OnErrRtnOrderAction(self, pOrderAction, pRspInfo):
        """报单操作错误回报"""

    def OnRtnInstrumentStatus(self, pInstrumentStatus):
        """合约交易状态通知"""

    def OnRtnTradingNotice(self, pTradingNoticeInfo):
        """交易通知"""

    def OnRtnErrorConditionalOrder(self, pErrorConditionalOrder):
        """提示条件单校验错误"""

    def OnRtnExecOrder(self, pExecOrder):
        """执行宣告通知"""

    def OnErrRtnExecOrderInsert(self, pInputExecOrder, pRspInfo):
        """执行宣告录入错误回报"""

    def OnErrRtnExecOrderAction(self, pExecOrderAction, pRspInfo):
        """执行宣告操作错误回报"""

    def OnErrRtnForQuoteInsert(self, pInputForQuote, pRspInfo):
        """询价录入错误回报"""

    def OnRtnQuote(self, pQuote):
        """报价通知"""

    def OnErrRtnQuoteInsert(self, pInputQuote, pRspInfo):
        """报价录入错误回报"""

    def OnErrRtnQuoteAction(self, pQuoteAction, pRspInfo):
        """报价操作错误回报"""

    def OnRtnForQuoteRsp(self, pForQuoteRsp):
        """询价通知"""

    def OnRtnCFMMCTradingAccountToken(self, pCFMMCTradingAccountToken):
        """保证金监控中心用户令牌"""

    def OnRtnCombAction(self, pCombAction):
        """申请组合通知"""

    def OnErrRtnCombActionInsert(self, pInputCombAction, pRspInfo):
        """申请组合录入错误回报"""

    def OnRspQryContractBank(
        self,
        pContractBank,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询签约银行响应"""

    def OnRspQryParkedOrder(self, pParkedOrder, pRspInfo, nRequestID, bIsLast):
        """请求查询预埋单响应"""

    def OnRspQryParkedOrderAction(
        self,
        pParkedOrderAction,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询预埋撤单响应"""

    def OnRspQryTradingNotice(
        self,
        pTradingNotice,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询交易通知响应"""

    def OnRspQryBrokerTradingParams(
        self,
        pBrokerTradingParams,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询经纪公司交易参数响应"""

    def OnRspQryBrokerTradingAlgos(
        self,
        pBrokerTradingAlgos,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询经纪公司交易算法响应"""

    def OnRspQueryCFMMCTradingAccountToken(
        self,
        pQueryCFMMCTradingAccountToken,
        pRspInfo,
        nRequestID,
        bIsLast
    ):
        """请求查询监控中心用户令牌"""

    def OnRtnFromBankToFutureByBank(self, pRspTransfer):
        """银行发起银行资金转期货通知"""

    def OnRtnFromFutureToBankByBank(self, pRspTransfer):
        """银行发起期货资金转银行通知"""

    def OnRtnRepealFromBankToFutureByBank(self, pRspRepeal):
        """银行发起冲正银行转期货通知"""

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
