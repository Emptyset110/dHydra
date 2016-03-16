# -*- coding: utf8 -*-
"""
工具类
Created on 03/01/2016
@author: Wen Gu
@contact: emptyset110@gmail.com
"""
from __future__ import print_function
try:
    import dHydra.config.const as C
except:
    from config import const as C
import requests

def _code_to_symbol(code):
    """
        生成symbol代码标志
        @author: Jimmy Liu
		@group : waditu
		@contact: jimmysoa@sina.cn
    """
    if code in C.INDEX_LABELS:
        return C.INDEX_LIST[code]
    else:
        if len(code) != 6 :
            return ''
        else:
            return 'sh%s'%code if code[:1] in ['5', '6', '9'] else 'sz%s'%code

def symbol_list_to_code(symbolList):
    codeList = []
    for symbol in symbolList:
        codeList.append(symbol[2:8])
    return codeList

def _get_public_ip():
	return requests.get('http://ipinfo.io/ip').text.strip()
