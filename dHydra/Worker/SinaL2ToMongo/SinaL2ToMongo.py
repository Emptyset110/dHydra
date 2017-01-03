# -*- coding: utf-8 -*-
from dHydra.core.Worker import Worker
import pickle

class SinaL2ToMongo(Worker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # You ae not supposed to change THIS

    def __data_handler__(self, msg):
        if msg["type"] == 'pmessage' or msg["type"] == "message":
            try:
                data = pickle.loads(msg["data"])
                result = self.mongo.dHydra.SinaL2.insert_many(
                    data,
                    ordered=False
                )
            except Exception:
                pass

    def ensure_index(self):
        self.mongo.dHydra.SinaL2.create_index(
            [
                ("symbol", 1),
                ("data_type", 1),
                ("time", 1),
                ("index", 1)
            ],
            unique=True,
            drop_dups=True,
            name="basic_index"
        )

    def on_start(self):
        self.ensure_index()
        self.subscribe(worker_name="SinaL2", nickname="SinaL2")

    def __producer__(self):
        pass

    def __before_termination__(self, sig):
        """
        It will be called when a TERM signal is received, right before
        sys.exit(0)
        """
        print("Ahhhh! I'm going to be killed. My pid:{}, signal received:{}"
              .format(self.pid, sig ) )
