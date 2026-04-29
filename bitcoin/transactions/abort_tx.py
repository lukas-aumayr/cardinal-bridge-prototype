from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.script import Script
from identity import Id
from consts import timelock


def get_abort_tx(
    tx_in: TxInput,
    id_A: Id,
    htlc_script: Script,
    amount: float,
    fee: float,
) -> Transaction:
    """
    AbortTx: A reclaims BTC via the timeout path (OP_ELSE branch).
    Requires CSV timelock to have passed.

    script_sig: <A_sig> OP_0 <redeem_script>
    """
    tx_out = TxOutput(amount - fee, id_A.p2pkh)
    tx = Transaction([tx_in], [tx_out])

    # Enforce CSV via nSequence
    tx_in.sequence = timelock.to_bytes(4, byteorder='little')

    # Sign against the redeem script
    sig_A = id_A.sk.sign_input(tx, 0, htlc_script)

    tx_in.script_sig = Script([
        sig_A,
        'OP_0',                  # take OP_ELSE branch
        htlc_script.to_hex(),    # redeem script pushed as data
    ])

    return tx