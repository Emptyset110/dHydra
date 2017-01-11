# coding: utf-8
from dHydra.console import *
import time
"""
仅为了演示如何调用start_worker函数开启一个进程（传入参数）
将开启Ctp期货数据全市场的行情源，与存储到MongoDB的进程

注意这里的进程开启时候都用到了./config文件夹下的配置文件，
而配置帐号的ctp.json则是os.getcwd()对应的目录（与config目录同级）
"""

# 存储
start_worker(
    worker_name="CtpMdToMongo",
    nickname="CtpMdToMongo",
    config="CtpMd.json"
)

time.sleep(4)
# 开启行情源
start_worker(
    worker_name="CtpMd",
    nickname="CtpMd",
    account="ctp.json",
    config="CtpMd.json"
)