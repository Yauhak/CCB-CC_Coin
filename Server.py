import socket
import random
import CCBEncrypt
from time import time
from collections import Counter
from Client import tcp_client
from DataLoad import rewrite_account_list,rewrite_transaction,read_transaction_payer,add_node

#线程锁（保护公有变量栈）
import threading
account_lock = threading.Lock() 
transaction_lock = threading.Lock() 
command_lock = threading.Lock() 

import logging #输出错误日志
logging.basicConfig(filename='blockchain.log', level=logging.ERROR)

account_list={}#用户信息栈
node_list=[]#节点列表
cmd_list=[]#命令池
lc_transaction_pass={}#交易池
tran_vote_ratio={}#投票池

# 校验交易是否合理
# account_hash 交易发起方的哈希
# signiture 发起方加密后的签名
# data 原始签名
def exm_tran_valid(account_hash, signiture, data):
    # 使用锁保护对全局变量的访问
    with account_lock:
        if account_hash not in account_list:
            return 'reject-account-not-found' # 本地没有存储该账号的信息
        public_key = CCBEncrypt.load_public_key(account_list[account_hash][1].encode('utf-8'))
    if not CCBEncrypt.verify(data, signiture, public_key): # 利用发起方留在节点的公钥验证证书是否成立
        return 'reject-sign-no-pass'
    pay_msg = data.split('|')
    # 签名内容 转账方(哈希)|接受方(哈希)|金额|时间戳(UNIX)|订单号
    # 再次获取锁进行余额检查
    with account_lock:
        account_balance = float(account_list[account_hash][0])
        account_nonce = int(account_list[account_hash][2])
    if float(pay_msg[2]) > account_balance:
        return 'rejected-insufficient-balance'
    if int(pay_msg[4]) <= account_nonce:
        return 'reject-bad-nonce'
    t = time()
    if t <= float(pay_msg[3]) or t - float(pay_msg[3]) >= 600:
        return 'reject-time-out'
    # 保护交易状态字典
    # 将原始签名作为交易的指纹
    with transaction_lock:
        lc_transaction_pass[data] = True
        tran_vote_ratio[data] = 0
    return 'ok'

def lc_strategy(sign):
    with account_lock,transaction_lock:
        msg=f"{account_list[sign.split('|')[0]][0]}:{account_list[sign.split('|')[1]][0]}"
        return f"1:{msg}" if lc_transaction_pass.get(sign, True) else f"0:{msg}"
        # 对于其他节点共享投票结果的请求
        # 返回本地节点的投票结果

def get_sorted_elements(arr):
    #只返回按重复次数排序的元素列表
    counter = Counter(arr)
    # 按出现次数排序，只返回元素
    sorted_elements = [item for item, count in counter.most_common()]
    return sorted_elements

def vote_transaction(sign):
    # 交易状态锁
    with transaction_lock:
        if sign not in lc_transaction_pass:
            return 'transaction-not-found'
    req_balance1=[]
    req_balance2=[]
    current_votes = tran_vote_ratio.get(sign, 0)
    # 向所有节点发起共享投票结果的请求
    for node in node_list:
        recv = tcp_client(node[0], node[1], f"VOTE_TRAN:{sign}")
        if recv[0] == 'ok' and recv[1].split('|')[0] == '1':
            current_votes += 1
            req_balance1.append(float(recv[1].split('|')[1]))
            req_balance2.append(float(recv[1].split('|')[2]))
    # 最终更新时需要同时保护账户和交易状态
    with account_lock, transaction_lock:  # 同时获取两个锁
        # 如果投票支持率超过2/3，则更改存储于本地的账本信息，无论自己是否支持，少数服从多数
        # 投票同时各节点共享交易方和接受方的余额数据
        # 以余额数据的众数作为真实余额
        if current_votes / len(node_list) >= 2/3:
            pay_msg = sign.split('|')
            account_hash = pay_msg[0]
            common_balance1=get_sorted_elements(req_balance1)[0]
            common_balance2=get_sorted_elements(req_balance2)[0]
            # 更新账户信息
            account_list[account_hash][2] = pay_msg[4]  # 更新nonce（最近的历史订单号）
            account_list[account_hash][0] = common_balance1 - float(pay_msg[2])
            account_list[pay_msg[1]][0] = common_balance2 + float(pay_msg[2])
            # 修改本地文件
            rewrite_account_list(account_list)
            rewrite_transaction(account_hash, pay_msg[1], pay_msg[2], pay_msg[3], pay_msg[4])
            result = 'vote-success'
        else:
            result = 'vote-failed'
        # 清理交易状态
        if sign in lc_transaction_pass:
            lc_transaction_pass.pop(sign)
        if sign in tran_vote_ratio:
            tran_vote_ratio.pop(sign)
    return result

def test_the_num(account_hash,mine_number,signiture,data):
    with account_lock:
        if account_hash not in account_list:
            return 'reject-account-not-found' # 本地没有存储该账号的信息
        public_key = CCBEncrypt.load_public_key(account_list[account_hash][1].encode('utf-8'))
    if not CCBEncrypt.verify(data, signiture, public_key): # 利用发起方留在节点的公钥验证证书是否成立
        return 'reject-sign-no-pass'
    # 验证时间戳是否合理
    if float(time())<float(data.split('|')[-1]) or float(time())-float(data.split('|')[-1])>600:
        return 'reject-time-out'
    payer_history=read_transaction_payer()
    if mine_number in payer_history:
        return 'reject-this-mine-has-been-manual'
    if hash(float(mine_number))<=2e12:
        account_list[account_hash][2] = int(account_list[account_hash][2])+1  # 更新nonce（最近的历史订单号）
        account_list[account_hash][0] = float(account_list[account_hash][0]) +1
        rewrite_account_list(account_list)
        rewrite_transaction(mine_number, account_hash, 1, time(), account_list[account_hash][2])
        # 如果是挖矿成功而获得一枚CC币
        # 那么视为哈希为mine_number的账号（即矿源这个本体）支付给该账号的奖励
        # 因为真实存在的哈希值不可能出现小数
        # 并且mine_number也很难再次复现，基本可视为一次性的
        # 所以交易记录本用mine_number作为哈希不仅可以表示出这枚CC币的来源（挖矿）
        # 还可以防止利用重复的mine_number刷钱
        return "pass"
    return "reject-bad-mine-num"

def add_account(account_hash,public_key):
    #防止重复注册，覆盖原有账号
    if account_hash in account_list:
        return 'reject-account-exist'
    account_list.update({account_hash,[0,public_key,0]})
    rewrite_account_list(account_list)

# 根据接受的不同命令实现相应操作
def command(cmd):
    # 使用命令锁保护cmd_list
    with command_lock:
        cmd_list.append(cmd)
        if cmd_list:
            current_cmd = cmd_list[0]
            cmd_list.pop(0)
        else:
            return "NO_COMMAND"
    params=current_cmd.split(':')
    match params[0]:
        case "EXM_TRAN":
            return exm_tran_valid(params[1], params[2], params[3])
        case "VOTE_REQUEST":
            return vote_transaction(params[1])
        case "VOTE_TRAN":
            return lc_strategy(params[1])
        case "EXM_MINE":
            return test_the_num(params[1],params[2],params[3],params[4])
        case "ADD_NODE":
            node_list.append([params[1],params[2]])
            return add_node(params[1],params[2])
        case "ADD_ACCOUNT":
            return add_account(params[1],params[2])
        case _:
            return "NO_SUCH_COMMAND"

# 服务端程序
# 循环接受其他节点的指令并做出相应操作
def tcp_server(addr,port):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((addr,int(port)))
        server_socket.listen(5)
        while True:
            client_socket, client_address = server_socket.accept()
            try:
                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    message = data.decode('utf-8')
                    cmd_list.append(message)
                    response = command(cmd_list[0])
                    cmd_list.pop(0)
                    client_socket.send(response.encode('utf-8'))        
            except Exception as e:
                logging.error(f"Server error at {time()}: {e}")
                client_socket.close()
                return
    finally:
        client_socket.close()
