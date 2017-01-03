from dHydra.console import logger, get_worker_class
from dHydra.core.Functions import get_vendor
import click
import multiprocessing
import time
import os
import json
import traceback
import sys
import pickle

__redis__ = get_vendor("DB").get_redis()

__current_process__ = multiprocessing.current_process()
worker_dict = dict()


def __on_termination__(sig, frame):
    logger.info("The dHydra Server is about to terminate, pid:{}"
                .format(os.getpid())
                )
    sys.exit(0)


def bind_quit_signals():
    import signal
    shutdown_signals = [
        "SIGQUIT",  # quit 信号
        "SIGINT",  # 键盘信号
        "SIGHUP",  # nohup 命令
        "SIGTERM",  # kill 命令
    ]
    for s in shutdown_signals:
        if hasattr(signal, s):
            signal.signal(
                getattr(signal, s, None),
                __on_termination__
            )


def start_worker(worker_name, **kwargs):
    worker = get_worker_class(worker_name=worker_name, **kwargs)
    worker_dict[worker.nickname] = worker
    worker.start()


def terminate_worker(nickname=None, pid=None):
    import signal
    logger.info("{}".format(worker_dict))
    if pid is None:
        pid = get_pid_by_nickname(redis_cli=__redis__, nickname=nickname)
        os.kill(pid, signal.SIGTERM)
        i = 0
        while worker_dict[nickname]._popen is None and i < 30:
            time.sleep(0.1)
            i += 1
        worker_dict[nickname]._popen.wait(1)
        worker_dict.pop(nickname)


def get_workers_info(
        redis_cli=None,
        by="nickname",
        nickname=None,
        worker_name=None,
):
    if redis_cli is None:
        redis_cli = __redis__
    result = list()
    keys = list()
    if by == "nickname" and nickname is not None:
        keys = redis_cli.keys("dHydra.Worker.*." + nickname + ".Info")
    elif by == "worker_name" and worker_name is not None:
        keys = redis_cli.keys("dHydra.Worker." + worker_name + ".*.Info")
    for k in keys:
        result.append(redis_cli.hgetall(k))
    return result


def get_pid_by_nickname(redis_cli=None, nickname=None):
    if redis_cli is None:
        redis_cli = __redis__
    workers_info = get_workers_info(redis_cli=__redis__, nickname=nickname)
    if len(workers_info) == 1:
        return int(workers_info[0]["pid"])
    else:
        logger.warning("Worker is not Unique.")
        return 0


def __command_handler__(msg_command):
    # msg_command is a dict with the following structure:
    """
    msg_command = {
        "type"	:		"sys/customized",
        "operation"	:	"operation_name",
        "kwargs"	:	"suppose that the operation is a function, we need to
                         pass some arguments",
        "token"		:	"the token is used to verify the authentication of the
                         operation"
        }
    """
    import sys
    try:
        msg_command = pickle.loads(msg_command)
        if not isinstance(msg_command, dict):
            return
    except Exception as e:
        traceback.print_exc()
        print(e)
    if msg_command["type"] == "sys":
        if hasattr(
                sys.modules["dHydra.main"],
                msg_command["operation_name"]
        ):
            func = getattr(
                sys.modules["dHydra.main"],
                msg_command["operation_name"]
            )
            try:
                print(msg_command["kwargs"])
                result = func(**msg_command["kwargs"])
            except Exception as e:
                traceback.print_exc()
                logger.error(e)


@click.command()
@click.argument('what', nargs=-1)
def hail(what=None):
    import threading
    import time
    import dHydra.web

    try:
        if what:
            if what[0] != "dHydra":
                print("Hail What??")
                exit(0)
            else:
                print(
                    "Welcome to dHydra! Following is the "
                    "Architecture of dHydra"
                )
                doc = \
                    """
    "hail dHydra"
         |
         |
    ┌────┴─────┐         ┌────────────┐
    |  dHydra  |         |   Tornado  |
    |  Server  ├─────────┤ Web Server ├──http://127.0.0.1:5000────┐
    └────┬─────┘         └──────┬─────┘                           |
         |                      |               默认两种url映射规则，例如：
    ┌────┴────┐                 |               /api/Worker/BackTest/method/
    |  Redis  ├─────────────────┘               /Worker/BackTest/index
    └──┬──────┘                                          详情参考文档
       |                                                          |
       ├─────Publish────┬─────Subscribe──────┬─────Publish───┐────┤
       |                |                    |               |
┌──────┴──┐        ┌────┴─────┐         ┌────┴─────┐    ┌────┴─────┐
| (Worker)|        | (Worker) |         | (Worker) |    | (Worker) |
| CTP     |        | Strategy |         | BackTest |    | Sina L2  |
└─────────┘        └──────────┘         └──────────┘    └──────────┘
"""
                print(doc)
                # open a thread for the Worker of Monitor
                start_worker(worker_name="Monitor",nickname="Monitor")
                logger.info("Monitor has started")

                # 开启Tornado
                if len(what) == 1:
                    # 没指定http端口，不开启Tornado
                    pass
                else:
                    port = int(what[1])
                    start_worker(worker_name="Web", nickname="Tornado")

            # 绑定退出信号
            bind_quit_signals()

            redis_conn = get_vendor("DB").get_redis()
            command_listener = redis_conn.pubsub()
            channel_name = "dHydra.Command"
            command_listener.subscribe([channel_name])
            while True:
                msg_command = command_listener.get_message()
                if msg_command:
                    if msg_command["type"] == "message":
                        __command_handler__(msg_command["data"])
                else:
                    time.sleep(0.1)
        else:
            print("Hail What?")
    except Exception as e:
        traceback.print_exc()
        logger.error("{}".format(e))
        print("Hail What?")
