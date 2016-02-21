# -*- coding: utf8 -*-
"""
本脚本用于实时接收股票数据
Created on 02/17/2016
@author: Wen Gu
@contact: emptyset110@gmail.com
"""
import dHydra

# Get an instance of stock
stock = dHydra.Stock()

stock.start_realtime()

