# Cardinal2 — BTC<->Cardano Bridge Prototype

A proof-of-concept implementation of a Bitcoin<->Cardano bridge following the TOOP peg-out protocol. The prototype covers both the peg-in (BTC -> wBTC) and peg-out (wBTC -> BTC) directions, with on-chain transactions deployed on Bitcoin testnet and Cardano Preprod testnet. An additional Ethereum ERC-721 implementation is included to demonstrate compatibility with account-based blockchains.

## Repository Structure

```
cardinal2/
├── bitcoin/                 # Bitcoin transaction graph (Python)
│   ├── main.py
│   ├── transactions/
│   │   ├── lock_req_tx.py
│   │   ├── lock_tx.py
│   │   ├── abort_tx.py
│   │   └── spend_tx.py
│   ├── identity.py
│   ├── helper.py
│   ├── consts.py
│   └── init.py
├── bridge-validators/       # Aiken validators (PlutusV3)
│   └── validators/
│       └── bridge.ak
├── ethereum/                # Ethereum ERC-721 contract (Solidity)
│   └── src/
│       └── WBTCBridge.sol
├── config.py                # Keys, parameters, hash lock
├── scripts.py               # Loads compiled Aiken scripts
├── utils.py                 # Datum/redeemer types, helpers
├── mint_tx.py               # Cardano: operators mint wBTC
├── release_tx.py            # Cardano: B releases wBTC
├── commit_burn_tx.py        # Cardano: C commits to burn
└── burn_tx.py               # Cardano: C burns wBTC, commits g_id
```

## Prerequisites

**Python**
```bash
python3 -m venv bridge-env
source bridge-env/bin/activate
pip install -r requirements.txt
```

**Aiken** (for compiling Cardano validators)
```bash
curl -sSfL https://install.aiken-lang.org | bash
aikup
```

**Foundry** (for Ethereum)
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

## Setup

1. Copy the example env file and fill in your values:
   ```bash
   cp .env.example .env
   ```
   You need a [Blockfrost](https://blockfrost.io) project ID for Cardano Preprod — sign up for a free account and create a Preprod project.

2. Generate Cardano keys:
   ```bash
   python keygen.py
   ```

3. Fund addresses from faucets:
   - Cardano Preprod: https://docs.cardano.org/cardano-testnets/tools/faucet
   - Bitcoin testnet: https://bitcoinfaucet.uo1.net

4. Compile Aiken validators:
   ```bash
   cd bridge-validators
   aiken build
   cd ..
   ```

## Cardano — Peg-in

```bash
# Operators mint wBTC and lock it at the HTLC validator
python mint_tx.py

# B releases wBTC by revealing the preimage + operator signature over LockTx txid
python release_tx.py
```

## Cardano — Peg-out (TOOP)

```bash
# C commits to burning, publishes ek_C for operator key exchange
python commit_burn_tx.py

# C burns wBTC and commits g_id on-chain
python burn_tx.py
```

## Bitcoin

```bash
cd bitcoin
python main.py
```

Builds and prints `LockReqTx`, `LockTx`, `AbortTx`, and `SpendTx`. To broadcast, paste the serialized hex into a testnet explorer such as https://blockstream.info/testnet/tx/push, or add a submission call using the Blockstream API.

**Setup**: replace the placeholder UTxO inputs in `main.py` with real testnet UTxOs funded from a faucet. The secret and hash lock must match the values in `config.py` on the Cardano side.

## Ethereum

See [`ethereum/README.md`](ethereum/README.md) for setup and deployment instructions.

## Testnet Transactions

| Chain | Transaction | TxId |
|---|---|---|
| Cardano | MintTx | `26d72626...` |
| Cardano | ReleaseTx | `32b1f625...` |
| Cardano | CommitBurnTx | `d2ac0c06...` |
| Cardano | BurnTx | `50a1abbf...` |
| Ethereum | Deploy | `0xdb31be40...` |
| Ethereum | Mint | `0x4c29b596...` |
| Ethereum | CommitBurn | `0xa3f2722f...` |