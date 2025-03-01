# Solana API Gateway Rust Server

## Overview

This project is a Rust-based server that interacts with the Solana blockchain. It provides several endpoints for managing an escrow-based storage subscription system.

## Prerequisites

Before running this project, ensure you have the following installed:

- [Rust](https://www.rust-lang.org/tools/install)
- [Solana CLI](https://docs.solana.com/cli/install-solana-cli)
- [Anchor](https://book.anchor-lang.com/getting_started/installation.html)

## Configuration

### Setting the Solana Program ID

The Solana program ID is defined in `main.rs`:

```rust
const PROGRAM_ID: &str = "5LthHd6oNK3QkTwC59pnn1tPFK7JJUgNjNnEptxxXSei";
```

If your program ID is different, update this constant with the correct value.

### Setting the Solana RPC URL

The RPC URLs for different environments are defined in `main.rs`:

```rust
const DEV_RPC_URL: &str = "https://api.localnet.solana.com";
const LOCAL_RPC_URL: &str = "http://127.0.0.1:8899";
```

To use a different RPC URL, modify these values accordingly.

## Running the Project

To build and run the project, execute the following commands:

```sh
cargo build
cargo run
```

By default, the server will be available at `http://127.0.0.1:3030/`.

## Curl Templates and Examples

Example `curl` requests for all endpoints are available in the [`./curls`](./curls) directory. You can use them to quickly test the API.

## API Endpoints

The server provides the following endpoints:

### 1. Start Subscription

This endpoint initiates a new storage subscription between a buyer and a seller on the Solana blockchain. It generates a unique subscription ID, derives an escrow public key, and sends a transaction to start the subscription, returning the subscription ID and escrow public key upon success.

**Endpoint:** `POST /start_subscription` **Request Body:**

```json
{
  "query_size": 64,
  "number_of_blocks": 100,
  "u": "...",
  "g": "...",
  "v": "...",
  "validate_every": 10,
  "buyer_private_key": "...",
  "seller_pubkey": "..."
}
```

### 2. Add Funds to Subscription

This endpoint allows the buyer to add funds (in lamports) to an existing subscription by interacting with the escrow account.

**Endpoint:** `POST /add_funds_to_subscription` **Request Body:**

```json
{
  "buyer_private_key": "...",
  "escrow_pubkey": "...",
  "amount": 5000000
}
```

### 3. Prove Subscription

This endpoint allow the seller to provide a proof of a storage subscription (PoR) by submitting elastic curve points as proofs (`sigma` and `mu`). It verifies the subscription's validity by processing the proof on the blockchain.

**Endpoint:** `POST /prove` **Request Body:**

```json
{
  "seller_private_key": "...",
  "escrow_pubkey": "...",
  "sigma": "...",
  "mu": "..."
}
```

### 4. Prove Subscription Simulation

This endpoint allows the seller to simulate the proof verification for a storage subscription by submitting elastic curve points (`sigma` and `mu`). It bypasses the on-chain BLS pairing operation due to compute unit limitations and sends a pre-verified result (`is_verified`) to the blockchain.

**Endpoint:** `POST /prove` **Request Body:**

```json
{
  "seller_private_key": "...",
  "escrow_pubkey": "...",
  "sigma": "...",
  "mu": "..."
}
```

### 5. End Subscription by Buyer

This endpoint allows the buyer to terminate a storage subscription by interacting with the escrow account.

**Endpoint:** `POST /end_subscription_by_buyer` **Request Body:**

```json
{
  "buyer_private_key": "...",
  "escrow_pubkey": "..."
}
```

### 6. End Subscription by Seller

This endpoint allows the seller to terminate a storage subscription by interacting with the escrow account.

**Endpoint:** `POST /end_subscription_by_seller` **Request Body:**

```json
{
  "seller_private_key": "...",
  "escrow_pubkey": "..."
}
```

### 7. Request Funds

This endpoint enables a user (buyer or seller) to request funds from an escrow account. The transaction is processed to release the funds from escrow to the requester’s account.

**Endpoint:** `POST /request_funds` **Request Body:**

```json
{
  "user_private_key": "...",
  "escrow_pubkey": "..."
}
```

### 8. Generate Queries

This endpoint generates queries for a given escrow account by allowing the user to submit a request for queries to be created and associated with a specific escrow.

**Endpoint:** `POST /generate_queries` **Request Body:**

```json
{
  "escrow_pubkey": "...",
  "user_private_key": "..."
}
```

### 9. Get Queries by Escrow

This endpoint retrieves all queries associated with a particular escrow account. It provides the list of queries linked to the escrow's public key.

**Endpoint:** `POST /get_queries_by_escrow` **Request Body:**

```json
{
  "escrow_pubkey": "..."
}
```

### 10. Get Escrow Data

This endpoint fetches data related to a specific escrow account.

**Endpoint:** `POST /get_escrow_data` **Request Body:**

```json
{
  "escrow_pubkey": "..."
}
```
