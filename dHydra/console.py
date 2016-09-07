# -*- coding: utf-8 -*-
import logging
from dHydra.core.Functions import *
import dHydra.core.util as util
import click


def init_logger():
    return util.get_logger(logger_name="console")


@click.command()
@click.argument('worker_name', nargs=1)
@click.argument('nickname', nargs=-1)
def start(worker_name=None, nickname=None):
    msg = {
        "type": "sys",
        "operation_name": "start_worker",
        "kwargs": {
                "worker_name": worker_name
        }
    }
    if nickname is not None:
        msg["kwargs"]["nickname"] = nickname[0]
    __redis__.publish("dHydra.Command", msg)


@click.command()
@click.argument('nickname', nargs=1)
def terminate(nickname=None):
    msg = {"type": "sys", "operation_name": "terminate_worker",
           "kwargs": {"nickname": nickname}}
    if nickname is not None:
        msg["kwargs"]["nickname"] = nickname
        __redis__.publish("dHydra.Command", msg)


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
    __redis__.publish("dHydra.Command", msg)


def stop_worker(nickname=None):
    msg = {
        "type": "sys",
        "operation_name": "terminate_worker",
        "kwargs": {
            "nickname": nickname
        }
    }

    __redis__.publish("dHydra.Command", msg)


def send_command(channel_name="dHydra.Command",
                 command_type="sys",
                 operation_name=None,
                 token=None,
                 kwargs={}):
    if operation_name is not None:
        command = {"type": command_type,
                   "operation_name": operation_name,
                   "token": token,
                   "kwargs": kwargs
                   }
        __redis__.publish(channel_name, json.dumps(command))

logger = init_logger()
__redis__ = get_vendor("DB").get_redis()
