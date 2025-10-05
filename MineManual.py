from random import random
from time import time
from Client import tcp_client
from CCBEncrypt import load_private_key,sign

node_list=[]

# 挖矿规则：
# 在0至1间取随机小数
# 如果其哈希值小于2*10^12
# 那么视为挖到一次矿
def mine_manual():
	count=0
	t=time()
	while True:
		rand_num=random()
		this_hash = hash(rand_num)
		count=count+1
		print(f"Sequence:{count:<10}Hash:{this_hash:<25}Time:{time()-t:20}(s)")
		if this_hash<=2e12:
			print(f"找到一个符合规定的数字:{rand_num}")
			break

# 向各节点发布挖矿成功广播
# 让各节点评判该矿是否有价值
def req_award(account_hash,key,mine_number):
	private_key=load_private_key(key.encode())
	# 签名
	text=f"{account_hash}|{1}|{time()}"
	signiture=sign(private_key,text)
	for node in node_list:
    	tcp_client(node[0],node[1],f"EXM_MINE:{account_hash}:{mine_number}:{signiture}:{text}")