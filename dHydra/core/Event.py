# -*- coding: utf8 -*-
"""
为了规范推送数据的格式
推荐用Event对象进行数据推送
通常需要设置几个参数：
	eventType指这个事件的类型：
		由于action从不同的producer获取Event，action需要被告知这个event是什么类型的
	dataType是指data的数据类型：
		例如dataframe，json等等
		同一个producer很可能产生不同数据类型的数据，因此，需要用dataType来进行注明
	data： 
		需要传递的数据主体
	timestamp： 
		数据产生的时间戳

"""
class Event:

	def __init__(
					self
				,	eventType = None
				,	dataType = None
				,	timestamp = None
				,	data = None):
		self.eventType = eventType
		self.dataType = dataType
		self.timestamp = timestamp
		self.data = data