# -*- coding: utf-8 -*-
"""
# Created on
# @author:
# @contact:
"""
import tornado.ioloop
import tornado.web
import os

class MainHandler(tornado.web.RequestHandler):
	def get(self, name):
		print( "MainHandler Name: {}".format(name) )
		if name == "action":
			self.redirect("/action/")
			return
		elif name == "producer":
			self.redirect("/producer/")
		elif name == "vendor":
			self.redirect("/vendor/")
		else:
			self.redirect("/")

	def prepare(self):
		print("This is MainHandler")

	def get_template_path(self):
		"""
		重写get_template_path
		"""
		return os.path.split(os.path.realpath(__file__))[0] + "/templates"

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
		VendorHandler(application=application,request=request)
		print("This is IndexHandler")

	def get(self, *args ):
		self.render( "index.html" )
		print(args)

	def get_template_path(self):
		"""
		重写get_template_path
		"""
		return os.path.split(os.path.realpath(__file__))[0] + "/templates"

class ActionHandler(tornado.web.RequestHandler):
	def get(self, name):
		print("Action Name: {}".format(name))
		self.render("index.html")

	def prepare(self):
		print("This is ActionHandler")

	def get_template_path(self):
		"""
		重写get_template_path
		"""
		return os.path.split(os.path.realpath(__file__))[0] + "/templates/action"

class ProducerHandler(tornado.web.RequestHandler):
	def get(self, name):
		print( "Producer Name: {}".format(name) )
		self.render("index.html")

	def prepare(self):
		print("This is ProducerHandler")

	def get_template_path(self):
		"""
		重写get_template_path
		"""
		return os.path.split(os.path.realpath(__file__))[0] + "/templates/producer"

class VendorHandler(tornado.web.RequestHandler):
	def get(self, *name):
		print( "Vendor Name: {}".format(name) )
		self.render("index.html")

	def prepare(self):
		print("This is VendorHandler")

	def get_template_path(self):
		"""
		重写get_template_path
		"""
		return os.path.split(os.path.realpath(__file__))[0] + "/templates/vendor"

def make_app():
	"""
	/<addon_type>/<addon_name>/<addon_controller>/<method>
	------
		e.g.:
		"/action/print_sina_l2/main_controller/index"
	"""
	return tornado.web.Application([
		# (r"/favicon.ico", tornado.web.StaticFileHandler ),
		(r"/(.*)", IndexHandler),
		# (r"(?:([a-zA-Z0-9_-]+)/?)+", VendorHandler),
		# (r"([^/]+)(?:/|$)", VendorHandler)
		# (r"/vendor/(?:([a-zA-Z0-9_-]+)\/?)+", VendorHandler),
		# (r"/action/(.*)/$", ActionHandler),
        # (r"/producer/(.*)(?:\/)?$", ProducerHandler),
		# (r"/(.*)/$", MainHandler),
    ])

app = make_app()
app.listen(5000)
tornado.ioloop.IOLoop.current().start()
