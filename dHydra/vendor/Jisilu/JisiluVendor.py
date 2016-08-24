# -*- coding: utf-8 -*-
"""
# Created on
# @author:
# @contact:
"""
# 以下是自动生成的 #
# --- 导入系统配置
import dHydra.core.util as util
from dHydra.core.Vendor import Vendor
from dHydra.config import connection as CON
from dHydra.config import const as C
from dHydra.core.Globals import *
# --- 导入自定义配置
from .connection import *
from .const import *
from .config import *
# 以上是自动生成的 #
import requests
import getpass
from pandas import DataFrame
import copy

class JisiluVendor(Vendor):
	def __init__(self, username = None, pwd = None):
		super().__init__()
		self.session = requests.Session()
		if (username is None):
			if "jisiluUsername" in config.keys():
				self.username = config["jisiluUsername"]
			else:
				self.username = input('请输入集思路登录帐号：')
		else:
			self.username = username
		if (pwd is None):
			if "jisiluPassword" in config.keys():
				self.pwd = config["jisiluPassword"]
			else:
				self.pwd = getpass.getpass("输入登录密码（密码不会显示在屏幕上，输入后按回车确定）:")
		else:
			self.pwd = pwd
		self.is_login = False

	def login(self, username = None, pwd = None):
		if username is not None:
			self.username = username
		if pwd is not None:
			self.pwd = pwd
		try:
			self.session.get("https://www.jisilu.cn/login/")
			self.loginResponse = self.session.post(
				URL_LOGIN
			,	data = DATA_LOGIN( username = self.username, pwd = self.pwd )
			,	headers = HEADERS_LOGIN
			,	verify = True
			).json()
			if self.loginResponse["err"] is None:
				self.logger.info("登录集思路成功")
				return True
			else:
				self.logger.error( self.loginResponse["err"] )
				return False
		except Exception as e:
			self.logger.error( "{}".format(e) )

	def fundarb(self, dataframe = True):
		if not self.is_login:
			self.is_login = self.login()
		while True:
			try:
				fundarb = self.session.post(
					URL_FUNDAB
				,	data = DATA_FUNDAB
				,	headers = HEADERS
				)
				break
			except Exception as e:
				self.logger.warning( e )
		ab = fundarb.json()
		if not dataframe:
			return fundarb.json()
		else:
			result = list()
			for item in ab["rows"]:
				result.append(item["cell"])
			df = DataFrame.from_records( result )
			return df

	def get_future_quotation(self, future_type = ["IF","IC"],):
		try:
			quotation_dict = dict()
			for f in future_type:
				res = self.session.get( URL_FUTURE(f), headers = HEADERS )
				if res.status_code == 200:
					quotation = res.json()
					if "rows" in quotation:
						for item in quotation["rows"]:
							if "id" in item:
								quotation_dict[item["id"]] = copy.deepcopy( item["cell"] )
				else:
					return False
			return quotation_dict
		except Exception as e:
			self.logger.warning(e)
