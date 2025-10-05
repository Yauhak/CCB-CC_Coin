import hashlib
import portalocker #跨平台文件锁，需要额外下载

node_file_path=''
account_file_path=''
history_file_path=''

# 加载本地储存的节点列表文件
# 每一行的内容格式都为:[节点地址（IP地址）] [该节点开放的端口]
def load_node_list():
    with open(node_file_path,"r") as handle:
        portalocker.lock(handle, portalocker.LOCK_EX)
        lines=handle.read().split('\n')
    msg_tree=[]
    for each_line in lines:
        node_msg=each_line.split(' ')
        node_addr=node_msg[0]
        node_port=node_msg[1]
        msg_tree.append([node_addr,node_port])
    return msg_tree

def add_node(addr,port):
    with open(node_file_path,"a") as handle:
        portalocker.lock(handle, portalocker.LOCK_EX)
        handle.write(f"{addr} {port}\n")

# 加载本地储存的用户信息列表文件
# 每一行的内容格式都为:[用户哈希] [该用户持有的CC币] [该用户的公钥] [该用户已进行多少次交易]
def load_account_list():
    with open(account_file_path,"r") as handle:
        portalocker.lock(handle, portalocker.LOCK_EX)
        lines=handle.read().split('\n')
    msg_tree={}
    for each_line in lines:
        account_msg=each_line.split(' ')
        account_hash=account_msg[0]
        account_CCB=account_msg[1]
        account_publickey=account_msg[2]
        account_nonce=account_msg[3]
        msg_tree.update({account_hash:[account_CCB,account_publickey,account_nonce]})
    return msg_tree

# 该函数请结合Server中test_the_num函数一起理解
def read_transaction_payer():
    with open(history_file_path,"r") as handle:
        portalocker.lock(handle, portalocker.LOCK_EX)
        lines=handle.read().split('\n')
    payer_list=[]
    for each_line in lines:
        pay_msg=each_line.split(' ')
        payer_list.append(pay_msg[0])
    return payer_list

# 更新历史交易链（即更新存储在本地的历史交易文件）
# 本次交易的哈希值的原内容为[转账方] [接受方] [金额] [UNIX时间] [订单号] [上次交易的哈希值]
def rewrite_transaction(account1,account2,amount,time,nonce):
    with open(history_file_path, 'r') as f:
        portalocker.lock(f, portalocker.LOCK_EX)
        lines=f.read().split('\n')
    last_line=lines[len(lines)-1]
    last_hash=(last_line.split(' '))[5]
    this_hash=hashlib.sha256(f"{account1} {account2} {amount} {time} {nonce} {last_hash}\n".encode()).hexdigest()
    with open(history_file_path, 'a') as f:
        portalocker.lock(f, portalocker.LOCK_EX)
        f.write(f"{account1} {account2} {amount} {time} {nonce} {this_hash}\n")

# 更新账户余额信息
# 即改写本地文件
def rewrite_account_list(account_list):
    new_text=""
    for account_hash in account_list:
        new_text += f"{account_hash} {account_list[account_hash][0]} {account_list[account_hash][1]} {account_list[account_hash][2]}\n"
    with open(account_file_path, 'w') as f:
        portalocker.lock(f, portalocker.LOCK_EX)

        f.write(new_text)
