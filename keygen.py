# keygen.py — run once to generate all keys
from pycardano import *
import os

os.makedirs("keys", exist_ok=True)

def gen_key_pair(name: str):
    sk = PaymentSigningKey.generate()
    vk = PaymentVerificationKey.from_signing_key(sk)
    sk.save(f"keys/{name}.skey")
    vk.save(f"keys/{name}.vkey")
    addr = Address(payment_part=vk.hash(), network=Network.TESTNET)
    print(f"{name}: {addr}")

gen_key_pair("A")
gen_key_pair("C")
gen_key_pair("op0")
gen_key_pair("op1")