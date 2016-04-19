# -*- coding: utf8 -*-

import logging
from dHydra.app import *

def init_loger():
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    consoleHandle = logging.StreamHandler()
    consoleHandle.setFormatter(formatter)
    consoleHandle.setLevel(logging.DEBUG)
    logger.addHandler(consoleHandle)
    if not os.path.exists('log'):
        os.makedirs('log')
    #打开下面的输出到文件
    # fileHandler = logging.FileHandler('log/error.log')
    # fileHandler.setLevel(logging.ERROR)
    # fileHandler2 = logging.FileHandler('log/log.log')
    # fileHandler2.setLevel(logging.DEBUG)
    
    # logger.setLevel(logging.DEBUG)
    # logger.addHandler(fileHandler)
    # logger.addHandler(fileHandler2)

"""
初始化日志
"""

init_loger()

"""
读取数据处理模块(Action)列表
"""
actionList = ['PrintSinaL2']
"""
生成Action对象并开启actions
"""
start_action(actionList)

"""
嗯……只要这样就可以了
"""
