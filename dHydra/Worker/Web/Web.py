# -*- coding: utf-8 -*-
from dHydra.core.Worker import Worker
import dHydra.web

class Web(Worker):
    def __init__(self, port=5000, **kwargs):
        super().__init__(**kwargs)  # You ae not supposed to change THIS
        self.port = port
        # The following is customized:
        # In this case, the worker is listening to itself.
        # self.__listener__.subscribe( [ self.redis_key + "Pub" ] )

    def on_start(self):
        import threading
        thread_tornado = threading.Thread(
            target=dHydra.web.start_server,
            args=(self.port,)
        )
        thread_tornado.setDaemon(True)
        thread_tornado.start()
        self.logger.info("Tornado webserver has started")

    def __data_handler__(self, msg):
        """
        As a Consumer, This Worker(Demo) receives(listens) messages,
        uses __data_handler__ to deal with these msg

        The self.__listener__ is running in a daemon thread
        You can override this method to deal with the msg
        """
        # print(msg)

    def __producer__(self):
        """
        As a Producer, This Worker ( Demo ) publishes one number per second to
        the redis channel of: "dHydra.Worker.Demo.DemoDefault.Pub"

        The name of the channel, by convention, is formatted as follows:
        "dHydra.Worker.<worker_name>.<nickname>.Pub"
        where <worker_name> is the name of the class -- "Demo" in this case,
        <nickname> is the customized (unique) name, which can be configured
        when the worker is initialized.

        "self.publish" is the method for publishing data to the channel.
        """
        # import time
        # i = 0
        # while True:
        #     self.publish( i )
        #     i += 1
        #     time.sleep(1)

    def __before_termination__(self, sig):
        """
        It will be called when a TERM signal is received, right before
        sys.exit(0)
        """
        print("Web Server is closed. My pid:{}, signal received:{}"
              .format(self.pid, sig ) )
