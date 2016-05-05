# -*- coding: utf8 -*-
"""
# Created on 
# @author: 
# @contact: 
"""
import tornado.ioloop
import tornado.web
from dHydra.core.Globals import *

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write( "{}".format( json.dumps(actionDict,indent=2) ) )

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()