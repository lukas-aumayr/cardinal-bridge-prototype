# utils.py
from dataclasses import dataclass
from pycardano import *
from pycardano.hash import VerificationKeyHash
from typing import List, Optional
from config import context, NETWORK, MIN_ADA, WBTC_ASSET_NAME
from scripts import wbtc_policy_hash

# -------------------------
# Datum types
# -------------------------

@dataclass
class ReleaseDatum(PlutusData):
    """
    ReleaseDatum { hash_h, lock_tx_id, operator_pkh, expiry, recipient }
    Single operator for prototype (pretend aggregated sig).
    """
    CONSTR_ID = 0
    hash_h: bytes
    lock_tx_id: bytes
    operator_pkh: bytes       # single operator pkh
    expiry: int
    recipient: bytes


@dataclass
class CommitBurnDatum(PlutusData):
    """
    CommitBurnDatum { pk_C, instance_id, ek_C }
    """
    CONSTR_ID = 0
    pk_C: bytes
    instance_id: bytes
    ek_C: bytes


@dataclass
class BurnReceiptDatum(PlutusData):
    """
    BurnReceiptDatum { g_id, instance_id }
    """
    CONSTR_ID = 0
    g_id: List[bytes]
    instance_id: bytes


# -------------------------
# Redeemer types — must match Aiken constructor order exactly
# -------------------------

# ReleaseRedeemer: Release = 0, Abort = 1
@dataclass
class _ReleaseRelease(PlutusData):
    CONSTR_ID = 0
    preimage: bytes
    operator_sig: bytes

@dataclass
class _ReleaseAbort(PlutusData):
    CONSTR_ID = 1

class ReleaseRedeemer:
    Release = _ReleaseRelease
    Abort = _ReleaseAbort


# MintRedeemer: Mint = 0, Burn = 1
@dataclass
class _MintMint(PlutusData):
    CONSTR_ID = 0
    preimage: bytes
    operator_sig: bytes
    lock_tx_id: bytes

@dataclass
class _MintBurn(PlutusData):
    CONSTR_ID = 1
    g_id: List[bytes]
    instance_id: bytes

class MintRedeemer:
    Mint = _MintMint
    Burn = _MintBurn


# BurnRedeemer: BurnSpend = 0
@dataclass
class _BurnSpend(PlutusData):
    CONSTR_ID = 0
    g_id: List[bytes]
    instance_id: bytes

class BurnRedeemer:
    BurnSpend = _BurnSpend


# -------------------------
# Datum constructors
# -------------------------

def make_release_datum(
    hash_h: bytes,
    lock_tx_id: bytes,
    operator_pkh: VerificationKeyHash,
    expiry_slot: int,
    recipient_pkh: VerificationKeyHash,
) -> ReleaseDatum:
    return ReleaseDatum(
        hash_h=hash_h,
        lock_tx_id=lock_tx_id,
        operator_pkh=bytes(operator_pkh),
        expiry=expiry_slot,
        recipient=bytes(recipient_pkh),
    )


def make_commit_burn_datum(
    pk_C: VerificationKeyHash,
    instance_id: bytes,
    ek_C: bytes,
) -> CommitBurnDatum:
    return CommitBurnDatum(
        pk_C=bytes(pk_C),
        instance_id=instance_id,
        ek_C=ek_C,
    )


def make_burn_receipt_datum(
    g_id: List[bytes],
    instance_id: bytes,
) -> BurnReceiptDatum:
    return BurnReceiptDatum(
        g_id=g_id,
        instance_id=instance_id,
    )


# -------------------------
# wBTC value helpers
# -------------------------

def wbtc_value(lovelace: int = MIN_ADA, amount: int = 1) -> Value:
    multi_asset = MultiAsset.from_primitive({
        bytes(wbtc_policy_hash): {b"wBTC": amount}
    })
    return Value(lovelace, multi_asset)


# -------------------------
# UTxO helpers
# -------------------------

def find_utxo_at(address: Address) -> UTxO:
    utxos = context.utxos(str(address))
    if not utxos:
        raise ValueError(f"No UTxO found at {address}")
    return utxos[0]


def has_asset(utxo: UTxO, policy_id: ScriptHash = None) -> bool:
    if utxo.output.amount.multi_asset is None:
        return False
    if policy_id is None:
        return True
    return bytes(policy_id) in {bytes(k) for k in utxo.output.amount.multi_asset}


# -------------------------
# Signing helpers
# -------------------------

def sign_and_submit(tx, signing_keys: list) -> str:
    context.submit_tx(tx)
    return str(tx.id)


def sign_bytes(sk: PaymentSigningKey, data: bytes) -> bytes:
    return bytes(sk.sign(data))