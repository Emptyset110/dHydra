# -*- coding: utf8 -*-
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
from dHydra.app import PRODUCER_NAME, PRODUCER_HASH
import logging
import os

print("加载：Functions.py")

if not os.path.exists('log'):
	os.makedirs('log')

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = open('log/error.log','a')
log.close()
fileHandler = logging.FileHandler('log/error.log')
fileHandler.setLevel(logging.WARNING)
logger = logging.getLogger("Error")
logger.setLevel(logging.WARNING)
logger.addHandler(fileHandler)

def get_logger(name):
	print(name)
	log = open('log/%s.log'%name,'a')
	log.close()
	# 定义handler的输出格式  
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

	fileHandler = logging.FileHandler('log/%s.log'%name)
	# 日志记录所有
	fileHandler.setLevel(logging.DEBUG)
	fileHandler.setFormatter(formatter)

	# 屏幕输出/error/critical
	consoleHandler = logging.StreamHandler()  
	consoleHandler.setLevel(logging.ERROR)
	consoleHandler.setFormatter(formatter)

	l = logging.getLogger(name)
	l.setLevel(logging.DEBUG)
	l.addHandler(fileHandler)
	l.addHandler(consoleHandler)

	return l

"""
V方法，动态加载数据API类
V可以用Vendor来记忆
"""
def V(name, vName = None):
	if vName is None:
		vName = "V-"+name
	className = name + 'Vendor'
	name = 'vendor.' + name + '.' + className
	try:
		instance = getattr( __import__(name, globals(),locals(),[className], 0), className )()
	except ImportError:
		try:
			instance = getattr( __import__("dHydra."+name, globals(),locals(),[className], 0), className )()
		except Exception as e:
			logger.critical(e)
	except Exception as e:
		logger.critical(e)

	return instance


"""
P方法，动态获取生产者类
P可以用Producer来记忆
"""
def P(name, pName, **kwargs):
	if pName is None:
		print("pName参数不允许为空，请给producer实例设置一个名字")
		print("命名规范：<actionName.producerName>")
		return False
	# 将参数排序来保证唯一性
	json_kwargs = json.dumps( sorted(kwargs.items()) )
	producerHash = hashlib.sha1( ('name'+json_kwargs).encode('utf8') ).hexdigest()

	if producerHash in PRODUCER_HASH:
		# 这个Instance已经存在
		PRODUCER_NAME[pName] = PRODUCER_HASH[producerHash]
		return PRODUCER_HASH[producerHash]
	else:
		className = name + 'Producer'
		name = 'producer.' + name + '.' + className
		try:
			instance = getattr( __import__(name, globals(),locals(),[className], 0), className )(name=pName, **kwargs)
		except ImportError:
			try:
				instance = getattr( __import__("dHydra."+name, globals(),locals(),[className], 0), className )(name=pName, **kwargs)
			except Exception as e:
				logger.critical(e)
				exit()
		except Exception as e:
			logger.critical(e)
			exit()

		# print(instance)
		PRODUCER_NAME[pName] = instance
		PRODUCER_HASH[producerHash] = instance
		logger.info("生成Producer:\t",pName,"\t",className)
		return instance

"""
A方法，动态获取Action类
A可以用Action来记忆
"""
def A(name, aName = None, **kwargs):
	if aName is None:
		aName = "A-" + name
	className = name + 'Action'
	name = 'action.' + name + '.' + className
	try:
		return getattr( __import__(name, globals(),locals(),[className], 0), className )(name=aName, **kwargs)
	except ImportError:
		try:
			return getattr( __import__("dHydra." + name, globals(),locals(),[className], 0), className )(name=aName, **kwargs)
		except Exception as e:
			logger.critical(e)

"""
根据pName或者hash获取已经生成的Producer实例
"""
def get_producer(pName = None, pHash = None):
	if ( pName is None and pHash is None ):
		logger.error("错误：pName和pHash两个参数中至少要有一个不为空")
		return False
	try:
		return PRODUCER_NAME[pName]
	except:
		try:
			return PRODUCER_HASH[pHash]
		except:
			logger.error("没有找到对应的Producer")
			return False
		