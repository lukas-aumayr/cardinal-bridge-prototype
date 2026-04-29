# release_tx.py
# B releases wBTC by revealing preimage + operator sig over LockTx txid.

from pycardano import *
from config import (
    context, NETWORK, MIN_ADA,
    sk_B, pk_B,
    sk_ops, pk_ops,
    SECRET_S, LOCK_TX_ID,
)
from scripts import (
    release_tx_script, release_tx_address,
    wbtc_policy_hash,
)
from utils import (
    wbtc_value, sign_bytes,
    ReleaseRedeemer,
)


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


def build_release_tx(release_utxo: UTxO, fee_utxo: UTxO, preimage: bytes) -> Transaction:
    op_sig = sign_bytes(sk_ops[0], LOCK_TX_ID)

    rdmr = Redeemer(ReleaseRedeemer.Release(
        preimage=preimage,
        operator_sig=op_sig,
    ))

    b_address = Address(payment_part=pk_B, network=NETWORK)
    token_value = wbtc_value(lovelace=MIN_ADA, amount=1)

    builder = TransactionBuilder(context)

    # Script input with redeemer
    builder.add_script_input(
        utxo=release_utxo,
        script=release_tx_script,
        redeemer=rdmr,
    )

    # Fee input + collateral from B's wallet
    builder.add_input(fee_utxo)
    builder.collaterals = [fee_utxo]

    builder.add_output(TransactionOutput(
        address=b_address,
        amount=token_value,
    ))

    builder.required_signers = [pk_B]

    tx = builder.build_and_sign(
        signing_keys=[sk_B],
        change_address=b_address,
    )
    return tx


def submit_release_tx(preimage: bytes) -> str:
    release_utxo = find_wbtc_utxo(release_tx_address)
    print(f"Found wBTC UTxO: {release_utxo.input.transaction_id}#{release_utxo.input.index}")

    b_address = Address(payment_part=pk_B, network=NETWORK)
    fee_utxo = find_ada_utxo(b_address)
    print(f"Found fee UTxO: {fee_utxo.input.transaction_id}#{fee_utxo.input.index}")

    tx = build_release_tx(release_utxo, fee_utxo, preimage)
    context.submit_tx(tx)
    txid = str(tx.id)
    print(f"ReleaseTx submitted: {txid}")
    return txid


if __name__ == "__main__":
    txid = submit_release_tx(preimage=SECRET_S)
    print(f"wBTC released to B. TxId: {txid}")