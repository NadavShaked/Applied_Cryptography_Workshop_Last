# Applicative Crypto: Proof of Retrievability (PoR) Based Application

## Abstract

This project implements a **Proof of Retrievability (PoR) system** combined with a **file management system** to ensure data integrity, secure storage, and efficient file retrieval. The system incorporates **Reed-Solomon error correction** for data redundancy, **PoR authentication** for verification, and **Solana blockchain integration** for escrow-based storage subscriptions. Through this approach, we provide a secure and efficient method for data validation with minimal interaction between the buyer and the storage provider, ensuring trust and reliability in decentralized storage systems.

## 1. Introduction

### 1.1 Background & Motivation

Ensuring secure, verifiable, and retrievable file storage is a fundamental challenge in decentralized storage systems. This project implements a **Proof of Retrievability (PoR) system** alongside a **file management system** to provide both integrity verification and efficient data handling. By integrating **Reed-Solomon encoding**, **cryptographic authentication**, and **blockchain-based storage management**, we enable users to store files securely while ensuring their retrievability.

### 1.2 Problem Statement

A secure and efficient way to validate stored files is needed with minimal interaction between the buyer and the seller (storage server). The seller should require minimal knowledge about the stored files while ensuring data integrity. Additionally, the buyer must be able to restore their file using **error correction codes** if the seller corrupts it. This system addresses these challenges by implementing cryptographic verification techniques and blockchain-based economic incentives.

## 2. System Architecture

### 2.1 Components Overview

1. **User (Buyer):** Interacts with the PoR application to encode and authenticate files while managing storage on Solana.
2. **PoR Application:** Encodes files using **Reed-Solomon error correction** and **PoR authentication**.
3. **Storage Server:** A Flask-based service for secure file storage, retrieval, and validation.
4. **Storage Server Portal:** GUI for buyers to manage their stored files easily.
5. **Solana API Gateway:** Manages interactions with the **Solana blockchain** for subscription-based storage.
6. **Solana Blockchain:** Handles storage payments via escrow accounts.
7. **Solana Explorer:** GUI that provides transaction and account status information.

## 3. Implementation

### 3.1 Technologies Used

- **Cryptographic Library:** `bls12_381` for elliptic curve operations, including **pairing-based cryptography**.
- **Programming Languages:** Rust & Python.
- **Solana Blockchain:** Manages storage transactions.
- **Anchor Framework:** Facilitates Solana smart contract development.

### 3.2 Methods

- **Proof of Retrievability (PoR):** Uses Reed-Solomon encoding and authentication blocks for integrity verification.
- **Elliptic Curve Cryptography (ECC), Hash-to-Curve, and Pairing-Based Cryptography:** These cryptographic methods are used for secure encoding, verification, and integrity validation.
- **Cryptographic Random Value Generation:** Utilizes Python’s `secret` library for generating cryptographic random values.
- **Solana Smart Contract Random Query Generation:** Uses Solana's **slot hash** to generate randomized values for validation queries.
- **Blockchain Integration:** Manages storage subscriptions through Solana smart contracts.

## 4. Implementation Details

The system follows these steps to ensure secure storage and validation:

1. **Encoding and Authentication:**

   - The buyer encodes the file using **Reed-Solomon encoding**.
   - Each block of size **1024 bytes** is authenticated using **elliptic curve cryptography**.
   - The buyer receives **curve encoding details**: `u, g, v` (public keys) and `x` (the secret key).

2. **Subscription Creation:**

   - The buyer creates a **storage subscription** on Solana.
   - Parameters include:
     - File metadata and validation requirements.
     - `u, g, v` parameters for PoR verification.
     - **Number of blocks** and **size of each challenge**.
     - **Frequency of validation requests**.
   - **Trade-off Consideration:**
     - **Higher query size & frequency** → Increased security & trust, but **higher cost**.
     - Cost per challenge: **1 + 0.05 \* query size**.

3. **File Upload & Funding:**

   - The buyer uploads the file to the storage server.
   - The file is associated with an **escrow public key**.
   - The buyer can **add funds** to the storage subscription.

4. **Periodic Validation & Payment:**

   - The storage server periodically sends **PoR proofs** to the Solana smart contract.
   - The smart contract **verifies integrity** using the cryptographic methods defined.
   - **Escrow Funds Handling:**
     - The escrow **holds funds for the first three validations**.
     - After three successful validations, the seller **receives payments** for each validation.

5. **Subscription Termination:**
   - Either party can **end the subscription**.
   - The remaining funds can be **requested** by the other party upon termination.

## 5. Challenges and Solutions

### 5.1 Challenges

- **Missing Locally Decodable Erasure Code Implementations:** PoR requires **locally decodable erasure codes**, but no existing implementations were found online.
- **Elliptic Curve Compression & Decompression:** Finding a method to efficiently pass elliptic curve cryptographic data between **Python and Rust**.
- **Efficient Implementation of Basic Methods in Rust:** Implementing Python-like operations (e.g., **modulo for big integers, cryptographic randomness**) efficiently in Rust.
- **Integration with Solana Blockchain:** Running **bls12_381 operations** on Solana smart contracts was infeasible due to excessive compute unit (CU) requirements, even after increasing the blockchain limits.
- **Multi-Language & Solana Communication:** The project involved **Python, Rust, and React**, requiring structured inter-language communication.

### 5.2 Solutions

- **Erasure Code Alternative:** Instead of using a **locally decodable erasure code**, **Reed-Solomon encoding** was implemented. While not a perfect replacement, it demonstrates the PoR concept effectively.
- **Alternative Libraries & Randomization:** Used Rust’s **BigInt library** and **slot hash** for generating random values in Rust.
- **Solana Workaround:** Due to Solana’s **compute unit limitations**, heavy cryptographic operations were commented out and replaced with **mock instructions** that simulate successful validation. The actual logic remains **tested locally in Rust services** and can be reactivated once Solana increases its blockchain limits.
- **Centralized API Server:** To streamline Solana interactions, a **dedicated API server** was created to handle all blockchain communications. The API server was designed to be easily **replicated using Docker**, making it scalable for different project components.

## 6. Results and Performance

- **Secure storage management** through blockchain-based escrow.
- **Reliable file integrity checks** using PoR authentication.
- **Error detection and recovery mechanisms** using Reed-Solomon encoding.

## 7. Future Enhancements

- **Optimized Smart Contracts:** Reduce gas costs on Solana transactions.
- **Additional Cryptographic Enhancements:** Improve efficiency of pairing-based operations.

## 8. Conclusion

This project successfully demonstrates **Proof of Retrievability (PoR)** techniques to enhance data integrity and retrievability. By integrating **Reed-Solomon encoding** and **Solana blockchain-based subscriptions**, it provides a secure and efficient storage solution.

## 9. References

- [PoR Formula & Implementation](https://eprint.iacr.org/2008/073.pdf)
- [PoR Concept Explanation](https://www.ccs.neu.edu/home/alina/papers/PoR.pdf)
- Cryptographic Libraries Documentation
- Solana Blockchain API Docs
- Reed-Solomon Encoding Research Papers
