from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.script import Script
from identity import Id


def get_spend_tx(
    tx_in: TxInput,
    id_gid: Id,
    amount: float,
    fee: float,
) -> Transaction:
    """
    SpendTx: Releases BTC to C under the g_id operator key.

    In the full protocol:
      - Output of LockTx is covenant-locked to this specific tx
      - ChainVM verifies that g_id here matches the g_id committed
        in the Cardano BurnTx datum
      - SpendTx is locked under MSigScr_{g_id}

    For the prototype:
      - g_id = single operator key (id_gid)
      - ChainVM verification abstracted away
      - id_gid signs to release BTC to C (same party in prototype)
    """
    # Output goes to g_id operator (who will pass funds to C)
    # In production: output directly to C after ChainVM verification
    tx_out = TxOutput(amount - fee, id_gid.p2pkh)
    tx = Transaction([tx_in], [tx_out])

    # LockTx output is bare <pk> OP_CHECKSIG — sign against that script
    from bitcoinutils.script import Script
    lock_script = Script([id_gid.pk.to_hex(), 'OP_CHECKSIG'])
    sig_gid = id_gid.sk.sign_input(tx, 0, lock_script)
    tx_in.script_sig = Script([sig_gid])

    return tx