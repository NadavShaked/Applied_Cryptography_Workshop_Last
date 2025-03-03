# PoR Application

## Overview

This project is a Python-based application that provides file encoding/decoding functionality and interacts with a Solana API Gateway server. The application enables users to encode files using Reed-Solomon error correction, followed by Proof of Retrievability (PoR) authentication, and allows interaction with a Solana Blockchain for menage escrow-based subscription buyer's instructions.

## Prerequisites

Before running this project, ensure you have the following installed:

- [Python 3.11](https://www.python.org/downloads/)
- Required dependencies from [`requirements.txt`](requirements.txt), install with:

```sh
pip install -r requirements.txt
```

## Running the Application

To start the PoR application, navigate to the [PoR application project folder](./) and execute the following command:

```sh
python app.py
```

## Configuration

To configure the Solana API Gateway URL, you need to update the `SOLANA_GATEWAY_BASE_URL` field in the [`solanaApiGatewayProvider.py`](./Common/Providers/solanaApiGatewayProvider.py) file.

1. Open the [`solanaApiGatewayProvider.py`](./Common/Providers/solanaApiGatewayProvider.py) file located in your project directory.
2. Find the line that defines the `SOLANA_GATEWAY_BASE_URL` variable.
3. Update the URL to point to your Solana API Gateway endpoint.

Example:

```py
SOLANA_GATEWAY_BASE_URL: str = "http://127.0.0.1:3030"
```

## Application Pages

### 1. Encoding Page

The encoding page allows users to encode a file using a two-step process:

- **Reed-Solomon Encoding:** Adds redundancy to the file for error correction.
- **PoR Authentication Blocks:** Further encodes the data into authentication blocks for Proof of Retrievability (PoR).

The output of this process includes:

- Elastic curve points (g, v, u) and x under Z<sub>p</sub>, which are essential for Proof of Retrievability (PoR) subscriptions.
- A Reed-Solomon encoded file that enhances data reliability.

**Steps:**

1. Select a file to encode.
2. Start the encoding process.
3. Save the encoded file.

### 2. Decoding Page

The decoding page performs the reverse operation of encoding:

- **PoR Block Stripping:** Strips PoR authentication blocks prior to file reconstruction.
- **Reed-Solomon Decoding:** Recovers the original file from error-corrected data.

**Steps:**

1. Select an encoded file.
2. Start the decoding process.
3. Retrieve the original file.

### 3. Solana API Interaction Page

This page enables users to send requests to a Solana API Gateway server for handling buyer-side operations in a storage subscription system. The user can interact with the escrow system to:

- **Start a Subscription**
- **Add Funds to a Subscription**
- **End a Subscription**
- **Request Funds from an Escrow**

**Steps:**

1. Enter the required details (private key, escrow public key, amount, etc.).
2. Select the desired API request.
3. Send the request to the Solana API Gateway.
4. View the response and transaction details.

The GUI will launch, allowing users to navigate between encoding, decoding, and Solana interaction pages.

## Additional Information

- The application allows seamless integration of file encoding/decoding and Solana-based subscription management.
- Ensure you have a valid Solana wallet and API Gateway server running to test Solana requests.
- For troubleshooting, refer to logs displayed in the application or console output.
