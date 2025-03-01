# Solana Explorer (Forked master - 602219b72b612582d7c1614631c06e4443522ca5)

Solana Explorer is a **GUI** (Graphical User Interface) that allows you to view Solana transactions and accounts, similar to the original Solana Portal. This tool helps you explore the Solana blockchain and monitor activities in real time.

In this setup, the Solana Explorer is configured to connect to a local Solana test validator, by setting the Solana server URL to `localhost:8899`.

## Pre-requisites

Before running the Solana Explorer locally, ensure that you have the following installed:

pnpm of version 9.10.0

```sh
npm install -g pnpm@9.10.0
```

## Setup and Running Solana Explorer Locally

Follow these steps to set up and run the Solana Explorer on your local machine:

### 1. Clone the Repository

navigate to the Solana Explorer project folder using the following command:

```sh
cd solana_explorer
```

### 2. Install Dependencies

install the necessary dependencies using `pnpm`:

```sh
pnpm install
```

### 3. Run the Solana Explorer

After installing the dependencies and setting the correct Solana server URL, you can run the Solana Explorer locally on your machine by using the following command:

```sh
pnpm run dev -p 3090
```

This will start the Solana Explorer on `http://localhost:3930`.

### 5. Access the Explorer

Once the application is running, you can open your browser and navigate to:

```sh
http://localhost:3090
```

You should now be able to view the Solana transactions and accounts via the Solana Explorer.

---

## Notes:

- This Solana Explorer is similar to the original Solana Portal, but with a local setup to interact with your Solana test validator (`localhost:8899`).

- Make sure your local Solana test validator is running on `localhost:8899` before starting the Explorer, or the Explorer won't be able to fetch the blockchain data.

## Original Forked Repository

For more details about the original Solana Explorer repository, check out the official README:

🔗 [Solana Explorer GitHub Repository](./solana_explorer/README.md)

🔗 [Original Solana Explorer GitHub Repository](https://github.com/solana-foundation/explorera)
