import socket
import sys
import random
import time
from collections import Counter

#通过main.py设置该变量的值
node_list=[]

# 与其他节点进行通信
# 指挥其他节点进行操作
# 并回显操作结果
def tcp_client(addr,port,msg):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(10)
    response='\0'
    try:
        client_socket.connect((addr,int(port)))
        client_socket.send(msg.encode('utf-8'))
        response = ['ok',client_socket.recv(1024).decode('utf-8')]
    except Exception as e:
        response = ['err',e]
    finally:
        client_socket.close()
        return response