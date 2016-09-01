# -*- coding: utf-8 -*-
import redis
import copy
from dHydra.core.Functions import *
import json

conn = redis.StrictRedis(decode_responses=True, host = "127.0.0.1")

def get_workers_from_redis( arguments = None ):
    keys = conn.keys("dHydra.Worker.*.*.Info")
    for i in range(0, len(keys)):
        keys[i] = keys[i]
    result = {
        "error_code" : 0,
        "error_msg" : "",
        "res"       : keys,
    }
    return result

def get_alive_workers( arguments = None ):
    alive_workers = dict()
    keys = get_workers_from_redis()["res"]
    for item in keys:
        x = item.split(".")
        worker_name = x[2]
        nickname = x[3]
        info = conn.hgetall( item )
        if info["status"] == "started":
            alive_workers[nickname] = copy.deepcopy(info)
    result = {
        "error_code" : 0,
        "error_msg" : "",
        "res"       :  alive_workers ,
    }
    return result


def workers( arguments = None ):
    result = {
        "error_code" : 0,
        "error_msg" : "",
        "res"       : get_workers(),
    }
    return result
