import json
from pycardano import *

# -------------------------
# Load compiled scripts from Aiken's plutus.json
# -------------------------
with open("bridge-validators/plutus.json") as f:
    _blueprint = json.load(f)

def _get_script(title: str) -> PlutusV3Script:
    for v in _blueprint["validators"]:
        if v["title"] == title:
            return PlutusV3Script(bytes.fromhex(v["compiledCode"]))
    raise ValueError(f"Validator '{title}' not found in plutus.json")

wbtc_policy_script  = _get_script("bridge.wbtc_policy.mint")
release_tx_script   = _get_script("bridge.release_tx.spend")
commit_burn_script  = _get_script("bridge.commit_burn.spend")
burn_tx_script      = _get_script("bridge.burn_tx.spend")

# -------------------------
# Script hashes
# -------------------------
wbtc_policy_hash   = plutus_script_hash(wbtc_policy_script)
release_tx_hash    = plutus_script_hash(release_tx_script)
commit_burn_hash   = plutus_script_hash(commit_burn_script)
burn_tx_hash       = plutus_script_hash(burn_tx_script)

# -------------------------
# Script addresses (Preprod testnet)
# -------------------------
def script_address(script_hash: ScriptHash, network: Network = Network.TESTNET) -> Address:
    return Address(payment_part=script_hash, network=network)

release_tx_address  = script_address(release_tx_hash)
commit_burn_address = script_address(commit_burn_hash)
burn_tx_address     = script_address(burn_tx_hash)

# Unspendable address for permanent datum storage (g_id receipt)
# Using burn_tx_hash as a permanent store — in production use a dedicated always-fails script
unspendable_address = script_address(burn_tx_hash)

# -------------------------
# No more always_succeeds_native stub
# -------------------------
always_succeeds_native = None  # not used with real validators