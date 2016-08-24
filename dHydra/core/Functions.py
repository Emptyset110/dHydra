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
from dHydra.app import PRODUCER_NAME, PRODUCER_HASH
import os
import logging
import traceback
# print("加载：Functions.py")


"""
V方法，动态加载数据API类
V可以用Vendor来记忆
"""
def V(name, vendor_name = None, **kwargs):
	logger = logging.getLogger('Functions')
	if vendor_name is None:
		vendor_name = "V-"+name
	class_name = name + 'Vendor'
	module_name = 'vendor.' + name + '.' + class_name
	if os.path.exists(os.getcwd()+"/vendor/"+name+"/"+class_name+".py"):
		try:
			instance = getattr( __import__(module_name, globals(),locals(),[class_name], 0), class_name )(**kwargs)
		except ImportError:
			traceback.print_exc()
	else:
		try:
			instance = getattr( __import__("dHydra."+module_name, globals(),locals(),[class_name], 0), class_name )(**kwargs)
		except ImportError:
			traceback.print_exc()

	return instance


"""
P方法，动态获取生产者类
P可以用Producer来记忆
"""
def P(name, producer_name, **kwargs):
	logger = logging.getLogger('Functions')
	if producer_name is None:
		print("producer_name参数不允许为空，请给producer实例设置一个名字")
		print("命名规范：<actionName.producerName>")
		return False
	# 将参数排序来保证唯一性
	json_kwargs = json.dumps( sorted(kwargs.items()) )
	producer_hash = hashlib.sha1( ('name'+json_kwargs).encode('utf8') ).hexdigest()

	if producer_hash in PRODUCER_HASH:
		# 这个Instance已经存在
		print( "Producer已经存在" )
		PRODUCER_NAME[producer_name] = PRODUCER_HASH[producer_hash]
		return PRODUCER_HASH[producer_hash]
	else:
		class_name = name + 'Producer'
		module_name = 'producer.' + name + '.' + class_name
		if os.path.exists(os.getcwd()+"/producer/"+name+"/"+class_name+".py"):
			try:
				instance = getattr( __import__(module_name, globals(),locals(),[class_name], 0), class_name )(name=producer_name, **kwargs)
			except ImportError:
				traceback.print_exc()
		else:
			try:
				instance = getattr( __import__("dHydra."+module_name, globals(),locals(),[class_name], 0), class_name )(name=producer_name, **kwargs)
			except ImportError:
				traceback.print_exc()

		# print(instance)
		PRODUCER_NAME[producer_name] = instance
		PRODUCER_HASH[producer_hash] = instance
		logger.info("生成Producer:\t{}\t{}".format(producer_name,class_name) )
		return instance

"""
A方法，动态获取Action类
A可以用Action来记忆
"""
def A(name, action_name = None, **kwargs):
	logger = logging.getLogger('Functions')
	if action_name is None:
		action_name = "A-" + name
	class_name = name + 'Action'
	module_name = 'action.' + name + '.' + class_name
	if os.path.exists(os.getcwd()+"/action/"+name+"/"+class_name+".py"):
		try:
			return getattr( __import__(module_name, globals(),locals(),[class_name], 0), class_name )(name=action_name, **kwargs)
		except ImportError:
			traceback.print_exc()
	else:
		try:
			return getattr( __import__("dHydra." + module_name, globals(),locals(),[class_name], 0), class_name )(name=action_name, **kwargs)
		except ImportError:
			traceback.print_exc()

"""
根据producer_name或者hash获取已经生成的Producer实例
"""
def get_producer(producer_name = None, pHash = None):
	logger = logging.getLogger('Functions')
	if ( producer_name is None and pHash is None ):
		logger.error("错误：producer_name和pHash两个参数中至少要有一个不为空")
		return False
	try:
		return PRODUCER_NAME[producer_name]
	except:
		try:
			return PRODUCER_HASH[pHash]
		except:
			logger.error("没有找到对应的Producer")
			return False
