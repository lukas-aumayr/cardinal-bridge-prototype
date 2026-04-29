# commit_burn_tx.py
# C commits to burning wBTC by sending it to commit_burn_address.
# Operators observe this and send their ephemeral keys to C off-chain.

from pycardano import *
from config import (
    context, NETWORK, MIN_ADA,
    sk_B, pk_B, sk_C, pk_C,
    INSTANCE_ID,
)
from scripts import (
    commit_burn_script, commit_burn_address,
    wbtc_policy_hash,
)
from utils import make_commit_burn_datum, wbtc_value
import os


def find_wbtc_utxo(address: Address) -> UTxO:
    for u in context.utxos(str(address)):
        if u.output.amount.multi_asset:
            for policy in u.output.amount.multi_asset:
                if bytes(policy) == bytes(wbtc_policy_hash):
                    return u
    raise ValueError(f"No wBTC UTxO at {address}")


def find_ada_utxo(address: Address) -> UTxO:
    for u in context.utxos(str(address)):
        if not u.output.amount.multi_asset:
            return u
    raise ValueError(f"No ADA UTxO at {address}")


def build_commit_burn_tx(
    wbtc_utxo: UTxO,
    fee_utxo: UTxO,
    ek_C: bytes,
    instance_id: bytes = INSTANCE_ID,
) -> Transaction:
    """
    Move wBTC from B's wallet to commit_burn_address.
    Input is a plain wallet UTxO so no script witness needed on input side.
    Output goes to commit_burn_address (PlutusV3 script address) with datum.
    """
    datum = make_commit_burn_datum(
        pk_C=pk_C,
        instance_id=instance_id,
        ek_C=ek_C,
    )
    token_value = wbtc_value(lovelace=MIN_ADA, amount=1)
    b_address = Address(payment_part=pk_B, network=NETWORK)

    builder = TransactionBuilder(context)

    # Both inputs are plain wallet UTxOs — no script witness needed
    builder.add_input(wbtc_utxo)
    builder.add_input(fee_utxo)

    # Output to commit_burn script address with inline datum
    builder.add_output(TransactionOutput(
        address=commit_burn_address,
        amount=token_value,
        datum=datum,
    ))

    tx = builder.build_and_sign(
        signing_keys=[sk_B],
        change_address=b_address,
    )
    return tx


def simulate_operator_key_exchange(operator_pkhs: list) -> dict:
    ephemeral_keys = {}
    for pkh in operator_pkhs:
        ek_i = os.urandom(32)
        ephemeral_keys[bytes(pkh).hex()] = ek_i
        print(f"Operator {bytes(pkh).hex()[:8]}... sent ephemeral key: {ek_i.hex()[:16]}...")
    return ephemeral_keys


def collect_g_id(ephemeral_keys: dict, operator_pkhs: list) -> list:
    g_id = [pkh for pkh in operator_pkhs if bytes(pkh).hex() in ephemeral_keys]
    print(f"g_id: {[bytes(p).hex()[:8] for p in g_id]}")
    return g_id


def submit_commit_burn_tx(ek_C: bytes) -> str:
    b_address = Address(payment_part=pk_B, network=NETWORK)
    wbtc_utxo = find_wbtc_utxo(b_address)
    fee_utxo = find_ada_utxo(b_address)
    print(f"Found wBTC UTxO: {wbtc_utxo.input.transaction_id}#{wbtc_utxo.input.index}")
    print(f"Found fee UTxO:  {fee_utxo.input.transaction_id}#{fee_utxo.input.index}")

    tx = build_commit_burn_tx(wbtc_utxo, fee_utxo, ek_C)
    context.submit_tx(tx)
    txid = str(tx.id)
    print(f"CommitBurnTx submitted: {txid}")
    return txid


if __name__ == "__main__":
    from config import pk_ops
    import json

    ek_C = os.urandom(32)
    print(f"C's encryption key (ek_C): {ek_C.hex()}")

    txid = submit_commit_burn_tx(ek_C)

    ephemeral_keys = simulate_operator_key_exchange(pk_ops)
    g_id = collect_g_id(ephemeral_keys, pk_ops)

    with open("g_id.json", "w") as f:
        json.dump([bytes(p).hex() for p in g_id], f)
    print(f"g_id saved to g_id.json")