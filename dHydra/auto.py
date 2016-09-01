# -*- coding: utf-8 -*-
import sys
import os
import click

@click.command()
@click.argument('worker_name', nargs = 1)
def new_worker(worker_name = None):
	dir_worker = "Worker/" + worker_name
	if os.path.exists(dir_worker):
		print("[创建失败]：目录 "+dir_worker+"已经存在")
	else:
		os.makedirs( dir_worker )
		# 创建actionNameAction.py
		f = open( dir_worker + '/' + worker_name + '.py', 'w', encoding= 'UTF-8' )
		f.write("""# -*- coding: utf-8 -*-
from dHydra.core.Worker import Worker

class %s(Worker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # You ae not supposed to change THIS

        # The following is customized:
        # In this case, the worker is listening to itself.
        self.__listener__.subscribe( [ self.redis_key + "Pub" ] )

    def __data_handler__(self, msg):
        \"\"\"
        As a Consumer, This Worker(Demo) receives(listens) messages, uses __data_handler__
        to deal with these msg

        The self.__listener__ is running in a daemon thread
        You can override this method to deal with the msg
        \"\"\"
        print(msg)

    def __producer__(self):
        \"\"\"
        As a Producer, This Worker ( Demo ) publishes one number per second to
        the redis channel of: "dHydra.Worker.Demo.DemoDefault.Pub"

        The name of the channel, by convention, is formatted as follows:
        "dHydra.Worker.<worker_name>.<nickname>.Pub"
        where <worker_name> is the name of the class -- "Demo" in this case,
        <nickname> is the customized (unique) name, which can be configured when
        the worker is initialized.

        "self.publish" is the method for publishing data to the channel.
        \"\"\"
        import time
        i = 0
        while True:
            self.publish( i )
            i += 1
            time.sleep(1)

    def __before_termination__(self, sig):
        \"\"\"
        It will be called when a TERM signal is received, right before sys.exit(0)
        \"\"\"
        print("Ahhhh! I'm going to be killed. My pid:{}, signal received:{}".format(self.pid, sig ) )
""" % ( worker_name )
		)
		f.close()
		# 创建config,connection,const, __init__.py
		f = open( dir_worker + '/__init__.py', 'w', encoding= 'UTF-8' )
		f.close()



def init( demo = True ):
	os.makedirs( "data" , exist_ok=True )
	os.makedirs( "Worker" , exist_ok=True )
	print("目录结构已经生成")
	f = open('config.json', 'w', encoding="UTF-8")
	f.write(
		"""{

}""")
	f.close()
	print("试试输入:hail dHydra")
