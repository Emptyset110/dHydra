# -*- coding: utf-8 -*-
"""
dHydra框架的全局方法，在主程序运行时会被引用
---
Created on 03/27/2016
@author: Wen Gu
@contact: emptyset110@gmail.com
"""
import importlib
import sys
import json
import hashlib
import os
import logging
import traceback


def get_workers():
    candidates = set(os.listdir("./Worker")) | set(os.listdir(
        os.path.split(os.path.realpath(__file__))[0][:-4] + "Worker"))
    candidates = list(candidates)
    workers = list()
    for item in candidates:
        if (item[0] >= "A" and item[0] <= "Z"):
            workers.append(item)
    return workers

"""
动态加载web controller
"""


def get_controller_method(class_name, method):
    logger = logging.getLogger("Functions")
    # get instance of controller
    if os.path.exists(
        os.getcwd() + "/Worker/" +
        class_name + "/" + "Controller.py"
    ):
        func = getattr(
            importlib.import_module("Worker." + class_name + ".Controller"),
            method
        )
        return func
    else:
        try:
            func = getattr(importlib.import_module(
                "dHydra.Worker." + class_name + ".Controller"),
                method
            )
            return func
        except Exception as e:
            return False


def V(name, vendor_name=None, **kwargs):
    return get_vendor(name=name, vendor_name=None, **kwargs)


def get_vendor(name, vendor_name=None, **kwargs):
    """
    get_vendor方法，动态加载vendor类
    """
    logger = logging.getLogger('Functions')
    if vendor_name is None:
        vendor_name = "V-" + name
    class_name = name
    module_name = 'Vendor.' + name + '.' + class_name
    if os.path.exists(
        os.getcwd() + "/Vendor/" +
        name + "/" + class_name + ".py"
    ):
        try:
            instance = getattr(
                __import__(module_name, globals(), locals(), [class_name], 0),
                class_name
            )(**kwargs)
        except ImportError:
            traceback.print_exc()
    else:
        try:
            instance = getattr(
                __import__(
                    "dHydra." + module_name,
                    globals(),
                    locals(),
                    [class_name],
                    0
                ),
                class_name
            )(**kwargs)
        except ImportError:
            traceback.print_exc()
    return instance


def get_worker_class(worker_name, **kwargs):
    logger = logging.getLogger('Functions')
    module_name = 'Worker.' + worker_name + '.' + worker_name
    if os.path.exists(
        os.getcwd() + "/Worker/" +
        worker_name + "/" + worker_name + ".py"
    ):
        try:
            return getattr(
                __import__(module_name, globals(), locals(), [worker_name], 0),
                worker_name
            )(**kwargs)
        except ImportError:
            traceback.print_exc()
    else:
        try:
            return getattr(
                __import__(
                    "dHydra." +
                    module_name,
                    globals(),
                    locals(),
                    [worker_name],
                    0
                ),
                worker_name
            )(**kwargs)
        except ImportError:
            traceback.print_exc()
