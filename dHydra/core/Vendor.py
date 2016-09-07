# -*- coding: utf-8 -*-
import logging
import dHydra.core.util as util


class Vendor:

    def __init__(self, logLevel=logging.INFO):
        self.logger = util.get_logger(logger_name=self.__class__.__name__)
