
# Solana Smart Contract - Storage Subscription

## Overview

This project is a Solana smart contract (program) built with Anchor that implements an escrow-based subscription system. The contract allows buyers and sellers to securely manage storage subscriptions on the Solana blockchain, including starting storage subscriptions, adding funds, generating queries, proving subscriptions (PoR), and ending storage subscriptions.

## Prerequisites

Before deploying and interacting with the contract, ensure you have the following installed:

- [Rust v1.84](https://www.rust-lang.org/tools/install)
- [Solana CLI v1.18.26](https://github.com/solana-labs/solana/releases)
- [Anchor CLI 0.30.1](https://book.anchor-lang.com/getting_started/installation.html)

## Configuration

### Setting the Solana Program ID

The Solana program ID is defined in [`lib.rs`](./programs/escrow-project/src/lib.rs):

```rust
const PROGRAM_ID: &str = "5LthHd6oNK3QkTwC59pnn1tPFK7JJUgNjNnEptxxXSei";
```

Make sure this value corresponds to the program ID of your deployed contract.

You should also set the program_id in the Anchor configuration file ([`Anchor.toml`](Anchor.toml)). In the `[programs.localnet]` section, define the program ID as follows:

```rust
[programs.localnet]
escrow_project = "5LthHd6oNK3QkTwC59pnn1tPFK7JJUgNjNnEptxxXSei"
```

**Note:**

After deploying the program, verify that the program ID remains unchanged. If the program ID changes, update it in both [`lib.rs`](./programs/escrow-project/src/lib.rs) and [`Anchor.toml`](Anchor.toml), then re-build and re-deploy the program to ensure consistency.

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

This command will deploy your program to the cluster specified in your [`Anchor.toml`](Anchor.toml) file (localnet).

## Program Settings

To modify this setting, simply update the constant in the contract and redeploy the program.

**Proof Submission Deadline**

This parameter determines how much time the seller has to submit a proof to the smart contract after the queries have been generated.

```rust
pub const PROOF_SUBMISSION_DEADLINE: i64 = 30 * MIN_IN_SECOND;
```

**Subscription Duration**

The contract enforces a minimum subscription duration, ensuring that the escrow holds the buyer's funds for a defined period before the seller can claim them upon successful proof submission.

```
pub const MIN_SUBSCRIPTION_DURATION: u64 = 60 * MIN_IN_SECOND;  
```

**Buyer Protection**

To protect the buyer, the contract defines a minimum timeout period after which the buyer can reclaim funds if the seller fails to submit a proof within the allowed timeframe.

```rust
pub const BUYER_REFUND_TIMEOUT: i64 = 1 * MIN_IN_SECOND;  
```

## Contract Instructions

### 1. Start Subscription

This instruction starts a new storage subscription by initializing an escrow account with the provided parameters. The escrow account will store the subscription details and track the buyer, seller, and other related data.

### 2. Add Funds to Subscription

This instruction allows the buyer to add funds (in lamports) to an existing subscription by transferring a specified amount from the buyer's account to the escrow account.

### 3. Generate Queries

This instruction generates queries for a subscription by processing slot hashes from the system's slot hash data. Each query is saved in the escrow account with the timestamp of query generation.

### 4. Prove Subscription

This instruction allows the seller to provide elliptic curve points as proofs (`sigma` and `mu`) to validate the storage subscription (PoR). It updates the escrow account based on the validity of the proof.

**Note:** This instruction is not expected to succeed on-chain due to compute unit (CU) limitations on Solana.  
BLS12-381 operations, such as pairing checks required for proof verification, are computationally expensive and currently unsupported within Solana's constraints. Even at the maximum CU limit, these operations exceed the available execution budget.

As a result, we have commented out the actual validation logic and designed this instruction as a mock to simulate a real verification process. This allows off-chain testing and instruction flow validation without causing execution failures.

In the future, if Solana introduces support for more efficient BLS12-381 operations or increases CU limits, we may be able to uncomment the validation logic and perform actual on-chain verification.

### 5. End Subscription by Buyer

This instruction allows the buyer to end the storage subscription by interacting with the escrow account. It ensures that only the buyer can terminate the subscription.

### 6. End Subscription by Seller

This instruction allows the seller to end the storage subscription by interacting with the escrow account. It ensures that only the seller can terminate the subscription.

### 7. Request Funds

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
    pub validate_every: i64,    // validate every in seconds
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
