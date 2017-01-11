from ctp.futures import ApiStruct, TraderApi
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
            "CtpMiniTrader: 成功获取Instruments:{}个"
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


class CtpMiniTrader(TraderApi):
    """
    这个迷你Trader只为了更新InstrumentID
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
        # self.user_login = None  # 用户登录应答的缓存
        # self.trading_account = None  # 资金账户
        # self.trading_account_last_updated = None  # 资金账户上次更新时间
        # position
        # self.position = None    # DataFrame类型

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
        import hashlib
        import tempfile
        import sys
        """初始化连接"""
        self.user_id = user_id                # 账号
        self.password = password            # 密码
        self.broker_id = broker_id            # 经纪商代码
        self.trade_front = trade_front              # 服务器地址

        # 如果尚未建立服务器连接，则进行连接
        if not self.is_connected:
            # 创建C++环境中的API对象，这里传入的参数是需要用来保存.con文件的文件夹路径
            dir = b''.join((b'ctp.futures', self.broker_id, self.user_id))
            dir = hashlib.md5(dir).hexdigest()
            dir = os.path.join(tempfile.gettempdir(), dir, 'Md') + os.sep
            if not os.path.isdir(dir):
                os.makedirs(dir)
            self.Create(os.fsencode(dir) if sys.version_info[0] >= 3 else dir)

            # 注册服务器地址
            self.RegisterFront(self.trade_front)

            # 订阅公共流
            self.SubscribePublicTopic(ApiStruct.TERT_QUICK)

            # 订阅私有流
            self.SubscribePrivateTopic(ApiStruct.TERT_QUICK)

            # 初始化连接，成功会调用OnFrontConnected
            self.Init()

            self.logger.info(
                "CTP Initialization has completed."
            )

        # 若已经连接但尚未登录，则进行登录
        # CtpMiniTrader暂时不登录

        # else:
        #     if not self.is_login:
        #         self.req_user_login()

    def OnFrontConnected(self):
        """
        当客户端与交易后台建立起通信连接时（还未登录前），该方法被调用。
        """
        self.is_connected = True
        self.logger.info(
            "MiniTrader: Successfully connected to the Trader Front, "
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
        if pRspInfo.ErrorID == 0:
            self.front_id = pRspUserLogin.FrontID
            self.session_id = pRspUserLogin.SessionID
            self.is_login = True

            self.logger.info(
                "CtpMiniTrader Login Successfully:{}"
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
            time.sleep(60)
            self.connect(
                self.user_id,
                self.password,
                self.broker_id,
                self.trade_front
            )

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

        t = threading.Thread(
            target=self.prepare_instruments_info, daemon=True
        )
        t.start()
