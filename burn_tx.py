# burn_tx.py
# C burns wBTC from commit_burn_address, committing g_id on-chain.

from pycardano import *
from pycardano.hash import VerificationKeyHash
from config import (
    context, NETWORK, MIN_ADA,
    sk_C, pk_C, pk_B,
    INSTANCE_ID,
)
from scripts import (
    wbtc_policy_script, wbtc_policy_hash,
    commit_burn_script, commit_burn_address,
)
from utils import (
    make_burn_receipt_datum, BurnRedeemer, MintRedeemer,
    wbtc_value,
)
import json, cbor2


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


def build_burn_tx(
    commit_burn_utxo: UTxO,
    fee_utxo: UTxO,
    g_id: list,
    instance_id: bytes = INSTANCE_ID,
) -> Transaction:
    """
    Spend commit_burn UTxO, burn wBTC, output g_id datum.
    """
    g_id_bytes = [bytes(pkh) for pkh in g_id]

    spend_rdmr = Redeemer(BurnRedeemer.BurnSpend(
        g_id=g_id_bytes,
        instance_id=instance_id,
    ))

    mint_rdmr = Redeemer(MintRedeemer.Burn(
        g_id=g_id_bytes,
        instance_id=instance_id,
    ))

    receipt_datum = make_burn_receipt_datum(g_id=g_id_bytes, instance_id=instance_id)
    c_address = Address(payment_part=pk_C, network=NETWORK)
    b_address = Address(payment_part=pk_B, network=NETWORK)

    builder = TransactionBuilder(context)

    # Script input: commit_burn UTxO
    builder.add_script_input(
        utxo=commit_burn_utxo,
        script=commit_burn_script,
        redeemer=spend_rdmr,
    )

    # Fee + collateral from C's wallet (or B's since A=B=C)
    builder.add_input(fee_utxo)
    builder.collaterals = [fee_utxo]

    # Burn -1 wBTC
    builder.add_minting_script(
        script=wbtc_policy_script,
        redeemer=mint_rdmr,
    )
    builder.mint = MultiAsset.from_primitive({
        bytes(wbtc_policy_hash): {b"wBTC": -1}
    })

    # Burn receipt output with g_id datum
    # Send to C's address with datum (permanent record)
    builder.add_output(TransactionOutput(
        address=c_address,
        amount=Value(MIN_ADA),
        datum=receipt_datum,
    ))

    builder.required_signers = [pk_C]

    tx = builder.build_and_sign(
        signing_keys=[sk_C],
        change_address=c_address,
    )
    return tx


def submit_burn_tx(g_id: list) -> tuple:
    wbtc_utxo = find_wbtc_utxo(commit_burn_address)
    fee_utxo = find_ada_utxo(Address(payment_part=pk_C, network=NETWORK))
    print(f"Found wBTC UTxO: {wbtc_utxo.input.transaction_id}#{wbtc_utxo.input.index}")
    print(f"Found fee UTxO:  {fee_utxo.input.transaction_id}#{fee_utxo.input.index}")

    tx = build_burn_tx(wbtc_utxo, fee_utxo, g_id)
    context.submit_tx(tx)
    txid = str(tx.id)

    g_id_cbor = cbor2.dumps([bytes(pkh) for pkh in g_id]).hex()
    print(f"BurnTx submitted: {txid}")
    print(f"g_id for Bitcoin SpendTx: {g_id_cbor}")
    return txid, g_id_cbor


if __name__ == "__main__":
    with open("g_id.json") as f:
        g_id_hex = json.load(f)
    g_id = [VerificationKeyHash(bytes.fromhex(h)) for h in g_id_hex]
    print(f"Loaded g_id: {[h[:8] for h in g_id_hex]}")

    txid, g_id_cbor = submit_burn_tx(g_id)
    print(f"Peg-out complete on Cardano. TxId: {txid}")