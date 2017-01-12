# -*- coding: utf-8 -*-
import redis
import copy
from dHydra.core.Functions import *
from dHydra.core.Controller import controller
from dHydra.core.Controller import controller_get
from dHydra.core.Controller import controller_post

conn = get_vendor("DB").get_redis()

@controller_get
def get_worker_names(
    query_arguments,
    get_query_argument
):
    """
    从文件夹名中获取Worker names
    :param arguments:
    :return:
    """
    import dHydra.core.util as util
    worker_names = util.get_worker_names(logger=None)
    result = {
        "error_code": 0,
        "error_msg": "",
        "res": worker_names,
    }
    return result


@controller_get
def get_workers_from_redis(
    query_arguments,
    get_query_argument
):
    keys = conn.keys("dHydra.Worker.*.*.Info")
    workers = dict()
    for i in range(0, len(keys)):
        channel = keys[i]
        parsed_channel = channel.split('.')
        if (len(parsed_channel) == 5) and (parsed_channel[4] == "Info")\
            and (parsed_channel[0] == 'dHydra')\
            and (parsed_channel[1] == 'Worker'):
            if parsed_channel[2] not in workers:
                workers[parsed_channel[2]] = dict()
            worker = conn.hgetall(keys[i])
            workers[parsed_channel[2]][parsed_channel[3]] = worker
    result = {
        "error_code": 0,
        "error_msg": "",
        "res": workers,
    }
    return result


@controller
def get_alive_workers(
        query_arguments,
        body_arguments,
        get_query_argument,
        get_body_argument
):
    alive_workers = dict()
    keys = get_workers_from_redis()["res"]
    for item in keys:
        x = item.split(".")
        worker_name = x[2]
        nickname = x[3]
        info = conn.hgetall(item)
        if info["status"] == "started":
            alive_workers[nickname] = copy.deepcopy(info)
    result = {
        "error_code": 0,
        "error_msg": "",
        "res":  alive_workers,
    }
    return result


@controller
def start_worker(
        query_arguments,
        body_arguments,
        get_query_argument,
        get_body_argument
):
    import tornado.escape as escape
    worker_name = get_body_argument("worker_name")
    nickname = get_body_argument("nickname")
    kwargs = escape.json_decode(get_body_argument("kwargs"))
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
    conn.publish("dHydra.Command", msg)
    result = {
        "error_code": 0,
        "error_msg": "",
        "res": {"worker_name": worker_name, "nickname": nickname, "kwargs": kwargs }
    }
    return result

@controller_get
def stop_worker(
        query_arguments,
        get_query_argument,
):
    nickname = get_query_argument("nickname")

    msg = {
        "type": "sys",
        "operation_name": "terminate_worker",
        "kwargs": {
            "nickname": nickname
        }
    }

    conn.publish("dHydra.Command", msg)
    result = {
        "error_code": 0,
        "error_msg": "",
        "res": { "nickname": nickname }
    }
    return result
