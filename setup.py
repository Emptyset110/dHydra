# -*- coding: utf8 -*-
# import dHydra
import codecs
import os
import sys
 
try:
    from setuptools import setup
except:
    from distutils.core import setup
"""
打包的用的setup必须引入，
"""

def read(fname):
    return codecs.open(os.path.join(os.path.dirname(__file__), fname)).read()
 
NAME = "dHydra"
"""
名字，一般放你包的名字即可
"""
 
PACKAGES = ["dHydra","dHydra.config","dHydra.movies"]

DESCRIPTION = "A solution for saving & data mining Chinese Stocks based on TuShare"
 
LONG_DESCRIPTION = ""
"""
参见read方法说明
"""

KEYWORDS = ("Finance","Chinese Stock","Quant")
"""
关于当前包的一些关键字，方便PyPI进行分类。
"""
 
AUTHOR = "Wen Gu"
 
AUTHOR_EMAIL = "emptyset110@gmail.com"
 
URL = "http://dHydra.org"

VERSION = "0.2.14"

LICENSE = "Apache Software License"
 
setup(
    name = NAME
,   version = VERSION
,   description = DESCRIPTION
,   long_description = LONG_DESCRIPTION
,   classifiers = [
        'License :: OSI Approved :: Apache Software License'
    ,   'Programming Language :: Python'
    ,   'Intended Audience :: Financial and Insurance Industry'
    ,   'Operating System :: OS Independent'
    ]
,   install_requires = ["requests","pandas","tushare","pymongo","websockets","rsa"]
,   keywords = KEYWORDS
,   author = AUTHOR
,   author_email = AUTHOR_EMAIL
,   url = URL
,   license = LICENSE
,   packages = PACKAGES
,   include_package_data=True
,   zip_safe=True
)