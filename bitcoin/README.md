# Bitcoin Bridge Prototype

Bitcoin transaction graph for the BTC <-> Cardano bridge, covering peg-in and peg-out.

## Prerequisites

Use parent python env.

## Setup

1. Generate a private key and address for user A and the operator:
   ```bash
   python -c "from bitcoinutils.keys import PrivateKey; k = PrivateKey(); print(k.to_bytes().hex(), k.get_public_key().get_address().to_string())"
   ```
   Run this twice — once for A, once for the operator.

2. Add the keys and addresses to the root `.env`:
   ```bash
   BITCOIN_SK_A=your_hex_private_key
   BITCOIN_SK_OP=your_hex_private_key
   ADDR_A=...
   ADDR_OP=...
   ```

3. Fund the address A from the [Bitcoin testnet faucet](https://bitcoinfaucet.uo1.net). Use A's address for peg-in funding.

4. Replace the `tx_in_A` UTxO in `main.py` with a real funded UTxO and the correct input index:
   ```python
   tx_in_A = TxInput('your_txid', output_index)
   ```
   Check your UTxOs at https://blockstream.info/testnet.

5. Set `btc_amount` to the amount available in your UTxO (in satoshis, minus fees).

## Run

```bash
cd bitcoin
python main.py
```

This builds and prints all four transactions. To broadcast, paste the raw hex into:
- https://blockstream.info/testnet/tx/push

Broadcast in order: `LockReqTx` first, then `LockTx` (or `AbortTx` for the abort path), then `SpendTx` after the Cardano peg-out is complete.

## Transactions

| Transaction | Description |
|---|---|
| `LockReqTx` | A locks BTC in a P2SH HTLC |
| `LockTx` | Operator moves BTC into covenant-locked output (happy path) |
| `AbortTx` | A reclaims BTC after timelock (abort path) |
| `SpendTx` | BTC released to C under g_id after Cardano burn |