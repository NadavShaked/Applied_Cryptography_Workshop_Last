# Storage Portal

## Overview

The **Storage Portal** is a web-based GUI built with **React (Next.js)** that provides an intuitive interface for clients to interact with the **Storage Server**. It allows users to easily send requests to the storage system, manage their stored files, and monitor their storage subscriptions.

## Features

- **File Management:** Upload, download, and delete stored files.
- **Storage Subscription:** View and manage escrow-based file storage.
- **User-Friendly Interface:** Simplifies API interactions for clients.

## Running the Storage Portal

There are two ways to run the Storage Portal:

### 1. Run with Docker

You can run the Storage Portal using Docker, which ensures that all dependencies are correctly set up without requiring manual installation.

1. Build the Docker image from the current folder:

   ```sh
   docker build -t storage-portal .
   ```

2. Run the Docker container:

   ```sh
   docker run -p 3000:3000 storage-portal
   ```

The portal will be accessible at `http://127.0.0.1:3000/`.

### 2. Run Manually

If you prefer to run the Storage Portal manually, ensure you have the following installed:

- [Node.js](https://nodejs.org/) (version 18.17.1 or later)
- [npm](https://www.npmjs.com/) (version 9.6.7 or later)

From the current folder, execute the following commands:

1. Install dependencies:

   ```sh
   npm install
   ```

2. Start the development server:

   ```sh
   npm run dev
   ```

The portal will start at `http://localhost:3000/`.

## API Interaction

The Storage Portal communicates with the **Storage Server** API to perform file operations and validate subscriptions. Ensure that the **Storage Server** is running before using the portal.

By default, the portal expects the Storage Server to be available at `http://127.0.0.1:8000/`. If running in Docker, ensure network settings allow communication between the containers.
