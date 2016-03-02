# -*- coding: utf8 -*-
"""
Config类
Created on 02/22/2016
@description:	Used for 
@author: 		Wen Gu
@contact: 		emptyset110@gmail.com
"""
import const

class Config:

	def __init__(self):
		self.VERSION = const.VERSION

	def reset(self):
		self.__init__()
		print "The configuration has been reset"