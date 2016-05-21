# -*- coding: utf-8 -*-

import logging
from dHydra.core.Functions import *

class Vendor:
	def __init__(self, logLevel = logging.INFO):
		self.logger = self.get_logger()
		pass

	def get_logger(self):
		logger = logging.getLogger(self.__class__.__name__)
		return logger