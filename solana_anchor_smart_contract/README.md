
# Solana Smart Contract - Storage Subscription

## Overview

This project is a Solana smart contract (program) built with Anchor that implements an escrow-based subscription system. The contract allows buyers and sellers to securely manage storage subscriptions on the Solana blockchain, including starting storage subscriptions, adding funds, generating queries, proving subscriptions (PoR), and ending storage subscriptions.

## Prerequisites

Before deploying and interacting with the contract, ensure you have the following installed:

- [Rust](https://www.rust-lang.org/tools/install)
- [Solana CLI](https://docs.solana.com/cli/install-solana-cli)
- [Anchor](https://book.anchor-lang.com/getting_started/installation.html)

## Configuration

### Setting the Solana Program ID

The Solana program ID is defined in `lib.rs`:

```rust
const PROGRAM_ID: &str = "5LthHd6oNK3QkTwC59pnn1tPFK7JJUgNjNnEptxxXSei";
```

Make sure this value corresponds to the program ID of your deployed contract.

You should also set the program_id in the Anchor configuration file ([`Anchor.toml`](Anchor.toml)). In the `[programs.localnet]` section, define the program ID as follows:

```rust
[programs.localnet]
escrow_project = "5LthHd6oNK3QkTwC59pnn1tPFK7JJUgNjNnEptxxXSei"
```

## Running and Deploying the Anchor Smart Contract

### 1. Set Up the Solana Cluster
Before deploying, ensure your Solana CLI is connected to the correct cluster.

```sh
solana config set --url http://127.0.0.1:8899
```

This command configures your Solana CLI to point to a localnet cluster.

### 2. Build the Program

Use the following command to build your smart contract program using Anchor:

```sh
anchor build
```

This will compile your Rust-based smart contract into a deployable program for Solana.

### 3. Deploy the Program

To deploy your program to the Solana blockchain, run the following command:

```sh
anchor deploy
```

This command will deploy your program to the cluster specified in your Anchor.toml file (localnet).

## Contract Instructions

### 1. Start Subscription

This instruction starts a new storage subscription by initializing an escrow account with the provided parameters. The escrow account will store the subscription details and track the buyer, seller, and other related data.

### 2. Add Funds to Subscription

This instruction allows the buyer to add funds (in lamports) to an existing subscription by transferring a specified amount from the buyer's account to the escrow account.

### 3. Generate Queries

This instruction generates queries for a subscription by processing slot hashes from the system's slot hash data. Each query is saved in the escrow account with the timestamp of query generation.

### 4. Prove Subscription

This instruction allows the seller to provide a elastic curve points as proofs (`sigma` and `mu`) to validate the storage subscription (PoR). It updates the escrow account based on the validity of the proof.

### 5. Prove Subscription Simulation

This instruction simulates proof verification for a subscription due to Solana’s compute unit limitations. The actual BLS pairing operation is too costly to execute on-chain, so the function uses a boolean flag (`is_verified`) to indicate off-chain verification.
If `is_verified` is `true`, the function updates the escrow account by extending the subscription duration and transferring funds to the seller if conditions are met.

### 6. End Subscription by Buyer

This instruction allows the buyer to end the storage subscription by interacting with the escrow account. It ensures that only the buyer can terminate the subscription.

### 7. End Subscription by Seller

This instruction allows the seller to end the storage subscription by interacting with the escrow account. It ensures that only the seller can terminate the subscription.

### 8. Request Funds

This instruction handles the fund request process for both the buyer and the seller. The function ensures that the requesting user is either the buyer or the seller and checks that the conditions are met. If successful, the funds are transferred from the escrow account to the user.

## Contract Structure

### Escrow Account

The escrow account stores the subscription's data, including the buyer, seller, subscription amount, and other details:

```rust
#[account]
pub struct Escrow {
    pub buyer_pubkey: Pubkey,
    pub seller_pubkey: Pubkey,
    pub query_size: u64,
    pub number_of_blocks: u64,
    pub u: [u8; 48],
    pub g: [u8; 96],
    pub v: [u8; 96],
    pub subscription_duration: u64,
    pub validate_every: i64,
    pub queries: Vec<(u128, [u8; 32])>,
    pub queries_generation_time: i64,
    pub balance: u64,
    pub last_prove_date: i64,
    pub is_subscription_ended_by_buyer: bool,
    pub is_subscription_ended_by_seller: bool,
    pub subscription_id: u64,
    pub bump: u8,
}
```
