from ctp.futures import ApiStruct, TraderApi
# from datetime import datetime
# from dHydra.core.Vendor import Vendor
import dHydra.core.util as util
import os
from pandas import DataFrame
import inspect
import pickle
import time

from collections import defaultdict
from queue import Empty
from queue import Queue

import itertools
from abc import ABCMeta, abstractmethod

import threading
import copy
import logging
import pandas


def rsp_buffer(func):
    """
    OnRspQry的装饰器
    :return:
    """

    def _on_rsp(self, *args, **kwargs):
        # 先执行一下回调函数
        func(self, *args, **kwargs)

        # 获取被封装的函数参数
        named_args = inspect.getcallargs(func, self, *args, **kwargs)
        named_args.pop("self")
        name = None
        is_last = None
        request_id = None
        rsp_info = None
        data = None

        for k in named_args:
            if k == "bIsLast":
                is_last = named_args[k]
            elif k == "pRspInfo":
                rsp_info = named_args[k]
            elif k == "nRequestID":
                request_id = named_args[k]
            else:
                data = named_args[k]
                name = named_args[k].__class__.__name__

        msg = OnRspData(
            name=name,
            data=data,
            rsp_info=rsp_info,
            request_id=request_id,
            is_last=is_last
        )

        self.requests_map[request_id].put(pickle.loads(pickle.dumps(msg)))

    return _on_rsp


def get_logger(
    logger_name="CtpTraderApi",
    log_path="log",                     #
    console_log=True,                   # 屏幕打印日志开关，默认True
    console_log_level=logging.INFO,     # 屏幕打印日志的级别，默认为INFO
    critical_log=False,                 # critical单独写文件日志，默认关闭
    error_log=True,                     # error级别单独写文件日志，默认开启
    warning_log=False,                  # warning级别单独写日志，默认关闭
    info_log=True,                      # info级别单独写日志，默认开启
    debug_log=False,                    # debug级别日志，默认关闭
):
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    if log_path:
        # 补全文件夹
        if log_path[-1] != '/':
            log_path += '/'

    if not logger.handlers:
        # 屏幕日志打印设置
        if console_log:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(console_log_level)
            logger.addHandler(console_handler)

        if not os.path.exists(log_path + logger_name):
            os.makedirs(log_path + logger_name)
        # 打开下面的输出到文件
        if critical_log:
            log_handler = logging.FileHandler(
                log_path + logger_name + '/critical.log'
            )
            log_handler.setLevel(logging.CRITICAL)
            log_handler.setFormatter(formatter)
            logger.addHandler(log_handler)
        if error_log:
            log_handler = logging.FileHandler(
                log_path + logger_name + '/error.log'
            )
            log_handler.setLevel(logging.ERROR)
            log_handler.setFormatter(formatter)
            logger.addHandler(log_handler)
        if warning_log:
            log_handler = logging.FileHandler(
                log_path + logger_name + '/warning.log'
            )
            log_handler.setLevel(logging.WARNING)
            log_handler.setFormatter(formatter)
            logger.addHandler(log_handler)
        if info_log:
            log_handler = logging.FileHandler(
                log_path + logger_name + '/info.log'
            )
            log_handler.setLevel(logging.INFO)
            log_handler.setFormatter(formatter)
            logger.addHandler(log_handler)
        if debug_log:
            log_handler = logging.FileHandler(
                log_path + logger_name + '/debug.log'
            )
            log_handler.setLevel(logging.DEBUG)
            log_handler.setFormatter(formatter)
            logger.addHandler(log_handler)
    return logger


class Request(object):
    """
    请求的抽象类:
        request = SomeRequest(args)
                    .log(use="mongodb")
                    .send()
        result = req.result

    子类需要实现的方法：
        __init__: 子类在__init__中进行Request构建
        __send__: 子类发送请求的过程，会在.send()时候直接调用
        on_complete: 在收到全部回调以后会调用on_complete，
                     因（可能的）异步调用方式，所以必须实现
                     它的返回值会成为result的内容，
                     如果返回None,则对result无影响。
    子类可以实现的方法：
        check_args: 子类检查参数的方法
    """
    __metaclass__ = ABCMeta

    def __init__(self, trader, timeout=0.5):
        self.__trader__ = trader
        self.__request_id__ = trader.request_id     # id由迭代器生成
        self.__req_time__ = time.time()     # 记录请求创建时间
        self.__timeout__ = timeout  # 默认超时0.5秒
        self.__rsp__ = Queue()      # 此队列用以记录回调
        self.__result__ = Queue()   # 同步模式下用这个来取result
        self.__create__()           # 建立（trader.requests_map中关联）
        self.sent = False
        self.timeout = False        # Boolean标记这个request是否超时退出
        self.completed = False

    def put(self, msg):
        self.__rsp__.put(msg)

    def get(self, timeout):
        return self.__rsp__.get(timeout=timeout)

    def check_args(self):
        """
        :return: boolean
        """
        return True

    def __wait_result__(self, timeout=0.5):
        result = list()
        while True:
            try:
                msg = self.__rsp__.get(timeout=timeout)
                result.append(msg.data.to_dict(decode=True))
                if msg.is_last:
                    dealt_result = self.on_complete(result=result)
                    if dealt_result is not None:
                        self.__result__.put(dealt_result)
                    else:
                        self.__result__.put(result)
                    self.completed = True
                    return True
            except Empty:
                self.on_timeout()
                return False

    def __create__(self):
        check_args = self.check_args()
        if check_args:
            self.__trader__.requests_map[self.__request_id__] = self
        elif isinstance(check_args, ValueError):
            raise check_args
        else:
            raise ValueError("check_args方法没有正确返回")

    @abstractmethod
    def __send__(self):
        """
        这是由子类实现的send过程
        """

    def send(self):
        """
        开始Request请求
        :return:
        """
        self.__send__()
        self.sent = True

        # 统一异步模式
        t = threading.Thread(
            target=self.__wait_result__,
            args=(self.__timeout__,),
            daemon=True
        )
        t.start()

        # 10秒后清除自己
        t0 = threading.Thread(
            target=self.auto_release,
            daemon=True
        )
        t0.start()

        return True

    def auto_release(self):
        time.sleep(10)
        self.delete_self()

    @abstractmethod
    def on_complete(self, result):
        """
        如果是异步实现，
        则一定要在这里调用get_result
        并且在此处处理result
        如果不想改变result数据结构，务必返回None
        :return:
        """
        pass

    def on_timeout(self):
        self.__trader__.logger.warning(
            "Request:{} 超时".format(self.__request_id__)
        )
        self.timeout = True
        self.delete_self()

    def log(self):
        """
        用于将Request持久化记录
        :return:
        """
        return self

    def delete_self(self):
        self.__trader__.delete_request(self.__request_id__)

    def get_result(self, timeout=None):
        """
        这里另外设置一个timeout是考虑到
        通用请求队列（非报单队列）因为强行设置了1秒的延迟可能会发生阻塞
        :param timeout:
        :return:
        """
        try:
            if timeout:
                return self.__result__.get(timeout=timeout)
            else:
                return self.__result__.get(timeout=self.__timeout__)
        except Empty:
            raise TimeoutError

    def __del__(self):
        self.__trader__.logger.debug(
            "Request Deleted, request_id:", self.__request_id__
        )


class RequestOrder(Request):
    """
    查询成交
    """
    def __init__(self, trader):
        super().__init__(trader=trader)

    def on_complete(self, result):
        pass

    def __send__(self):
        pQryOrder = ApiStruct.QryOrder()
        self.__trader__.ReqQryOrder(
            pQryOrder=pQryOrder,
            nRequestID=self.__request_id__
        )


class RequestInputOrder(Request):
    """
    下单请求
        direction: buy, sell
        flag: open, close, close_today
    """
    def __init__(
            self,
            trader,
            instrument_id,
            volume,
            price,
            direction,
            offset_flag
    ):
        self.instrument_id = instrument_id
        self.volume = volume
        self.price = price
        self.direction = direction
        self.offset_flag = offset_flag
        super().__init__(trader=trader)

    def check_args(self):
        # 检查instrument_id参数
        if isinstance(self.instrument_id, str):
            self.instrument_id = self.instrument_id.encode()

        # 检查direction参数
        if self.direction in self.__trader__.direction_map:
            self.direction = self.__trader__.direction_map[self.direction]
        elif self.direction not in self.__trader__.direction_map.values():
            return ValueError("direction Error: {}".format(self.direction))

        # 检查offset_flag参数
        if self.offset_flag in self.__trader__.offset_flag_map:
            self.offset_flag = self.__trader__.offset_flag_map[self.offset_flag]
        elif self.offset_flag not in self.__trader__.offset_flag_map:
            return ValueError("offset_flag Error: {}".format(self.offset_flag))
        return True

    def on_complete(self, result):
        pass

    def __send__(self):
        pInputOrder = ApiStruct.InputOrder(
            BrokerID=self.__trader__.broker_id,
            InvestorID=self.__trader__.investor_id,
            InstrumentID=self.instrument_id,
            OrderRef=str(self.__trader__.order_ref).encode(),
            UserID=self.__trader__.user_id,
            OrderPriceType=ApiStruct.OPT_LimitPrice,  # 默认限价单
            Direction=self.direction,  # 多空标志
            CombOffsetFlag=self.offset_flag,  # 开平标志
            #   OF_Open='0'  # 开仓
            #   OF_Close = '1'  # 平仓
            #   OF_ForceClose = '2'  # 强平
            #   OF_CloseToday = '3'  # 平今
            #   OF_CloseYesterday = '4'  # 平昨
            #   OF_ForceOff = '5'  # 强减
            #   OF_LocalForceClose = '6'  # 本地强平
            CombHedgeFlag=ApiStruct.HF_Speculation,  # 投机单
            LimitPrice=self.price,
            VolumeTotalOriginal=self.volume,
            TimeCondition=ApiStruct.TC_GFD,  # 当日有效
            # GTDDate=gtd_date,
            RequestID=self.__request_id__,
            # ctp测试服务器下：
            #     TC_IOC 立即完成否则撤销（未知，始终撤销）
            #     TC_GFS 本节有效（不被支持的报单类型）
            #     TC_GFD 当日有效（可用）
            #     TC_GTC 撤销前有效
            #     TC_GFA 集合竞价有效
            VolumeCondition=ApiStruct.VC_AV,
            MinVolume=1,
            ContingentCondition=ApiStruct.CC_Immediately,
            StopPrice=0.0,
            # ForceCloseReason=force_close_reason,
            IsAutoSuspend=0,
            # BusinessUnit=business_unit,
            UserForceClose=0,  # 用户强平标志
            # IsSwapOrder=is_swap_order,
        )
        self.__trader__.ReqOrderInsert(
            pInputOrder=pInputOrder,
            nRequestID=self.__request_id__
        )


class RequestMaxOrderVolume(Request):
    """
    最大
    """
    def __init__(self, trader, instrument_id, direction, offset_flag):
        self.instrument_id = instrument_id
        self.direction = direction
        self.offset_flag = offset_flag
        super().__init__(trader=trader)

    def check_args(self):
        if isinstance(self.instrument_id, str):
            self.instrument_id = self.instrument_id.encode()
        return True

    def __send__(self):
        pQueryMaxOrderVolume = ApiStruct.QueryMaxOrderVolume(
            BrokerID=self.__trader__.broker_id,
            InvestorID=self.__trader__.investor_id,
            InstrumentID=self.instrument_id,
            Direction=self.direction,
            OffsetFlag=self.offset_flag,
        )
        self.__trader__.ReqQueryMaxOrderVolume(
            pQueryMaxOrderVolume=pQueryMaxOrderVolume,
            nRequestID=self.__request_id__
        )

    def on_complete(self, result):
        pass


class RequestPosition(Request):
    """
    获取Position
    并且将结果更新给trader.position
    """
    def __init__(self, trader):
        super().__init__(trader=trader)
        self.data = ApiStruct.QryInvestorPosition(
            BrokerID=self.__trader__.broker_id,
            InvestorID=self.__trader__.investor_id
        )

    def __send__(self):
        self.__trader__.logger.info(
            "获取持仓request_id:{}".format(self.__request_id__)
        )
        self.__trader__.ReqQryInvestorPosition(
            pQryInvestorPosition=self.data,
            nRequestID=self.__request_id__
        )

    def on_complete(self, result):
        df = DataFrame(result).drop(
            ["SettlementPrice","PreSettlementPrice"],
            axis=1
        ).groupby(
            ["InstrumentID","PosiDirection"]
        ).sum()

        self.__trader__.position = df
        return df


class RequestTradingAccount(Request):
    """

    """
    def __init__(self, trader, currency_id=b"CNY"):
        super().__init__(trader=trader)
        self.currency_id = currency_id

    def __send__(self):
        self.__trader__.logger.info(
            "获取资金, request_id:{}".format(self.__request_id__)
        )
        pQryTradingAccount = ApiStruct.QryTradingAccount(
            BrokerID=self.__trader__.broker_id,
            InvestorID=self.__trader__.investor_id,
            CurrencyID=self.currency_id
        )

        self.__trader__.ReqQryTradingAccount(
            pQryTradingAccount=pQryTradingAccount,
            nRequestID=self.__request_id__
        )

    def on_complete(self, result):
        self.__trader__.logger.info(
            "获取资金完毕, request_id:{}".format(self.__request_id__)
        )
        if len(result) == 1:
            self.__trader__.account = result[0]

class RequestInstrument(Request):
    """
    获取合约信息
    """
    def __init__(self, trader):
        super().__init__(trader=trader)

    def __send__(self):
        print("RequestInstrument:", self.__request_id__)
        self.__trader__.ReqQryInstrument(
            pQryInstrument=ApiStruct.QryInstrument(),
            nRequestID=self.__request_id__
        )

    def on_complete(self, result):
        self.__trader__.instruments =\
            DataFrame(result)\
            .drop_duplicates("InstrumentID")
        print(
            "成功获取Instruments:{}个"
            .format(
                len(list(self.__trader__.instruments.InstrumentID))
            )
        )


class OnRspData(object):
    def __init__(
            self,
            name=None,
            data=None,
            rsp_info=None,
            request_id=None,
            is_last=True
    ):
        self.name = name    # 对应的是ApiStruct中的类名
        self.data = data    # 对应的是ApiStruct中的数据结构
        self.request_id = request_id    # nRequestID
        self.rsp_info = rsp_info        # pRspInfo
        self.is_last = is_last


class CtpTraderApi(TraderApi):
    """
    这里是CtpTraderApi主体
    """
    def __init__(
            self,
            account="ctp.json"
    ):
        self.logger = get_logger(
            log_path="log",                     #
            console_log=True,              # 屏幕打印日志开关，默认True
            console_log_level=logging.INFO,  # 屏幕打印日志的级别，默认为INFO
            critical_log=False,        # critical单独写文件日志，默认关闭
            error_log=True,             # error级别单独写文件日志，默认开启
            warning_log=False,         # warning级别单独写日志，默认关闭
            info_log=True,               # info级别单独写日志，默认开启
            debug_log=False,
            logger_name=self.__class__.__name__,
        )
        super().__init__()
        self.shfe_time = None
        self.dce_time = None
        self.czce_time = None
        self.ffex_time = None
        self.ine_time = None
        self.login_time = None

        # 将语义化的"buy","sell"映射到ApiStruct.D_Buy, ApiStruct.D_Sell
        self.direction_map = {
            "buy": ApiStruct.D_Buy,
            "sell": ApiStruct.D_Sell,
        }
        self.direction_inverse_map = {
            ApiStruct.D_Buy: "buy",
            ApiStruct.D_Sell: "sell",
        }
        self.posi_direction_map = {
            "long": ApiStruct.PD_Long,
            "short": ApiStruct.PD_Short
        }
        # 将语义化的"open","close"映射到ApiStruct.OF_Open, ApiStruct.OF_Close
        self.offset_flag_map = {
            "open": ApiStruct.OF_Open,
            "close": ApiStruct.OF_Close,
            "force_close": ApiStruct.OF_ForceClose,  # 强平
            "close_today": ApiStruct.OF_CloseToday,  # 平今
            "close_yesterday": ApiStruct.OF_CloseYesterday,  # 平昨
            "force_off": ApiStruct.OF_ForceOff,  # 强减
        }
        self.offset_flag_inverse_map = {
            ApiStruct.OF_Open: "open",
            ApiStruct.OF_Close: "close",
            ApiStruct.OF_CloseToday: "close_today",
            ApiStruct.OF_CloseYesterday: "close_yesterday",
        }

        # Get Api Version
        self.api_version = self.GetApiVersion().decode("utf-8")
        self.trading_day = None

        # CtpTraderApi自己维护的几个属性
        self.user_login = None  # 用户登录应答的缓存
        self.trading_account = None  # 资金账户
        self.trading_account_last_updated = None  # 资金账户上次更新时间
        # position
        self.position = None    # DataFrame类型

        self.instruments = DataFrame(
            columns=[
                'CombinationType', 'CreateDate', 'DeliveryMonth',
                'DeliveryYear', 'EndDelivDate', 'ExchangeID',
                'ExchangeInstID', 'ExpireDate', 'InstLifePhase',
                'InstrumentName', 'IsTrading', 'LongMarginRatio',
                'MaxLimitOrderVolume', 'MaxMarginSideAlgorithm',
                'MaxMarketOrderVolume', 'MinLimitOrderVolume',
                'MinMarketOrderVolume', 'OpenDate', 'OptionsType',
                'PositionDateType', 'PositionType', 'PriceTick',
                'ProductClass', 'ProductID', 'ShortMarginRatio',
                'StartDelivDate', 'StrikePrice', 'UnderlyingInstrID',
                'UnderlyingMultiple', 'VolumeMultiple', "InstrumentID"
            ]
        )
        self.instruments_last_updated = None
        self.instrument_status = dict()

        self.position_last_updated = None  # 持仓最近更新时间：datetime类型
        self.position_updating = False   # 用于标记position是否正在更新
        self.position_timeout = False    # 当获取持仓超时的时候标记，当获取完毕一次持仓以后取消标记
        self.position_buffer = list()  # list内嵌dict
        self.position_latest_request_id = None  # 最新的对position的request_id
        self.position_buffer_request_id = None  # 正在buffer中的request_id
        # 委托明细
        self.orders = None      # DataFrame类型
        # 成交明细
        self.trade = None       # 成交明细，DataFrame类型

        self.__request_counter__ = itertools.count()  # self.request_ref的迭代器
        self.__request_counter__.__next__()
        self.__order_counter__ = itertools.count()  # self.order_ref的迭代器
        self.__order_counter__.__next__()

        self.requests_map = defaultdict(Queue)
        self.requests_safe_queue = Queue()

        self.is_connected = False       # 连接状态
        self.is_login = False            # 登录状态

        account_path = ""
        if isinstance(account, dict):
            cfg = account
        else:
            if account[0] != '/':
                account = '/' + account
            account_path = os.getcwd() + "{}".format(account)
            cfg = util.read_config(account_path)
        try:
            self.investor_id = cfg["investor_id"].encode()
            self.user_id = cfg["user_id"].encode()                # 账号
            self.password = cfg["password"].encode()            # 密码
            self.broker_id = cfg["broker_id"].encode()            # 经纪商代码
            self.trade_front = cfg["trade_front"].encode()  # 服务器地址
        except KeyError as e:
            self.logger.error(
                "没有从{}读取到正确格式的配置, Error: {}"
                .format(account_path, e)
            )
            raise KeyError

        self.front_id = None            # 前置机编号
        self.session_id = None          # 会话编号

        self.connect(
            self.user_id,
            self.password,
            self.broker_id,
            self.trade_front
        )

        request_sender = threading.Thread(
            target=self.request_sender, daemon=True
        )
        request_sender.start()

    # ==========================================================
    # Request相关，通用部分
    # ==========================================================
    def request_sender(self):
        while True:
            try:
                req = self.requests_safe_queue.get(timeout=None)
                req.send()
                time.sleep(1)
            except Empty as e:
                pass

    @property
    def request_id(self):
        return self.__request_counter__.__next__()

    @property
    def order_ref(self):
        return self.__order_counter__.__next__()

    def delete_request(self, request_id):
        if request_id in self.requests_map:
            del self.requests_map[request_id]

    # ==========================================================
    # 登录相关
    # ==========================================================
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
            self.SubscribePublicTopic(ApiStruct.TERT_RESUME)

            # 订阅私有流
            self.SubscribePrivateTopic(ApiStruct.TERT_RESUME)

            # 初始化连接，成功会调用OnFrontConnected
            self.Init()

            self.logger.info(
                "CTP Initialization has completed."
            )

        # 若已经连接但尚未登录，则进行登录
        else:
            if not self.is_login:
                self.req_user_login()

    def OnFrontConnected(self):
        """
        当客户端与交易后台建立起通信连接时（还未登录前），该方法被调用。
        """
        self.is_connected = True
        self.logger.info(
            "Successfully connected to the Trader Front, "
            "about to login."
        )

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

            self.ReqUserLogin(
                pReqUserLogin=pReqUserLogin,
                nRequestID=self.request_id
            )

    def get_settlement(self):
        req = ApiStruct.QrySettlementInfoConfirm(
            BrokerID=self.broker_id,
            InvestorID=self.investor_id,
        )
        self.ReqSettlementInfoConfirm(
            req,
            self.request_id
        )

    def OnRspUserLogin(self, pRspUserLogin, pRspInfo, nRequestID, bIsLast):
        """登录请求响应"""
        # rsp_user_login = pRspUserLogin.to_dict(decode=True)
        # rsp_info = pRspInfo.to_dict()

        if pRspInfo.ErrorID == 0:
            self.front_id = pRspUserLogin.FrontID
            self.session_id = pRspUserLogin.SessionID
            self.is_login = True

            self.logger.info(
                "CTP Login Successfully:{}"
                .format(pRspInfo.ErrorMsg.decode("gbk"))
            )

            self.shfe_time = pRspUserLogin.SHFETime
            self.dce_time = pRspUserLogin.DCETime
            self.czce_time = pRspUserLogin.CZCETime
            self.ffex_time = pRspUserLogin.FFEXTime
            self.ine_time = pRspUserLogin.INETime
            self.login_time = pRspUserLogin.LoginTime

            req = ApiStruct.QrySettlementInfoConfirm(
                BrokerID=self.broker_id,
                InvestorID=self.investor_id,
            )
            self.ReqSettlementInfoConfirm(
                req,
                self.request_id
            )
            time.sleep(0.5)
            self.prepare_instruments_info()
            self.update_position(async=True, timeout=0.5)
            self.update_trading_account(async=True, timeout=0.5)

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
            time.sleep(3)
            self.connect(
                self.user_id,
                self.password,
                self.broker_id,
                self.trade_front
            )

    # ==========================================================
    # 登录时预备数据
    # ==========================================================
    def max_order_volume(
            self,
            instrument_id,
            direction=ApiStruct.D_Buy,
            offset_flag=ApiStruct.OF_Open
    ):
        """
        查询最大报单数量
        :return:
        """
        request = RequestMaxOrderVolume(
            trader=self,
            instrument_id=instrument_id,
            direction=direction,
            offset_flag=offset_flag
        )

    @rsp_buffer
    def OnRspQueryMaxOrderVolume(
            self,
            pQueryMaxOrderVolume,
            pRspInfo,
            nRequestID,
            bIsLast
    ):
        """查询最大报单数量响应"""

    def prepare_instruments_info(self, async=True, timeout=1.0):
        """
        获取当前全部instruments
            self.instruments设置为一个DataFrame
        :return: boolean
        """
        if self.instruments_last_updated is None:
            self.instruments_last_updated = time.time()
        else:
            if time.time()-self.instruments_last_updated < 30:
                self.logger.debug("与上次请求时间距离太短")
                return False
        self.logger.info("获取Instrument")
        request = RequestInstrument(trader=self)
        self.requests_safe_queue.put(request)

        if not async:
            result = request.get_result()
            self.instruments_last_updated = time.time()
            return result
        else:
            self.instruments_last_updated = time.time()


    @rsp_buffer
    def OnRspQryInstrument(self, pInstrument, pRspInfo, nRequestID, bIsLast):
        """请求查询合约响应"""

    # ==========================================================
    # 与 持仓 有关的部分
    # ==========================================================
    def exchange_id(self, instrument_id):
        df = self.instruments
        result = df[df.InstrumentID == instrument_id]
        if len(result) > 0:
            return list(result.ExchangeID)[0]

    def judge_position(self, instrument_id, direction):
        """
        根据缓存持仓来判断持今，持昨
        :param instrument_id:
        :return:
        {
            "position": "当前总持仓"
            "today": "今仓"
            "yesterday": "昨仓"
            "exchange_id" : "交易所"
        }
        """
        try:
            if direction in self.posi_direction_map:
                direction = self.posi_direction_map[direction].decode()
            result = self.position[["Position","TodayPosition","YdPosition"]].ix[(instrument_id, direction)]
            return result
        except KeyError:
            return pandas.Series([])

    def update_position(self, async=True, timeout=0.5):
        """
        让trader更新持仓，可同步/异步
        :param async:
        :param timeout:
        :return:
        """
        request = RequestPosition(trader=self)
        if async:
            self.requests_safe_queue.put(request)
        else:
            self.requests_safe_queue.put(request)
            return request.get_result()

    # ==========================================================
    # 与 资金 有关的部分
    # ==========================================================
    def update_trading_account(
            self,
            currency_id=b"CNY",
            async=True,
            timeout=1.5
    ):
        """
        获取资金账户
        """
        request = RequestTradingAccount(trader=self, currency_id=currency_id)
        self.requests_safe_queue.put(request)
        if not async:
            return request.get_result(timeout=timeout)

    @rsp_buffer
    def OnRspQryTradingAccount(
            self,
            pTradingAccount,
            pRspInfo,
            nRequestID,
            bIsLast
    ):
        """请求查询资金账户响应"""

    # ==========================================================
    # 查询委托单相关部分
    # ==========================================================
    def get_order(self):
        """
        请求查询委托单
        :return:
        """
        request = RequestOrder(trader=self)
        request.send()
        if not request.timeout and request.completed:
            return request.get_result()

    # ==========================================================
    # 下单相关的部分
    # ==========================================================
    def order_insert(
            self,
            instrument_id,
            price, volume,
            direction,
            offset_flag,
            async=False,
            timeout=0.2
    ):
        request = RequestInputOrder(
            trader=self,
            instrument_id=instrument_id,
            volume=volume,
            price=price,
            direction=direction,
            offset_flag=offset_flag
        )
        request.send()
        if request.completed and not request.timeout:
            return request.get_result()

    def req_order_insert(
            self,
            instrument_id=b'',
            price=0.0,
            volume=0,
            direction=ApiStruct.D_Buy,
            offset_flag=ApiStruct.OF_Open,
    ):
        """
        CTP的下单种类
            普通限价单:
            order_price_type=ApiStruct.OPT_LimitPrice
        """
        request_id = self.request_id

        if isinstance(instrument_id, str):
            instrument_id = instrument_id.encode()
        pInputOrder = ApiStruct.InputOrder(
            InstrumentID=instrument_id,
            LimitPrice=price,
            VolumeTotalOriginal=volume,
            Direction=direction,  # 多空标志
            CombOffsetFlag=offset_flag,  # 开平标志
            # OF_Open='0'  # 开仓
            # OF_Close = '1'  # 平仓
            # OF_ForceClose = '2'  # 强平
            # OF_CloseToday = '3'  # 平今
            # OF_CloseYesterday = '4'  # 平昨
            # OF_ForceOff = '5'  # 强减
            # OF_LocalForceClose = '6'  # 本地强平
            RequestID=request_id,
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
            nRequestID=request_id
        )

    @rsp_buffer
    def OnRspOrderInsert(self, pInputOrder, pRspInfo, nRequestID, bIsLast):
        """报单录入请求响应"""
        print(pInputOrder)

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

    def smart_cover(self, instrument_id, volume, price):
        # 检查空头持仓
        if self.exchange_id(instrument_id) == 'SHFE':
            check = self.judge_position(
                instrument_id=instrument_id,
                direction="short"
            )
            if len(check)>0:
                if (check.Position-check.TodayPosition) >= volume:
                    self.cover(instrument_id, volume, price, "close_yesterday")
                elif check.Position >= volume:
                    # 优先平昨
                    if int(check.Position-check.TodayPosition) > 0:
                        self.cover(
                            instrument_id=instrument_id,
                            volume=int(check.Position-check.TodayPosition),
                            price=price,
                            flag="close_yesterday"
                        )
                    self.cover(
                        instrument_id=instrument_id,
                        volume=int(volume-check.Position+check.TodayPosition),
                        price=price,
                        flag="close_today"
                    )
                else:
                    self.cover(instrument_id, volume, price)
            else:
                self.cover(instrument_id, volume, price)
        else:
            self.cover(instrument_id, volume, price)

    def cover(self, instrument_id, volume, price, flag="close"):
        """
        买平=平空=cover
        """
        offset_flag = self.offset_flag_map[flag]
        if isinstance(instrument_id, str):
            instrument_id = instrument_id.encode()
        self.req_order_insert(
            instrument_id=instrument_id,
            price=price,
            volume=volume,
            direction=ApiStruct.D_Buy,
            offset_flag=offset_flag
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

    def smart_sell(self, instrument_id, volume, price):
        # 检查多头持仓
        if self.exchange_id(instrument_id) == 'SHFE':
            check = self.judge_position(
                instrument_id=instrument_id,
                direction="long"
            )
            if len(check)>0:
                if (check.Position-check.TodayPosition) >= volume:
                    self.sell(instrument_id, volume, price, "close_yesterday")
                elif check.Position >= volume:
                    # 优先平昨
                    if int(check.Position-check.TodayPosition) > 0:
                        self.sell(
                            instrument_id=instrument_id,
                            volume=int(check.Position-check.TodayPosition),
                            price=price,
                            flag="close_yesterday"
                        )
                    self.sell(
                        instrument_id=instrument_id,
                        volume=int(volume-check.Position+check.TodayPosition),
                        price=price,
                        flag="close_today"
                    )
                else:
                    self.sell(instrument_id, volume, price)
            else:
                self.sell(instrument_id, volume, price)
        else:
            self.sell(instrument_id, volume, price)

    def sell(self, instrument_id, volume, price, flag="close"):
        """
        卖平=平多=sell
        """
        offset_flag = self.offset_flag_map[flag]
        if isinstance(instrument_id, str):
            instrument_id = instrument_id.encode()
        self.req_order_insert(
            instrument_id=instrument_id,
            price=price,
            volume=volume,
            direction=ApiStruct.D_Sell,
            offset_flag=offset_flag
        )

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
        self.is_login = False
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

    def OnHeartBeatWarning(self, nTimeLapse):
        """心跳超时警告。当长时间未收到报文时，该方法被调用。
        @param nTimeLapse 距离上次接收报文的时间
        """
        self.logger.warning(
            "心跳超时警告, 距离上次接收报文的时间:{}"
            .format(nTimeLapse)
        )

    @rsp_buffer
    def OnRspAuthenticate(
            self,
            pRspAuthenticate,
            pRspInfo,
            nRequestID,
            bIsLast
    ):
        """客户端认证响应"""

    def req_user_logout(self):
        pUserLogout = ApiStruct.UserLogout(
            BrokerID=self.broker_id,
            UserID=self.user_id
        )
        request_id = self.request_id
        self.ReqUserLogout(pUserLogout, request_id)
        self.logger.info(
            "req_user_logout: Request Sent"
            "with request_id:{}".format(request_id)
        )

    @rsp_buffer
    def OnRspUserLogout(self, pUserLogout, pRspInfo, nRequestID, bIsLast):
        """登出回报"""
        # 如果登出成功，推送日志信息
        if pRspInfo.ErrorID == 0:
            self.is_login = False
            self.logger.info('OnRspUserLogout: Success')
            user_logout = pUserLogout.to_dict()
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

    @rsp_buffer
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

    def req_qry_investor_position_detail(self):
        """请求查询投资者持仓明细"""
        pQryInvestorPositionDetail = ApiStruct.QryInvestorPositionDetail(
            BrokerID=self.broker_id,
            InvestorID=self.investor_id
        )
        request_id = self.request_id
        self.ReqQryInvestorPositionDetail(
            pQryInvestorPositionDetail=pQryInvestorPositionDetail,
            nRequestID=request_id
        )

    @rsp_buffer
    def OnRspQryInvestorPositionDetail(
            self,
            pInvestorPositionDetail,
            pRspInfo,
            nRequestID,
            bIsLast
    ):
        """请求查询投资者持仓明细响应"""
        # investor_position_detail = pInvestorPositionDetail.to_dict()
        # self.logger.info(
        #     "InvestorPositionDetail: {}".format(investor_position_detail)
        # )

    def req_qry_investor_position_combine_detail(self):
        pQryInvestorPositionCombineDetail = \
            ApiStruct.QryInvestorPositionCombineDetail(
                BrokerID=self.broker_id,
                InvestorID=self.investor_id
            )
        request_id = self.request_id
        self.ReqQryInvestorPositionCombineDetail(
            pQryInvestorPositionCombineDetail,
            request_id
        )

    # @onrsp
    def OnRspQryInvestorPositionCombineDetail(
            self,
            pInvestorPositionCombineDetail,
            pRspInfo,
            nRequestID,
            bIsLast
    ):
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

    # @onrsp
    def OnRspParkedOrderInsert(
            self,
            pParkedOrder,
            pRspInfo,
            nRequestID,
            bIsLast
    ):
        """预埋单录入请求响应"""
        if pRspInfo.ErrorID == 0:
            parked_order = pParkedOrder.to_dict()
            self.logger.info(
                "OnRspParkedOrderInsert: Received"
                ", no operation is followed"
                "ParkedOrder:{}".format(parked_order)
            )

    # @onrsp
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

    # @onrsp
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

        request = RequestMaxOrderVolume(
            trader=self,
            instrument_id=instrument_id,
            direction=direction,
            offset_flag=offset_flag
        )
        request.send()

        if request.completed:
            return request.get_result()
            # pQueryMaxOrderVolume = ApiStruct.QueryMaxOrderVolume(
            #     BrokerID=self.broker_id,
            #     InvestorID=self.investor_id,
            #     InstrumentID=instrument_id,
            #     Direction=direction,
            #     OffsetFlag=offset_flag,
            # )
            #
            # self.ReqQueryMaxOrderVolume(
            #     pQueryMaxOrderVolume=pQueryMaxOrderVolume,
            #     nRequestID=request_id
            # )

    # @onrsp
    def OnRspSettlementInfoConfirm(
            self,
            pSettlementInfoConfirm,
            pRspInfo,
            nRequestID,
            bIsLast
    ):
        """投资者结算结果确认响应"""
        print("OnRspSettlementInfoConfirm")

    # @onrsp
    def OnRspRemoveParkedOrder(
            self,
            pRemoveParkedOrder,
            pRspInfo,
            nRequestID,
            bIsLast
    ):
        """删除预埋单响应"""

    # @onrsp
    def OnRspRemoveParkedOrderAction(
            self,
            pRemoveParkedOrderAction,
            pRspInfo,
            nRequestID,
            bIsLast
    ):
        """删除预埋撤单响应"""

    # @onrsp
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

    # def req_qry_order(self):
    #     """
    #     查询委托
    #     :return:
    #     """
    #     pQryOrder = ApiStruct.QryOrder(
    #         BrokerID=self.broker_id,
    #         InvestorID=self.investor_id
    #     )
    #     request_id = self.request_id
    #     self.ReqQryOrder(pQryOrder=pQryOrder, nRequestID=request_id)
    #     self.__wait_result__(request_id=request_id,timeout=0.5)

    @rsp_buffer
    def OnRspQryOrder(
            self,
            pOrder,
            pRspInfo,
            nRequestID,
            bIsLast
    ):
        """请求查询报单响应"""

    @rsp_buffer
    def OnRspQryTrade(
            self,
            pTrade,
            pRspInfo,
            nRequestID,
            bIsLast
    ):
        """请求查询成交响应"""
        # if pRspInfo.ErrorID == 0:
        #     self.logger.info(
        #         "OnRspQryTrade: Received"
        #         ", no operation is followed"
        #     )
        # # 否则，推送错误信息
        # else:
        #     self.logger.error(
        #         "OnRspQryTrade:{}, ErrorMsg:{}"
        #             .format(
        #             pRspInfo.ErrorID,
        #             pRspInfo.ErrorMsg.decode('gbk')
        #         )
        #     )

    def req_qry_investor_position(self):
        """
        查询持仓
        """
        pQryInvestorPosition = ApiStruct.QryInvestorPosition(
            BrokerID=self.broker_id,
            InvestorID=self.investor_id
        )
        request_id = self.request_id
        self.position_buffer_request_id = request_id
        self.position_buffer = list()
        self.ReqQryInvestorPosition(
            pQryInvestorPosition=pQryInvestorPosition,
            nRequestID=request_id
        )
        # 设置正在更新的标记为True， 更新完成后会设置为False
        self.position_updating = True

    @rsp_buffer
    def OnRspQryInvestorPosition(
            self,
            pInvestorPosition,
            pRspInfo,
            nRequestID,
            bIsLast
    ):
        """请求查询投资者持仓响应"""

    @rsp_buffer
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
        order = pOrder.to_dict(decode=True)
        self.logger.info(
            "OnRtnOrder: Received"
            ", no operation is followed\n"
            "order:{}"
            .format(order)
        )

    def OnRtnTrade(self, pTrade):
        """成交通知"""
        trade = pTrade.to_dict(decode=True)

        self.logger.info(
            "OnRtnTrade: {}, Volume: {}, Direction: {} "
            "OffsetFlag: {}, Price: {}, Time: {}, OrderRef: {}"
            "OrderSysID: {}"
            .format(
                trade["InstrumentID"],
                trade["Volume"],
                trade["Direction"],
                trade["OffsetFlag"],
                trade["Price"],
                trade["TradeTime"],
                trade["OrderRef"],
                trade["OrderSysID"]
            )
        )

        self.update_position(async=True, timeout=0.5)
        self.update_trading_account(async=True, timeout=0.5)

    def update_local_position(self, instrument_id, volume, direction):
        """
        :return:
        """
        # TODO: 本地更新持仓，为了更高频的交易

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
                "pInputOrder:{}\tOnErrRtnOrderInsert:{}\t, ErrorMsg:{}"
                .format(
                    pInputOrder,
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
        instrument_status = pInstrumentStatus.to_dict(decode=True)
        self.logger.info(
            "OnRtnInstrumentStatus: {}"
            .format(
                instrument_status["InstrumentID"]
            )
        )
        self.instrument_status[instrument_status["InstrumentID"]] =\
            copy.deepcopy(instrument_status)

        if instrument_status["InstrumentID"] not in \
                set(self.instruments.ProductID):
            t = threading.Thread(
                target=self.prepare_instruments_info, daemon=True
            )
            t.start()
        else:
            if instrument_status["InstrumentStatus"] == 2:
                self.instruments.ix[
                    instrument_status["InstrumentID"],"IsTrading"
                ] = 1
            else:
                self.instruments.ix[
                    instrument_status["InstrumentID"],"IsTrading"
                ] = 0
        # TODO: 按字段更新self.instruments

    def OnRtnTradingNotice(self, pTradingNoticeInfo):
        """交易通知"""
        trading_notice_info = pTradingNoticeInfo.to_dict(decode=True)
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

    def OnRtnFromFutureToBankByBank(self, pRspTransfer):
        """银行发起期货资金转银行通知"""

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
