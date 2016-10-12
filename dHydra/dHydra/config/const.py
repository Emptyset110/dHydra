# -*- coding: utf-8 -*-
"""
Config
Created on 02/22/2016
@description:	Used for 
@author: 		Wen Gu
@contact: 		emptyset110@gmail.com
"""
VERSION = '0.2.0'

#	路径配置		
#	Path Configuration
PATH_DATA_ROOT = './data/'
PATH_DATA_REALTIME = 'stock_realtime/'
PATH_DATA_L2 = 'stock_l2/'

#	Mongodb连接配置
#	Mongodb Configuration


#	股票指数与代码的转换表（无需修改）
INDEX_LABELS = ['sh', 'sz', 'hs300', 'sz50', 'cyb', 'zxb', 'zx300', 'zh500']
INDEX_LIST = {'sh': 'sh000001', 'sz': 'sz399001', 'hs300': 'sz399300',
              'sz50': 'sh000016', 'zxb': 'sz399005', 'cyb': 'sz399006', 'zx300': 'sz399008', 'zh500':'sh000905',
              'HSCEI': 'sz110010',
              'HSI' : 'sz110000'
              }