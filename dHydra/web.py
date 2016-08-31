# -*- coding: utf-8 -*-
"""
# Created on
# @author:
# @contact:
"""
import tornado.ioloop
import tornado.web
import os
from dHydra.console import *

# 首页根目录
class IndexHandler(tornado.web.RequestHandler):
	def prepare(self):
		"""
		单入口做URI路由转发，交给对应Handler处理
		"""
		request = self.request
		application = self.application
		# kwargs = self.kwargs
		uri = self.request.uri

	def get(self, *args ):
		self.render( "index.html" )
		print(args)

	def get_template_path(self):
		"""
		重写get_template_path
		"""
		return os.path.split(os.path.realpath(__file__))[0] + "/templates"

class WorkerHandler(tornado.web.RequestHandler):
	def get(self, worker_name, method_name):
		if method_name == "":
			method_name = "index"
		print("Worker Name: {}, method_name: {}".format(worker_name, method_name))
		try:
			self.render(method_name+".html")
		except Exception as e:
			self.write( "Cannot render: "+self.get_template_path() + "/" + method_name+".html" )

	def prepare(self):
		print("This is WorkerHandler")

	def get_template_path(self):
		"""
		重写get_template_path
		"""
		if self.path_args[1] == "":
			self.path_args[1] = "index"
		if os.path.exists( os.getcwd()+"/Worker/" + self.path_args[0] + "/templates/"+self.path_args[1]+".html" ):
			return os.getcwd()+"/Worker/" + self.path_args[0] + "/templates"
		else:
			return os.path.split(os.path.realpath(__file__))[0] + "/Worker/"+self.path_args[0]+"/templates"

class ApiHandler(tornado.web.RequestHandler):
	def get(self, class_name, method):
		controller = {"class_name": class_name, "method": method}
		func = get_controller_method( class_name, method )
		result = func(self.get_query_arguments)
		self.write( result )

def make_app():
	"""
	/<addon_type>/<addon_name>/<addon_controller>/<method>
	------
		e.g.:
		"/action/print_sina_l2/main_controller/index"
	"""
	return tornado.web.Application([
		# (r"/favicon.ico", tornado.web.StaticFileHandler, { "path": os.getcwd() + "/static/" } ),
		(r"/", IndexHandler),
		(r"/public/js/(.*)", tornado.web.StaticFileHandler,  { "path": os.getcwd() + "/public/js/" } ),
		(r"/public/css/(.*)", tornado.web.StaticFileHandler,  { "path": os.getcwd() + "/public/css/" } ),
		(r"/public/fonts/(.*)", tornado.web.StaticFileHandler,  { "path": os.path.split(os.path.realpath(__file__))[0] + "/public/fonts/" } ),
		(r"/static/js/(.*)", tornado.web.StaticFileHandler,  { "path": os.path.split(os.path.realpath(__file__))[0] + "/static/js/" } ),
		(r"/static/css/(.*)", tornado.web.StaticFileHandler,  { "path": os.path.split(os.path.realpath(__file__))[0] + "/static/css/" } ),
		(r"/static/fonts/(.*)", tornado.web.StaticFileHandler,  { "path": os.path.split(os.path.realpath(__file__))[0] + "/static/fonts/" } ),
		(r"/api/Worker/(.*)/(.*)/", ApiHandler),	# ClassName, MethodName
		(r"/Worker/(.*)/(.*)", WorkerHandler)		# ClassName, TemplateName
    	]
		, debug = True
		)

def start_server(port = 5000):
	app = make_app()
	app.listen(port)
	print("Listening on port: 127.0.0.1:5000")
	tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
	app = make_app()
	app.listen(5000)
	tornado.ioloop.IOLoop.current().start()
