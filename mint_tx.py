# mint_tx.py
# Operators mint 1 wBTC on Cardano and lock it at release_tx_address.
# Uses real PlutusV3 minting policy.

from pycardano import *
from config import (
    context, NETWORK, MIN_ADA,
    pk_ops, sk_ops, vk_ops,
    pk_B, HASH_H, LOCK_TX_ID, T_RELEASE_TX, INSTANCE_ID,
    SECRET_S,
)
from scripts import (
    wbtc_policy_script, wbtc_policy_hash,
    release_tx_address,
)
from utils import (
    make_release_datum, wbtc_value, sign_bytes,
    MintRedeemer,
)


def build_mint_tx(operator_funding_utxo: UTxO, preimage: bytes) -> Transaction:
    # Operator signs LockTx txid to authorise the mint
    op_sig = sign_bytes(sk_ops[0], LOCK_TX_ID)

    datum = make_release_datum(
        hash_h=HASH_H,
        lock_tx_id=LOCK_TX_ID,
        operator_pkh=pk_ops[0],
        expiry_slot=T_RELEASE_TX,
        recipient_pkh=pk_B,
    )

    rdmr = Redeemer(MintRedeemer.Mint(
        preimage=preimage,
        operator_sig=op_sig,
        lock_tx_id=LOCK_TX_ID,
    ))

    token_value = wbtc_value(lovelace=MIN_ADA, amount=1)
    op_address = Address(payment_part=pk_ops[0], network=NETWORK)

    builder = TransactionBuilder(context)
    builder.add_input(operator_funding_utxo)
    builder.collaterals = [operator_funding_utxo]

    builder.add_minting_script(
        script=wbtc_policy_script,
        redeemer=rdmr,
    )
    builder.mint = MultiAsset.from_primitive({
        bytes(wbtc_policy_hash): {b"wBTC": 1}
    })

    builder.add_output(
        TransactionOutput(
            address=release_tx_address,
            amount=token_value,
            datum=datum,
        )
    )

    builder.required_signers = [pk_ops[0]]

    tx = builder.build_and_sign(
        signing_keys=sk_ops,
        change_address=op_address,
    )
    return tx


def submit_mint_tx(operator_funding_utxo: UTxO, preimage: bytes) -> str:
    tx = build_mint_tx(operator_funding_utxo, preimage)
    context.submit_tx(tx)
    txid = str(tx.id)
    print(f"MintTx submitted: {txid}")
    return txid


if __name__ == "__main__":
    op_address = Address(payment_part=pk_ops[0], network=NETWORK)
    funding_utxo = context.utxos(str(op_address))[0]
    txid = submit_mint_tx(funding_utxo, preimage=SECRET_S)
    print(f"wBTC minted and locked. TxId: {txid}")