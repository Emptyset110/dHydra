from dHydra.core.Worker import Worker
from dHydra.console import *
import os
import signal

class Monitor(Worker):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

    def start_worker(self, worker_name, **kwargs):
        worker = get_worker_class(worker_name = worker_name, **kwargs)
        worker.start()

    def terminate_worker(self, nickname = None, pid = None):
        if pid is None:
            pid = self.get_pid_by_nickname(redis_cli = self.__redis__, )
            os.kill(pid, signal.SIGTERM)

    def get_workers_info( redis_cli = None, by = "nickname", nickname = None, worker_name = None ):
        if redis_cli is None:
            redis_cli = self.__redis__
        result = list()
        keys = list()
        if by == "nickname" and nickname is not None:
            keys = redis_cli.keys("dHydra.Worker.*."+nickname+".Info")
        elif by =="worker_name" and worker_name is not None:
            keys = redis_cli.keys("dHydra.Worker."+worker_name+".*.Info")
        for k in keys:
            result.append( redis_cli.hgetall( k ) )
        return result

    def get_pid_by_nickname( redis_cli = None, nickname = None ):
        if redis_cli is None:
            redis_cli = self.__redis__
        workers_info = self.get_workers_info( redis_cli = self.__redis__, nickname = nickname )
        if len(workers_info) == 1:
            return int( workers_info[0]["pid"].decode("utf-8") )
        else:
            self.logger.warning("Worker is not Unique.")
            return 0
