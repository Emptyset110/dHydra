# -*- coding: utf-8 -*-
import logging
from dHydra.core.Functions import *
import click

def init_loger():
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)

	# 屏幕日志打印设置
	console_handler = logging.StreamHandler()
	console_handler.setFormatter(formatter)
	console_handler.setLevel(logging.INFO)
	logger.addHandler(console_handler)

	if not os.path.exists('log'):
		os.makedirs('log')
	# 打开下面的输出到文件
	file_handler = logging.FileHandler('log/error.log')
	file_handler.setLevel(logging.ERROR)
	file_handler.setFormatter(formatter)
	file_handler2 = logging.FileHandler('log/debug.log')
	file_handler2.setLevel(logging.DEBUG)
	file_handler2.setFormatter(formatter)

	logger.setLevel(logging.INFO)
	logger.addHandler(file_handler)
	logger.addHandler(file_handler2)

@click.command()
@click.argument('worker_name', nargs = 1)
@click.argument('nickname', nargs = -1)
def start(worker_name = None, nickname = None):
    msg = { "type":"sys", "operation_name":"start_worker", "kwargs": { "worker_name": worker_name } }
    if nickname is not None:
        msg["kwargs"]["nickname"] = nickname[0]
    __redis__.publish( "dHydra.Command", msg )

@click.command()
@click.argument('nickname', nargs = 1)
def terminate(nickname = None):
    msg = { "type":"sys", "operation_name":"terminate_worker", "kwargs": { "nickname": nickname } }
    if nickname is not None:
        msg["kwargs"]["nickname"] = nickname
        __redis__.publish( "dHydra.Command", msg )

def start_worker(worker_name = None, nickname = None, **kwargs):
    msg = { "type":"sys", "operation_name":"start_worker", "kwargs": { "worker_name": worker_name } }
    if nickname is not None:
        msg["kwargs"]["nickname"] = nickname[0]
    for k in kwargs.keys():
        msg["kwargs"][k] = kwargs[k]
    __redis__.publish( "dHydra.Command", msg )

def send_command(channel_name = "dHydra.Command", command_type = "sys", operation_name = None, token = None, kwargs = {} ):
	if operation_name is not None:
		command = { 	"type":command_type
					,	"operation_name": operation_name
					,	"token" : token
		 			,	"kwargs": kwargs
				}
		__redis__.publish( channel_name, json.dumps(command) )

init_loger()
__redis__ = get_vendor("DB").get_redis()
