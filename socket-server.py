# -*- coding: utf8 -*-
import socket
import threading
import time

def tcplink(sock, addr):
    print('Accept new connection from %s:%s...' % addr)
    data = b''
    # sock.send(b'Welcome!')
    while True:
        while True:
            newdata = sock.recv(10240)
            data += newdata
            try:
                print( data.decode("utf-8") )
                data = b''
            except:
                continue
    sock.close()
    print('Connection from %s:%s closed.' % addr)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 监听端口:
s.bind(('127.0.0.1', 9999))

s.listen(5)
print('Waiting for connection...')

while True:
    # 接受一个新连接:
    sock, addr = s.accept()
    # 创建新线程来处理TCP连接:
    t = threading.Thread(target=tcplink, args=(sock, addr))
    t.start()

