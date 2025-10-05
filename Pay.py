from cryptography.fernet import Fernet
from Client import tcp_client
from random import randint
from time import time
from DataLoad import rewrite_account_list
from CCBEncrypt import load_private_key,sign

#通过main.py设置该变量的值
node_list=[]

# 支付、转账操作
# 向所有节点发布交易申请
# 基于各节点的回应判断是否拥有交易资格
# 无论通过与否，在验证完交易资格后仍会通知各节点共享投票结果
# 因为各节点此时并不知晓是否应该修改账本
# 并且为了防止申请者伪造投票结果欺骗各节点
# 各节点点对点交换结果是必要的
def pay_to(account1,account2,key,amount,nonce):
	private_key=load_private_key(key.encode())
	text=f"{account1}|{account2}|{amount}|{time()}|{nonce}"
	signiture=sign(private_key,text)
	success_nodes=0
	for node in node_list:
		recv=tcp_client(node[0],node[1],f"EXM_TRAN:{account1}:{signiture}:{text}")
		if recv[0] == 'ok' and recv[1] == 'ok':
			success_nodes += 1
	if success_nodes >= len(node_list) * 2 // 3:
		print("交易资格验证通过")
	else:
		print("交易资格验证不通过")
	for node in node_list:
		recv=tcp_client(node[0],node[1],f"VOTE_REQUEST:{text}")