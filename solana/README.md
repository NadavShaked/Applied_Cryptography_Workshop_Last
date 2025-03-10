# Solana Rust Example

This repository contains an example Solana program and client, both in rust, as well as a docker-compose configuration to run the solana toolchain and local validator.

The code for the example is from the [Anchor Rust Client Example](https://www.anchor-lang.com/docs/clients/rust).

## Running the Example

1. Clone this repository

2. In the repository root, run
   
       docker compose build
       docker compose up -d
   
   This will create a docker container running the Solana test validator, and start it running.

3. Run a shell in the docker container:
   
       docker compose exec solana bash

4. Set up a local Solana wallet and request an airdrop (in the container):
   
       solana config set -ul
       solana-keygen new
       solana airdrop 10

5. Build example `hello` program (in the container):
   
       cd data/hello
       anchor build

6. Replace the id in the anchor program with the correct ID:
   a. Run (in the container)
   
       anchor keys list
   
      To get the correct key for the `hello` program.
   
   b. Edit the file `data/hello/programs/hello/src/lib.rs` and replace the id in `declare_id!("...")` with the correct id.
   c. Edit the file `data/hello/Anchor.toml` and replace the id under the `[programs.localnet]` key with the correct id. 

7. Rebuild with the correct id and deploy (in the container):
   
       anchor build

8. Build and execute the example `client` program (in the container):
   
       cd ../client
       cargo build
       cargo run

9. Celebrate!   
