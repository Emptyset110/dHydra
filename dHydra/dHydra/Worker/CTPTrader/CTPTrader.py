# -*- coding: utf-8 -*-
from dHydra.core.Worker import Worker


class CTPTrader(Worker):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # You ae not supposed to change THIS

        # The following is customized:
        # In this case, the worker is listening to itself.
        self.__listener__.subscribe([self.redis_key + "Pub"])
        trader = get_vendor("CTPTraderApi")

    def __data_handler__(self, msg):
        print(msg)

    def __producer__(self):
        pass

    def __before_termination__(self, sig):
        """
        It will be called when a TERM signal is received, right before
        sys.exit(0)
        """
        print(
            "Ahhhh! I'm going to be killed. My pid:{}, signal received:{}"
            .format(self.pid, sig)
        )
