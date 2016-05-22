# -*- coding: utf-8 -*-
import sys
import os
def new_vendor(vendorName = None):
	dirVendor = "vendor/"+vendorName
	if os.path.exists(dirVendor):
		print("[创建失败]：目录 "+dirVendor+"已经存在")
	else:
		os.makedirs( dirVendor )
		# 创建vendorNameVendor.py
		f = open( dirVendor + '/' + vendorName + 'Vendor.py' , 'w' , encoding= 'UTF-8')
		f.write(
		"""# -*- coding: utf-8 -*-
\"\"\"
# Created on
# @author:
# @contact:
\"\"\"
# 以下是自动生成的 #
# --- 导入系统配置
import dHydra.core.util as util
from dHydra.core.Vendor import Vendor
from dHydra.config import connection as CON
from dHydra.config import const as C
# --- 导入自定义配置
from .connection import *
from .const import *
from .config import *
# 以上是自动生成的 #

class {}(Vendor):
	def __init__(self):
		pass
		""".format(vendorName+"Vendor")
			)
		f.close()
		# 创建config,connection,const, __init__.py
		f = open( dirVendor + '/config.py', 'w', encoding= 'UTF-8' )
		f.close()
		f = open( dirVendor + '/const.py', 'w', encoding= 'UTF-8' )
		f.close()
		f = open( dirVendor + '/connection.py', 'w', encoding= 'UTF-8' )
		f.close()
		f = open( dirVendor + '/__init__.py', 'w', encoding= 'UTF-8' )
		f.close()

def new_producer(producerName = None):
	dirProducer = "producer/" + producerName
	if os.path.exists(dirProducer):
		print("[创建失败]：目录 "+dirProducer+"已经存在")
	else:
		os.makedirs( dirProducer )
		# 创建producerNameProducer.py
		f = open( dirProducer + '/' + producerName + 'Producer.py', 'w', encoding= 'UTF-8' )
		if producerName == 'Demo':
			demo = """
		# handler是需要被重写的方法，以下demo每隔0.5秒产生一个数据
		# 并且把数据推送给它的订阅者
		import time
		i = 0
		while ( self._active ):
			event = Event(event_type = 'Demo', data = i)
			for q in self._subscriber:
				q.put(event)
				print("DemoProducer:", event.data)
			i += 1
			time.sleep(0.5)
			"""
		else:
			demo = ""
		f.write(
		"""# -*- coding: utf-8 -*-
\"\"\"
# Created on
# @author:
# @contact:
\"\"\"
# 以下是自动生成的 #
# --- 导入系统配置
from dHydra.app import PRODUCER_NAME, PRODUCER_HASH
import dHydra.core.util as util
from dHydra.core.Producer import Producer
from dHydra.core.Event import Event
from dHydra.config import connection as CON
from dHydra.config import const as C
from dHydra.core.Functions import *
# --- 导入自定义配置

# 以上是自动生成的 #

class {}Producer(Producer):
	def __init__(self, name = None, **kwargs):
		super().__init__( name=name, **kwargs )

	def handler(self):{}
		pass
		""".format(producerName, demo)
			)
		f.close()
		# 创建config,connection,const, __init__.py
		f = open( dirProducer + '/config.py', 'w', encoding= 'UTF-8' )
		f.close()
		f = open( dirProducer + '/const.py', 'w', encoding= 'UTF-8' )
		f.close()
		f = open( dirProducer + '/connection.py', 'w', encoding= 'UTF-8' )
		f.close()
		f = open( dirProducer + '/__init__.py', 'w', encoding= 'UTF-8' )
		f.close()

def new_action(actionName = None):
	dirAction = "action/" + actionName
	if os.path.exists(dirAction):
		print("[创建失败]：目录 "+dirAction+"已经存在")
	else:
		os.makedirs( dirAction )
		# 创建actionNameAction.py
		f = open( dirAction + '/' + actionName + 'Action.py', 'w', encoding= 'UTF-8' )
		if actionName == "Demo":
			demo="""
		while not self._queue.empty():
			event = self._queue.get(True)
			print("DemoAction:", event.data)
			# 当收到数字15时，就停止action
			if event.data == 15:
				self._stop()
			"""
		else:
			demo = """
		pass"""
		f.write("""# -*- coding: utf-8 -*-
\"\"\"
# Created on
# @author:
# @contact:
\"\"\"
# 以下是自动生成的 #
# --- 导入系统配置
from dHydra.app import PRODUCER_NAME, PRODUCER_HASH
import dHydra.core.util as util
from dHydra.core.Action import Action
from dHydra.core.Event import Event
from dHydra.config import connection as CON
from dHydra.config import const as C
from dHydra.core.Functions import *
# --- 导入自定义配置

# 以上是自动生成的 #
class %sAction(Action):
	def __init__(self, name, **kwargs):
		# 用户自定义自动加载的_producer_list
		self._producer_list = [
			{
				"name"	:	"Demo"
			,	"producer_name"	:	"Demo.Demo"		#这是在action内部给producer起的自定义名字，可随意。一般最好遵守<actionName.producerName>
			}
		]
		# 设置进程检查消息队列的间隔
		self._interval = 0.5
		super().__init__(name, **kwargs)
		print(self._name,"初始化")

	# 需要重写的方法
	def handler(self):
%s
			""" % (actionName, demo)
			)
		f.close()
		# 创建config,connection,const, __init__.py
		f = open( dirAction + '/config.py', 'w', encoding= 'UTF-8' )
		f.close()
		f = open( dirAction + '/const.py', 'w', encoding= 'UTF-8' )
		f.close()
		f = open( dirAction + '/connection.py', 'w', encoding= 'UTF-8' )
		f.close()
		f = open( dirAction + '/__init__.py', 'w', encoding= 'UTF-8' )
		f.close()

def init( demo = True ):
	os.makedirs( "data" , exist_ok=True )
	os.makedirs( "producer" , exist_ok=True )
	os.makedirs( "vendor" , exist_ok=True )
	os.makedirs( "action" , exist_ok=True )
	print("目录结构已经生成")
	f = open('config.json', 'w', encoding="UTF-8")
	f.write(
		"""{

}""")
	f.close()
	f = open('test.py', 'w', encoding='UTF-8')
	f.write(
		"""# -*- coding: utf-8 -*-
import logging
from dHydra.app import *

def init_loger():
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)

	# 屏幕日志打印设置
	console_handler = logging.StreamHandler()
	console_handler.setFormatter(formatter)
	console_handler.setLevel(logging.ERROR)
	logger.addHandler(console_handler)

	if not os.path.exists('log'):
		os.makedirs('log')
	# 打开下面的输出到文件
	file_handler = logging.FileHandler('log/error.log')
	file_handler.setLevel(logging.ERROR)
	file_handler.setFormatter(formatter)
	file_handler2 = logging.FileHandler('log/log.log')
	file_handler2.setLevel(logging.INFO)
	file_handler2.setFormatter(formatter)

	logger.setLevel(logging.INFO)
	logger.addHandler(file_handler)
	logger.addHandler(file_handler2)

\"\"\"
初始化日志
\"\"\"
init_loger()
		"""
	)
	f.close()
	if os.path.exists('app.py'):
		print("[创建失败]：app.py已经存在")
	else:
		if demo:
			f = open( 'app.py', 'w', encoding= 'UTF-8' )
			f.write(
				"""# -*- coding: utf-8 -*-

import logging
from dHydra.app import *

def init_loger():
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # 屏幕日志打印设置
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.ERROR)
    logger.addHandler(console_handler)

    if not os.path.exists('log'):
        os.makedirs('log')
    # 打开下面的输出到文件
    file_handler = logging.FileHandler('log/error.log')
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)
    file_handler2 = logging.FileHandler('log/log.log')
    file_handler2.setLevel(logging.INFO)
    file_handler2.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(file_handler2)

\"\"\"
初始化日志
\"\"\"

init_loger()

\"\"\"
读取数据处理模块(Action)列表
\"\"\"
action_list = ['PrintSinaL2']
action_args = {
	"PrintSinaL2": {
		"producer_list" : [
		{
			"name"	  :	"SinaLevel2WS"
		,   "producer_name"	 :   "L2.Quotation"
		,   "query"	 :   ['quotation']
		}
		]
		,	"raw" : False
	}
}
\"\"\"
生成Action对象并开启actions
\"\"\"
start_action(action_list,action_args)

\"\"\"
嗯……只要这样就可以了
\"\"\"
				"""
				)
			f.close()
