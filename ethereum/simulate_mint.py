# ethereum/simulate_mint.py
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
import os

# -------------------------
# Config
# -------------------------
PRIVATE_KEY     = os.environ["PRIVATE_KEY"]
CONTRACT_ADDR   = os.environ["CONTRACT_ADDR"]
RPC_URL         = os.environ["SEPOLIA_RPC_URL"]

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = Account.from_key(PRIVATE_KEY)

recipient    = account.address      # A=B=C in prototype
instance_id  = bytes.fromhex("deadbeef" * 8)   # must match INSTANCE_ID in config.py
lock_tx_id   = bytes.fromhex("abcd" * 16)       # must match LOCK_TX_ID in config.py

# -------------------------
# Construct operator signature
# matches: keccak256(abi.encodePacked(recipient, instanceId, lockTxId))
# -------------------------
msg_hash = Web3.solidity_keccak(
    ["address", "bytes32", "bytes32"],
    [recipient, instance_id, lock_tx_id]
)
signed = account.sign_message(encode_defunct(msg_hash))
signature = signed.signature

print(f"Recipient:   {recipient}")
print(f"Instance ID: 0x{instance_id.hex()}")
print(f"LockTx ID:   0x{lock_tx_id.hex()}")
print(f"Signature:   {signature.hex()}")

# -------------------------
# Simulate via cast call (read-only, no gas)
# -------------------------
print("\nTo simulate with cast:")
print(f"""cast call {CONTRACT_ADDR} \\
  "mint(address,bytes32,bytes32,bytes)" \\
  {recipient} \\
  0x{instance_id.hex()} \\
  0x{lock_tx_id.hex()} \\
  {signature.hex()} \\
  --rpc-url $SEPOLIA_RPC_URL""")