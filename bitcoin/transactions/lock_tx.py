from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.script import Script
from bitcoinutils.keys import P2pkhAddress
from identity import Id


def get_lock_tx(
    tx_in: TxInput,
    id_op: Id,
    secret_s: str,
    htlc_script: Script,
    amount: float,
    fee: float,
) -> Transaction:
    """
    LockTx: Operator spends the P2SH HTLC via the happy path (OP_IF branch).
    Output: locked under operator key (covenant emulation for prototype).

    script_sig: <op_sig> <secret_s> OP_1 <redeem_script>
    """
    covenant_script = Script([
        id_op.pk.to_hex(), 'OP_CHECKSIG',
    ])

    tx_out = TxOutput(amount - fee, covenant_script)
    tx = Transaction([tx_in], [tx_out])

    # Sign against the redeem script (not the P2SH scriptPubKey)
    sig_op = id_op.sk.sign_input(tx, 0, htlc_script)

    tx_in.script_sig = Script([
        sig_op,
        secret_s,
        'OP_1',                  # take OP_IF branch
        htlc_script.to_hex(),    # redeem script pushed as data
    ])

    return tx