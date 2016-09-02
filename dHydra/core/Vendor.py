# -*- coding: utf-8 -*-
import logging


class Vendor:

    def __init__(self, logLevel=logging.INFO):
        self.logger = self.get_logger()

    def get_logger(self):
        logger = logging.getLogger(self.__class__.__name__)
        return logger
