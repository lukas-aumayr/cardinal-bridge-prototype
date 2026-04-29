# Ethereum Bridge Prototype (ERC-721)

Mint/burn logic for the BTC↔Ethereum bridge, implemented as an ERC-721 contract on Sepolia testnet.

## Prerequisites

Install Foundry (includes `forge` and `cast`):

```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

Install OpenZeppelin contracts:

```bash
forge install OpenZeppelin/openzeppelin-contracts
```

## Setup

1. Copy the example env file and fill in your values:
   ```bash
   cp .env.example .env
   ```

2. Generate a private key and address:
   ```bash
   cast wallet new
   ```

3. Update `.env` with your private key and operator address (same address for prototype).

4. Optionally fund your address from the [Sepolia faucet](https://cloud.google.com/application/web3/faucet/ethereum/sepolia).

5. Source the env:
   ```bash
   source .env
   ```

## Deploy

```bash
forge create --broadcast src/WBTCBridge.sol:WBTCBridge \
  --rpc-url $SEPOLIA_RPC_URL \
  --private-key $PRIVATE_KEY \
  --constructor-args $OPERATOR_ADDRESS
```

Update `CONTRACT_ADDR` in `.env` with the deployed contract address, then re-source:

```bash
source .env
```

## Run the protocol

First generate an operator signature for the mint (using the python env from the parent project):

```bash
python simulate_mint.py
```

Replace placeholders in .env with your actual values and re-source. Then run the three transactions. 

```bash
# 1. Mint — operator signs LockTx txid, wBTC NFT minted to recipient
cast send $CONTRACT_ADDR "mint(address,bytes32,bytes32,bytes)" \
  $RECIPIENT \
  $INSTANCE_ID \
  $LOCK_TX_ID \
  $SIGNATURE \
  --rpc-url $SEPOLIA_RPC_URL --private-key $PRIVATE_KEY

# 2. CommitBurn — burns the NFT, publishes encryption key ek_C on-chain
#    Operators observe this event and send their ephemeral keys to the holder
cast send $CONTRACT_ADDR "commitBurn(uint256,bytes)" \
  <tokenId> <ekC> \
  --rpc-url $SEPOLIA_RPC_URL --private-key $PRIVATE_KEY

# 3. SubmitGid — commits g_id on-chain for ChainVM to verify on Bitcoin
cast send $CONTRACT_ADDR "submitGid(bytes32,bytes32[])" \
  $INSTANCE_ID \
  "[<gid_entry_1>, <gid_entry_2>, ...]" \
  --rpc-url $SEPOLIA_RPC_URL --private-key $PRIVATE_KEY
```

## Contract

| Function | Description |
|---|---|
| `mint(recipient, instanceId, lockTxId, sig)` | Peg-in: mint wBTC NFT after operator confirms Bitcoin LockTx |
| `commitBurn(tokenId, ekC)` | Peg-out: burn NFT and signal operators with encryption key |
| `submitGid(instanceId, gId)` | Peg-out: commit operator key subset on-chain for ChainVM |
