from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
def generate_keys():
    """生成ECC密钥对"""
    private_key = ec.generate_private_key(
        ec.SECP256R1(),  # 使用P-256曲线
        default_backend()
    )
    public_key = private_key.public_key()
    return private_key,public_key
    
def serialize_public_key(public_key):
    """序列化ECC公钥"""
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

def sign(private_key, data):
    """ECC数字签名"""
    if isinstance(data, str):
        data = data.encode('utf-8')  # 确保数据是bytes
    signature = private_key.sign(
        data,
        ec.ECDSA(hashes.SHA256())
    )
    return signature
    
def verify(data, signature, public_key):
    """验证ECC签名"""
    try:
        public_key.verify(
            signature,
            data.encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )
        return True
    except:
        return False

def private_key_text(private_key):
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8
    )

def public_key_text(public_key):
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
def load_private_key(pem_data):
        return serialization.load_pem_private_key(
            pem_data,
            backend=default_backend()
        )
    
def load_public_key(pem_data):
    return serialization.load_pem_public_key(
        pem_data,
        backend=default_backend()
    )