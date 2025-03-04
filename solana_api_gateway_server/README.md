# Solana API Gateway Rust Server

## Overview

This project is a Rust-based server that interacts with the Solana blockchain. It provides several endpoints for managing an escrow-based storage subscription system.

## Prerequisites

Before running this project, ensure you have the following installed:

- [Rust v1.84](https://www.rust-lang.org/tools/install)
- [Solana CLI v1.18.26](https://github.com/solana-labs/solana/releases)
- [Anchor CLI 0.30.1](https://book.anchor-lang.com/getting_started/installation.html)

## Configuration

### Setting the Solana Program ID

The Solana program ID is defined in `main.rs`:

```rust
const PROGRAM_ID: &str = "EKRjhax35SiRHvSz44seczjBWvgmSzAeD46ofFyBgoK2";
```

If your program ID is different, update this constant with the correct value.

### Setting the Solana RPC URL

The RPC URLs for different environments are defined in `main.rs`:

```rust
const DEV_RPC_URL: &str = "https://api.localnet.solana.com";

// const LOCAL_RPC_URL: &str = "http://127.0.0.1:8899"; // The localhost url while running locally
const LOCAL_RPC_URL: &str = "http://host.docker.internal:8899";  // The localhost url while running from Docker
```

To use a different RPC URL, modify these values accordingly.

## Running the Solana API Gateway Server

There are two ways to run the Solana API Gateway server:

### Option 1: Run via Docker

you can build and run the project using Docker:

1. **Build the Docker image:**

```sh
docker build -t solana-api-gateway-server .
```

2. **Run the container:**

```sh
docker run -p 3030:3030 solana-api-gateway-server
```

### Option 1: Run Manually

To build and run the project manually, execute the following commands:

```sh
cargo build
cargo run
```

By default, the server will be available at `http://127.0.0.1:3030/`.

### Switching Between Local and Docker Execution

To switch between running locally and inside a Docker container, update the `LOCAL_RPC_URL` constant in [`main.rs`](./src/main.rs):

* For Docker execution: Uncomment the second line and comment the first.

* For local execution: Uncomment the first line and comment the second.

Make sure to update and recompile the project after making changes.

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
  "u": "...", // G1 compressed point in be hex representation.
  "g": "...", // G2 compressed point in be hex representation.
  "v": "...", // G2 compressed point in be hex representation.
  "validate_every": 10, // Validate every time, in seconds.
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
  "amount": 5000000 // Amount in Lamports.
}
```

### 3. Prove Subscription

This endpoint allow the seller to provide a proof of a storage subscription (PoR) by submitting elliptic curve points as proofs (`sigma` and `mu`). It verifies the subscription's validity by processing the proof on the blockchain.

**Endpoint:** `POST /prove` **Request Body:**

```json
{
  "seller_private_key": "...",
  "escrow_pubkey": "...",
  "sigma": "...", // G1 compressed point in be hex representation.
  "mu": "..." // Number under Z_p in be hex representation.
}
```

### 4. Prove Subscription Simulation

This endpoint allows the seller to provide a proof of a storage subscription (PoR) by submitting elliptic curve points as proofs (`sigma` and `mu`). It **validates the PoR proof locally** by processing the elliptic curve operations and pairings on the server. The proof is not submitted to the Solana blockchain for validation at this point due to Solana compute units limit.

The purpose of this endpoint is to simulate the proof verification process and ensure that the proof matches the expected values. This validation is done entirely within the application and does not involve interacting with the Solana blockchain. It is designed to verify the correctness of the proof locally, without making any on-chain updates or transactions.

Once PoR validation is successful, the seller is notified that the proof has been validated. However, the actual submission to the Solana blockchain, if needed, would be handled in a different process or transaction in the future.

**Endpoint:** `POST /prove_simulation` **Request Body:**

```json
{
  "seller_private_key": "...",
  "escrow_pubkey": "...",
  "sigma": "...", // G1 compressed point in be hex representation.
  "mu": "..." // Number under compressed point in be hex representation.
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
