from bitcoinutils.transactions import Transaction, TxInput, TxOutput
from bitcoinutils.script import Script
from bitcoinutils.keys import P2shAddress
from identity import Id
from consts import timelock


def get_lock_req_tx(
    tx_in: TxInput,
    id_A: Id,
    id_op: Id,
    hash_h: str,
    amount: float,
    fee: float,
):
    """
    LockReqTx: A locks BTC in a P2SH-wrapped HTLC.

    Redeem script:
      IF
        OP_SHA256 <h> OP_EQUALVERIFY <op_pk> OP_CHECKSIG  -- op + preimage
      ELSE
        <timelock> OP_CSV OP_DROP <A_pk> OP_CHECKSIG      -- abort after timelock
      ENDIF

    Returns (tx, htlc_script) — callers need htlc_script to spend the output.
    """
    htlc_script = Script([
        'OP_IF',
            'OP_SHA256', hash_h, 'OP_EQUALVERIFY',
            id_op.pk.to_hex(), 'OP_CHECKSIG',
        'OP_ELSE',
            timelock, 'OP_CHECKSEQUENCEVERIFY', 'OP_DROP',
            id_A.pk.to_hex(), 'OP_CHECKSIG',
        'OP_ENDIF',
    ])

    # Wrap in P2SH so the output script is standard
    p2sh_addr = P2shAddress.from_script(htlc_script)
    p2sh_script = p2sh_addr.to_script_pub_key()

    tx_out = TxOutput(amount - fee, p2sh_script)
    tx = Transaction([tx_in], [tx_out])

    sig_A = id_A.sk.sign_input(tx, 0, id_A.p2pkh)
    tx_in.script_sig = Script([sig_A, id_A.pk.to_hex()])

    return tx, htlc_script