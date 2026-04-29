use aiken/collection/list
use aiken/interval.{Finite}
use aiken/crypto.{VerificationKeyHash, sha2_256, verify_ed25519_signature}
use cardano/transaction.{Transaction, OutputReference}
use cardano/assets.{PolicyId}

// -------------------------
// Operator verification key (hardcoded for prototype)
// op0 raw Ed25519 vk bytes
// -------------------------
const operator_vk: ByteArray =
  #"4095d7268b1c1b42967d291090e122aafcd34384222ed6aa126eda951e72833e"

// -------------------------
// Datum types
// -------------------------

pub type ReleaseDatum {
  hash_h: ByteArray,
  lock_tx_id: ByteArray,
  operator_pkh: VerificationKeyHash,
  expiry: Int,
  recipient: VerificationKeyHash,
}

pub type CommitBurnDatum {
  pk_C: VerificationKeyHash,
  instance_id: ByteArray,
  ek_C: ByteArray,
}

// -------------------------
// Redeemer types
// -------------------------

pub type ReleaseRedeemer {
  Release { preimage: ByteArray, operator_sig: ByteArray }
  Abort
}

pub type MintRedeemer {
  Mint { preimage: ByteArray, operator_sig: ByteArray, lock_tx_id: ByteArray }
  Burn { g_id: List<VerificationKeyHash>, instance_id: ByteArray }
}

pub type BurnRedeemer {
  BurnSpend { g_id: List<VerificationKeyHash>, instance_id: ByteArray }
}

// -------------------------
// Helpers
// -------------------------

fn signed_by(tx: Transaction, pkh: VerificationKeyHash) -> Bool {
  list.has(tx.extra_signatories, pkh)
}

fn verify_op_sig(sig: ByteArray, message: ByteArray) -> Bool {
  verify_ed25519_signature(operator_vk, message, sig)
}

fn has_negative_mint(tx: Transaction) -> Bool {
  tx.mint
    |> assets.flatten
    |> list.any(fn(entry) {
        let (_, _, qty) = entry
        qty < 0
      })
}

// -------------------------
// 1. wBTC Minting Policy
// -------------------------

validator wbtc_policy {
  mint(redeemer: MintRedeemer, _policy_id: PolicyId, tx: Transaction) {
    when redeemer is {
      Mint { preimage: _, operator_sig, lock_tx_id } ->
        // Operator authorised this mint by signing the LockTx txid
        verify_op_sig(operator_sig, lock_tx_id)
      Burn { g_id: _, instance_id: _ } ->
        // Burn is valid as long as something is being burned
        // (enforced structurally by burn_tx validator on the input)
        has_negative_mint(tx)
    }
  }
}

// -------------------------
// 2. ReleaseTx Validator
// -------------------------

validator release_tx {
  spend(
    datum: Option<ReleaseDatum>,
    redeemer: ReleaseRedeemer,
    _utxo: OutputReference,
    tx: Transaction,
  ) {
    expect Some(d) = datum
    when redeemer is {
      Release { preimage, operator_sig } -> {
        let hash_ok = sha2_256(preimage) == d.hash_h
        let sig_ok = verify_op_sig(operator_sig, d.lock_tx_id)
        let recipient_ok = signed_by(tx, d.recipient)
        hash_ok && sig_ok && recipient_ok
      }
      Abort -> {
        let expired =
          when tx.validity_range.lower_bound.bound_type is {
            Finite(slot) -> slot >= d.expiry
            _ -> False
          }
        expired && signed_by(tx, d.operator_pkh)
      }
    }
  }
}

// -------------------------
// 3. CommitBurn Validator
// -------------------------

validator commit_burn {
  spend(
    datum: Option<CommitBurnDatum>,
    _redeemer: Data,
    _utxo: OutputReference,
    tx: Transaction,
  ) {
    expect Some(d) = datum
    signed_by(tx, d.pk_C)
  }
}

// -------------------------
// 4. BurnTx Validator
// -------------------------

validator burn_tx {
  spend(
    datum: Option<CommitBurnDatum>,
    redeemer: BurnRedeemer,
    _utxo: OutputReference,
    tx: Transaction,
  ) {
    expect Some(d) = datum
    when redeemer is {
      BurnSpend { .. } ->
        signed_by(tx, d.pk_C) && has_negative_mint(tx)
    }
  }
}