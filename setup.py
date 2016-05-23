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

PACKAGES = [	"dHydra"
			,	"dHydra.core"
			,	"dHydra.producer"
			,	"dHydra.producer.SinaLevel2WS"
			,	"dHydra.producer.SinaFreeQuote"
			,	"dHydra.vendor"
			,	"dHydra.vendor.Maoyan"
			,	"dHydra.vendor.Xueqiu"
			,	"dHydra.vendor.Sina"
			,	"dHydra.action"
			,	"dHydra.action.SinaTickToMongo"
			,	"dHydra.action.PrintSinaL2"
			,	"dHydra.action.Demo"
			,	"dHydra.action.SinaL2TCP"
			,	"dHydra.config"
			]

DESCRIPTION = "A framework for saving & data mining Chinese Stocks"

LONG_DESCRIPTION = ""
"""
参见read方法说明
"""

KEYWORDS = ("Finance","Chinese Stock","Quant","Framework")
"""
关于当前包的一些关键字，方便PyPI进行分类。
"""

AUTHOR = "Wen Gu"

AUTHOR_EMAIL = "emptyset110@gmail.com"

URL = "http://dHydra.org"

VERSION = "0.10.19"

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
,   install_requires = ["requests","numpy","pandas","pymongo","websockets","rsa","ntplib"]
,   keywords = KEYWORDS
,   author = AUTHOR
,   author_email = AUTHOR_EMAIL
,   url = URL
,   license = LICENSE
,   packages = PACKAGES
,   include_package_data=True
,   zip_safe=True
)
