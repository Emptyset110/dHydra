# -*- coding: utf-8 -*-
import redis
import copy
from dHydra.core.Functions import *
import json

conn = redis.StrictRedis(decode_responses=True, host="127.0.0.1")


def get_worker_names(arguments=None):
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


def get_workers_from_redis(arguments=None):
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


def get_alive_workers(arguments=None):
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


def workers(arguments=None):
    result = {
        "error_code": 0,
        "error_msg": "",
        "res": get_workers(),
    }
    return result
