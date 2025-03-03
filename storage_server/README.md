# Storage Server

## Overview

The **Storage Server** is a Flask-based application that provides secure file storage, retrieval, validation, and corruption testing functionalities. It integrates with a **Solana API Gateway** to manage escrow-based storage subscriptions and ensures data integrity through **Proof of Retrievability (PoR)**.

## Features

### API

- **File Upload & Storage:** Securely upload and store files with metadata linked to escrow accounts.
- **File Download:** Retrieve stored files via API requests.
- **Proof of Retrievability (PoR) Calculation:** Compute and verify PoR values (`sigma` and `mu`) for data integrity validation.
- **File Corruption:** Simulate data corruption using Reed-Solomon encoding for error detection. This gave you the capability to test that the storage server cheat and don't store the buyer file as the subscription agreement.

### Job

- **Automated File Validation:** Periodic validation of stored files based on their escrow contract conditions.
- **Subscription & Fund Management:** Interacts with Solana's escrow accounts to validate and handle storage payments.

## Prerequisites

Before running the Storage Server, ensure you have the following installed:

- [Python 3.11](https://www.python.org/downloads/)
- Required dependencies from [`requirements.txt`](requirements.txt), install with:

```sh
pip install -r requirements.txt
```

## Curl Templates and Examples

Example `curl` requests for all endpoints are available in the [`./curls`](Curls) directory. You can use them to quickly test the API.

## API Endpoints

### 1. **File Upload**
- **Endpoint:** `/api/upload`
- **Method:** `POST`
- **Description:** Uploads a file and associates it with an escrow account.
- **Parameters:**
  - `file`: The file to upload.
  - `escrow_public_key`: The escrow account associated with the file.
- **Response:**
  ```json
  { "message": "File received and saved", "filename": "example.txt" }
  ```

### 2. **File Download**
- **Endpoint:** `/api/download`
- **Method:** `GET`
- **Description:** Downloads a stored file.
- **Parameters:**
  - `filename`: The name of the file to download.
- **Response:** The requested file as an attachment.

### 3. **Calculate and Prove (PoR Validation)**
- **Endpoint:** `/api/calculate_and_prove`
- **Method:** `GET`
- **Description:** Computes and validates the PoR values (`sigma` and `mu`) for the given file.
- **Parameters:**
  - `filename`: The file to validate.
- **Response:**
  ```json
  { "proved": true }
  ```

### 4. **File Corruption Simulation**
- **Endpoint:** `/api/corrupt`
- **Method:** `GET`
- **Description:** Corrupts a stored file to test error detection and recovery mechanisms.
- **Parameters:**
  - `filename`: The file to corrupt.
- **Response:**
  ```json
  { "message": "The file 'example.txt' corrupted." }
  ```
  
### 5. **Get Files**
- **Endpoint:** `/api/get_files`
- **Method:** `GET`
- **Description:** Retrieves a list of all stored files with their details such as escrow public key, validation frequency, and last verification date.
- **Response:**
```json
{
  "data": {
    "storageFiles": [
      {
        "id": 0,
        "file_name": "example.txt",
        "escrow_public_key": "escrow_pubkey_here",
        "validate_every": "30 days",
        "last_verify": "2025-03-03T12:00:00"
      },
      ...
    ]
  }
}
```

### 6. **Delete File**
- **Endpoint:** `/api/delete_file`
- **Method:** `GET`
- **Description:** Deletes a specific file from the storage. Requires a query parameter filename.
- **Parameters:**
  - `filename`: The name of the file to delete.
- **Response:**
```json
{ "message": "Deletion succeeded" }
```

## Automated Validation System

The Storage Server periodically validates stored files based on escrow contract conditions. The process follows these steps:

1. Check if the file needs validation based on `validate_every` interval.
2. Retrieve the escrow details and check the storage subscription status.
3. If the storage subscription has ended, attempt to withdraw funds and delete the file.
4. If the storage subscription is active, ensure there are sufficient funds for validation.
5. Perform PoR validation (calculate `sigma` and `mu`) and update the last verification timestamp.

## Running the Storage Server

There are two ways to run the Storage Server:

### 1. Run with Docker

you can run the Storage Server via Docker. This option eliminates the need to install Python and dependencies manually. To do so:

1. Build the Docker image:

```sh
docker build -t storage-server .
```

2. Run the Docker container:

```sh
docker run -p 8000:8000 storage-server
```

### 2. Run Manually

To run the server manually, follow these steps:

1. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

2. Run the server:
   ```sh
   python -m flask run
   ```

The server will start at `http://127.0.0.1:8000/`

## Updating the Solana Gateway URL

In order to properly configure the Solana API Gateway URL, it is important to update the `SOLANA_GATEWAY_BASE_URL` in the [`solanaApiGatewayProvider.py`](../Common/Providers/solanaApiGatewayProvider.py) file.

For running in **Docker**, use the following URL instead:
```sh
SOLANA_GATEWAY_BASE_URL: str = "http://host.docker.internal:3030"
```

For running **locally**, update the URL to:
```sh
SOLANA_GATEWAY_BASE_URL: str = "http://host.docker.internal:3030"
```

Ensure that you update this field correctly depending on whether you are running the application locally or inside a Docker container.

## Scheduled Job & Cleanup

The server includes a background job that periodically validates files. On shutdown, it performs cleanup tasks:

- Ends subscriptions for stored files.
- Shuts down the job gracefully.
