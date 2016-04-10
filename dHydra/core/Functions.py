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

print("加载：Functions.py")

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
			print(e)
	except Exception as e:
		print(e)

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
				print(e)
				exit()
		except Exception as e:
			print(e)
			exit()

		# print(instance)
		PRODUCER_NAME[pName] = instance
		PRODUCER_HASH[producerHash] = instance
		print("生成Producer:\t",pName,"\t",className)
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
			print(e)

"""
根据pName或者hash获取已经生成的Producer实例
"""
def get_producer(pName = None, pHash = None):
	if ( pName is None and pHash is None ):
		print("错误：pName和pHash两个参数中至少要有一个不为空")
		return False
	try:
		return PRODUCER_NAME[pName]
	except:
		try:
			return PRODUCER_HASH[pHash]
		except:
			print("没有找到对应的Producer")
			return False
		