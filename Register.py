import pyhardware
import hashlib
from pyhardware.disk import Disk
from pyhardware.motherboard import Motherboard
from Client import tcp_client

user_msg=''

node_list=[]

# 以该用户的硬盘序列和主板序列以及用户自定义的数据作为用户指纹

def get_hardware_ids():
    disks = Disk.get_disks()
    for disk in disks:
        if disk.serial_number:
            user_msg += str(disk.serial_number)
            break
    motherboard = Motherboard.get_info()
    if motherboard.serial_number:
        user_msg += str(motherboard.serial_number)

# 求出用户哈希
# 这个哈希非常重要
# 它就像用户的“身份证号码”
# 此后所有的交易信息都必须携带它
def calc_hash():
    return hashlib.sha256(user_msg.encode()).hexdigest()

# 将本地机器作为节点注册到区块链网络中
# 现实生产中，addr肯定是该机器的公网IP地址
# 如果是在一个局域网下的设备上做实验，那就用局域网IP
def register_node(addr,port):
    for node in node_list:
        tcp_client(node[0],node[1],f"ADD_NODE:{addr}:{port}")

# 将账户注册到区块链网络中
def register_new_account(account_hash,public_key):
    for node in node_list:
        tcp_client(node[0],node[1],f"ADD_ACCOUNT:{account_hash}:{public_key}")