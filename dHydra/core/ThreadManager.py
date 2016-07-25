# -*- coding: utf-8 -*-
import threading
import logging
import time

class Thread(threading.Thread):
    def __init__(self, target, name = None, args = list(), kwargs = dict(), cancel_thread = None, on_finished = None, del_thread = None, manager = None):
        super().__init__(target = target, args = args, kwargs = kwargs, name = name)
        self.logger = self.get_logger()
        self.on_finished = on_finished
        self.__target = target
        self.__cancel = False
        if cancel_thread is not None:
            self.__cancel_thread = cancel_thread
        else:
            self.__cancel_thread = self.cancel_thread
        self.__del_thread = del_thread
        self._manager = manager

    def get_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        return logger

    def cancel_thread(self):
        return False

    def del_thread(self):
        self.logger.info( "Deleting: {}".format( threading.current_thread().name ) )
        return self.__del_thread( name = threading.current_thread().name )

    def run(self):
        while self.__cancel is False:
            result = self.__target()
            if self.__cancel_thread is not None:
                self.__cancel = ( self.__cancel_thread() ) and ( self._manager.threads_num > self._manager.num_min )

        if self.on_finished is not None:
            self.on_finished( result )
        self.del_thread()

class Manager():
    """
    manager = Manager(   target = some_func
                    ,   args = some_args
                    ,   kwargs = some_kwargs
                    ,   num_start = 10
                    ,   num_max = 100
                    ,   num_min = 2
                    )
    """
    def __init__(   self
                ,   target
                ,   args = list()
                ,   kwargs = dict()
                ,   num_start = 1
                ,   num_max = 1
                ,   num_min = 1
                ,   set_daemon = True
                ,   need_new_thread = None
                ,   cancel_thread = None
                ,   on_finished = None
                ):
        # Private Variables
        self.__target = target
        self.__args = args
        self.__kwargs = kwargs
        self.__num_start = num_start
        self.num_max = num_max
        self.num_min = num_min
        self.__set_daemon = set_daemon
        self.__threads = dict()
        self.__need_new_thread = need_new_thread  # need_new_thread是一个返回布尔值的函数
        self.__cancel_thread = cancel_thread
        self.__on_finished = on_finished
        self.logger = self.get_logger()

        # Initializing Threads
        self.is_running = False
        for i in range( 0, self.__num_start ):
            t = Thread( target = self.__target
                    ,   args = self.__args
                    ,   kwargs = self.__kwargs
                    ,   cancel_thread = self.__cancel_thread
                    ,   on_finished = self.__on_finished
                    ,   del_thread = self.del_thread
                    ,   manager = self
                    )
            t.setDaemon( self.__set_daemon )
            self.__threads[ t.name ] = t

        # 开启manager，用来动态平衡线程数量
        t = threading.Thread( target = self.manager )
        t.setDaemon(True)
        t.start()
        t = threading.Thread( target = self.threads_monitor )
        t.setDaemon(True)
        t.start()
        return

    @property
    def threads_num(self):
        return len(self.__threads)

    def get_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.DEBUG)
        return logger

    # 开启一个独立的线程，来动态平衡线程数量
    def manager(self):
        while True:
            num_threads = len( self.__threads )
            if self.__need_new_thread():
                if num_threads >= self.num_max:
                    self.logger.warning( "需要增加线程，但是已达到用户设置的线程数量上限" )
                else:
                    self.new_thread()
                    self.logger.debug( "增加了一个线程" )
            # else:
            #     self.logger.info("无需增加线程：{}".format(self.__threads))
            time.sleep(3)

    # 开启一个独立线程来定时检查当前用于执行handler的线程池
    def threads_monitor(self):
        while True:
            self.logger.debug("当前线程池（30秒显示一次）：{}".format( self.__threads ))
            time.sleep(30)

    def del_thread(self, name):
        self.logger.debug( "{}".format( self.__threads ) )
        if name in self.__threads.keys():
            if self.threads_num > self.num_min:
                self.logger.debug( "删除线程: {}".format( name ) )
                del self.__threads[ name ]
                return True
        else:
            return False

    def new_thread(self, ):
        if len(self.__threads) < self.num_max:
            t = Thread( target = self.__target
                    ,   args = self.__args
                    ,   kwargs = self.__kwargs
                    ,   cancel_thread = self.__cancel_thread
                    ,   on_finished = self.__on_finished
                    ,   del_thread = self.del_thread
                    ,   manager = self
                    )
            self.__threads[ t.name ] = t
            t.setDaemon( self.__set_daemon )
            t.start()
            return True
        else:
            return False

    def start(self,):
        self.check_status()
        self.logger.info("start线程")
        t_keys = list(self.__threads.keys())
        for k in t_keys:
            try:
                thread = self.__threads[ k ]
            except Exception as e:
                self.logger.warning( "{}".format(e) )
            thread.start()
        self.is_running = True
        self.logger.info("线程全部开启完毕")

        self.check_status()
        return True

    def check_status(self,):
        key_list = list( self.__threads.keys() )
        for k in key_list:
            thread = self.__threads[ k ]
            self.logger.debug("thread.name ={}, thread.ident ={}, thread.is_alive = {}"\
            .format( thread.name, thread.ident, thread.is_alive() ) )
