# -*- coding: utf-8 -*-
import logging
from dHydra.core.Functions import *
import dHydra.core.util as util
import click
import traceback
import pickle


def init_logger():
    return util.get_logger(logger_name="console")


@click.command()
@click.argument('worker_name', nargs=1)
@click.argument('nickname', nargs=1)
def start(worker_name=None, nickname=None):
    """
    主要依靠nickname来指定配置文件，通过配置文件传入参数

    :param worker_name:
    :param nickname:
     如果nickname以.json结尾，那么程序会去"./config/"目录下寻找对应配置文件
     如果不是以.json结尾，则认为传入的就是nickname，同时会去"./config/"目录下寻找
     nickname.json
    :return:
    """
    kwargs = dict()
    kwargs["worker_name"] = worker_name
    if nickname[-5:] == ".json":
        kwargs["config"] = nickname
        kwargs["nickname"] = nickname[0:-5]
    else:
        kwargs["config"] = nickname + ".json"
        kwargs["nickname"] = nickname
    config_file = os.path.join(os.getcwd(), "config", kwargs["config"])
    if os.path.exists(config_file):
        config = util.read_config(config_file)
    else:
        # 命令指定了配置文件，如果不存在，就结束
        print("未能找到配置文件：", config_file)
        print("默认无配置启动")
        config = {}

    for k in config.keys():
        kwargs[k] = config[k]

    msg = {
        "type": "sys",
        "operation_name": "start_worker",
        "kwargs": kwargs
    }
    __redis__.publish("dHydra.Command", pickle.dumps(msg))


@click.command()
@click.argument('nickname', nargs=1)
def terminate(nickname=None):
    msg = {"type": "sys", "operation_name": "terminate_worker",
           "kwargs": {"nickname": nickname}}
    if nickname is not None:
        msg["kwargs"]["nickname"] = nickname
        __redis__.publish("dHydra.Command", pickle.dumps(msg))


def start_worker(worker_name=None, nickname=None, **kwargs):
    msg = {
        "type": "sys",
        "operation_name": "start_worker",
        "kwargs": {
            "worker_name": worker_name,
            "nickname": nickname
        },
    }

    for k in kwargs.keys():
        msg["kwargs"][k] = kwargs[k]
    __redis__.publish("dHydra.Command", pickle.dumps(msg))


def stop_worker(nickname=None):
    msg = {
        "type": "sys",
        "operation_name": "terminate_worker",
        "kwargs": {
            "nickname": nickname
        }
    }

    __redis__.publish("dHydra.Command", pickle.dumps(msg))


def send_command(
        channel_name="dHydra.Command",
        command_type="sys",
        operation_name=None,
        token=None,
        kwargs={}
):
    if operation_name is not None:
        command = {
            "type": command_type,
            "operation_name": operation_name,
            "token": token,
            "kwargs": kwargs
        }
        __redis__.publish(channel_name, pickle.dumps(command))

logger = init_logger()
__redis__ = get_vendor("DB").get_redis()
