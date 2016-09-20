from dHydra.console import logger, get_worker_class
from dHydra.core.Functions import get_vendor
import click
import multiprocessing
import time
import os
import json
import traceback
import sys

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
        redis_cli = self.__redis__
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
    logger.info("{}".format(msg_command))
    msg_command = json.loads(msg_command.replace(
        "None", "\"None\"").replace("\'", "\""))
    if msg_command["type"] == "sys":
        str_kwargs = ""
        for k in msg_command["kwargs"].keys():
            if isinstance(msg_command["kwargs"][k], str):
                str_kwargs += (
                    k + "=" +
                    "\'" + msg_command["kwargs"][k] + "\'" +
                    ","
                )
            else:
                str_kwargs += (
                    k + "=" +
                    "{}".format(msg_command["kwargs"][k]) +
                    ","
                )
        try:
            logger.info(msg_command["operation_name"] + "(" + str_kwargs + ")")
            eval(msg_command["operation_name"] + "(" + str_kwargs + ")")
        except Exception as e:
            logger.error("{}".format(e))


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
                start_worker("Monitor")
                logger.info("Monitor has started")

                # open a thread for webserver
                thread_tornado = threading.Thread(
                    target=dHydra.web.start_server
                )
                thread_tornado.setDaemon(True)
                thread_tornado.start()
                logger.info("Tornado webserver has started")

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
        print("Hail What?")
        traceback.print_exc()
