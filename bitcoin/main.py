from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.script import Script
from identity import Id
from helper import print_tx, sha256, hash256
import os
from dotenv import load_dotenv
from pathlib import Path

from transactions.lock_req_tx import get_lock_req_tx
from transactions.lock_tx import get_lock_tx
from transactions.abort_tx import get_abort_tx
from transactions.spend_tx import get_spend_tx

def main():
    print('Bitcoin side of the BTC<>Cardano bridge prototype')
    print('Following the TOOP peg-out protocol')
    print()

    # -------------------------
    # Identities
    # -------------------------
    load_dotenv('.env')
    # User A (peg-in initiator)
    id_A  = Id(os.environ["BITCOIN_SK_A"])

    # Operators (O) — single op for prototype (simulating aggregated sig)
    id_op = Id(os.environ["BITCOIN_SK_OP"])

    # g_id: subset of operator keys collected by C during peg-out
    # In production: read from BurnTx datum on Cardano (g_id_cbor from burn_tx.py)
    # For prototype: same as id_op (C received op's ephemeral key)
    id_gid = id_op

    # -------------------------
    # Hash lock (shared with Cardano side)
    # s such that sha256(s) = h
    # In production: A picks s, computes h, uses same h in MintTx datum
    # -------------------------
    secret_s = 'ab'  # hex string — matches SECRET_S in config.py
    hash_h = hash256(secret_s)
    print(f'Secret s:  {secret_s}')
    print(f'Hash h:    {hash_h}')
    print()

    # -------------------------
    # UTxO inputs (replace with real testnet UTxOs)
    # -------------------------
    # A's funding UTxO
    tx_in_A = TxInput(
        '4bbd739a1159c4e936f66211a9785633370dd9441815150affd3641572647794', 1
    )

    # -------------------------
    # Protocol parameters
    # -------------------------
    btc_amount = 100000   # satoshis to bridge
    fee = 500             # satoshis per tx

    # -------------------------
    # Build transactions
    # -------------------------

    # Step 1: A locks BTC — output spendable by op+preimage or A after timelock
    lock_req, htlc_script = get_lock_req_tx(
        tx_in=tx_in_A,
        id_A=id_A,
        id_op=id_op,
        hash_h=hash_h,
        amount=btc_amount,
        fee=fee,
    )
    print_tx(lock_req, 'LockReqTx')

    secret_s = sha256(secret_s)

    # Step 2: Operators move BTC into covenant-locked output (presigned at setup)
    # Output locked to SpendTx only (covenant emulation via op presig)
    lock_tx = get_lock_tx(
        tx_in=TxInput(lock_req.get_txid(), 0),
        id_op=id_op,
        secret_s=secret_s,
        htlc_script=htlc_script,
        amount=btc_amount - fee,
        fee=fee,
    )
    print_tx(lock_tx, 'LockTx')

    # Step 3 (abort path): A reclaims after timelock if LockTx not posted
    abort_tx = get_abort_tx(
        tx_in=TxInput(lock_req.get_txid(), 0),
        id_A=id_A,
        htlc_script=htlc_script,
        amount=btc_amount - fee,
        fee=fee,
    )
    print_tx(abort_tx, 'AbortTx')

    # Step 4 (peg-out): SpendTx releases BTC to C under g_id multisig
    # g_id comes from BurnTx datum on Cardano
    spend_tx = get_spend_tx(
        tx_in=TxInput(lock_tx.get_txid(), 0),
        id_gid=id_gid,
        amount=btc_amount - 2 * fee,
        fee=fee,
    )
    print_tx(spend_tx, 'SpendTx')


if __name__ == '__main__':
    main()