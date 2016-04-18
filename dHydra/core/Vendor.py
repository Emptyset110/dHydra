# -*- coding: utf8 -*-
from dHydra.core.Functions import *

class Vendor:
	def __init__(self, logLevel = logging.INFO):
		self.logger = self.get_logger()

	def get_logger(self):
		logger = get_logger(self.__class__.__name__)
		return logger