# config.py
# All keys, addresses, policy IDs, and protocol parameters for the bridge.
# In a real deployment, load keys from files or env vars — never hardcode secrets.

from pycardano import *
from dotenv import load_dotenv
import os

load_dotenv()

# -------------------------
# Network
# -------------------------
NETWORK = Network.TESTNET
BLOCKFROST_PROJECT_ID = os.environ.get("BLOCKFROST_PROJECT_ID", "preprodXXXXXXXXXXXXXXXX")
context = BlockFrostChainContext(BLOCKFROST_PROJECT_ID, NETWORK)

# -------------------------
# Keys — load from disk for the prototype
# In production: HSM or similar
# -------------------------
def load_signing_key(path: str) -> PaymentSigningKey:
    return PaymentSigningKey.load(path)

def load_verification_key(path: str) -> PaymentVerificationKey:
    return PaymentVerificationKey.load(path)

# User A (peg-in initiator on Bitcoin, recipient on Cardano)
sk_A = load_signing_key("keys/A.skey")
vk_A = load_verification_key("keys/A.vkey")
pk_A = vk_A.hash()  # VerificationKeyHash, used in scripts

# User B = A in this prototype (recipient of wBTC on Cardano)
sk_B = sk_A
vk_B = vk_A
pk_B = pk_A

# User C (peg-out initiator on Cardano)
sk_C = load_signing_key("keys/C.skey")
vk_C = load_verification_key("keys/C.vkey")
pk_C = vk_C.hash()

# Operators (O) — n keys, we use 2 for the prototype
sk_ops = [load_signing_key(f"keys/op{i}.skey") for i in range(2)]
vk_ops = [load_verification_key(f"keys/op{i}.vkey") for i in range(2)]
pk_ops = [vk.hash() for vk in vk_ops]  # List[VerificationKeyHash]
N_OPS = len(pk_ops)

# -------------------------
# Timelocks (slot numbers on Preprod, ~1 slot/sec)
# -------------------------
T_LOCK_TX   = 1_000   # slots after which A can abort on Bitcoin
T_RELEASE_TX = 2_000  # slots after which operators can abort on Cardano

# -------------------------
# Hash lock (set per bridge instance)
# In a real instance: A picks secret s, computes h = sha256(s)
# -------------------------
import hashlib

def make_hash_lock(secret: bytes) -> bytes:
    return hashlib.sha256(secret).digest()

# Example values for the prototype (replace per run)
SECRET_S    = b"super_secret_preimage_32bytes!!!"  # 32 bytes
HASH_H      = make_hash_lock(SECRET_S)

# -------------------------
# Bitcoin LockTx txid (known at setup time, hardcoded into ReleaseTx datum)
# Replace with actual txid after constructing Bitcoin side
# -------------------------
LOCK_TX_ID  = bytes.fromhex("abcd" * 16)  # placeholder: 32 bytes

# -------------------------
# Instance identifier (unique per peg-in/peg-out pair)
# -------------------------
INSTANCE_ID = bytes.fromhex("deadbeef" * 8)  # 32 bytes, pick randomly per instance

# wBTC token — policy ID derived from compiled script (set after scripts.py loads)
# Imported after scripts to avoid circular import
WBTC_ASSET_NAME = AssetName(b"wBTC")

# -------------------------
# Min ADA for UTxOs carrying tokens (protocol parameter, ~2 ADA on Preprod)
# -------------------------
MIN_ADA = 2_000_000  # lovelace