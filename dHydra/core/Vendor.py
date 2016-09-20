# -*- coding: utf-8 -*-
import logging
import dHydra.core.util as util


class Vendor:

    def __init__(
        self,
        log_path="log",                     #
        console_log=True,                   # 屏幕打印日志开关，默认True
        console_log_level=logging.INFO,     # 屏幕打印日志的级别，默认为INFO
        critical_log=False,                 # critica单独l写文件日志，默认关闭
        error_log=True,                     # error级别单独写文件日志，默认开启
        warning_log=False,                  # warning级别单独写日志，默认关闭
        info_log=True,                      # info级别单独写日志，默认开启
        debug_log=False,                    # debug级别日志，默认关闭
    ):
        self.logger = util.get_logger(
            log_path=log_path,                     #
            console_log=console_log,              # 屏幕打印日志开关，默认True
            console_log_level=console_log_level,  # 屏幕打印日志的级别，默认为INFO
            critical_log=critical_log,        # critica单独l写文件日志，默认关闭
            error_log=error_log,             # error级别单独写文件日志，默认开启
            warning_log=warning_log,         # warning级别单独写日志，默认关闭
            info_log=info_log,               # info级别单独写日志，默认开启
            debug_log=debug_log,             # debug级别日志，默认关闭
            logger_name=self.__class__.__name__,
        )
