use anchor_client::{
    solana_client::rpc_client::RpcClient,
    solana_sdk::{
        commitment_config::CommitmentConfig, native_token::LAMPORTS_PER_SOL, signature::Keypair,
        signer::Signer, system_program, 
    },
    // solana_sdk::{ compute_budget::ComputeBudgetInstruction, },
    Client, Cluster,
    solana_client::rpc_config::RpcSendTransactionConfig,
    
};
use solana_logger;
// use solana_rpc_client_api::config::RpcSendTransactionConfig;
use anchor_lang::prelude::*;
use std::rc::Rc;
use rand_core::OsRng;

use bls12_381::{G1Affine, G1Projective};
use group::Group;



declare_program!(hello);
use hello::{accounts::Counter, client::accounts, client::args};
 
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    solana_logger::setup();

    msg!("testing!");

    let connection = RpcClient::new_with_commitment(
        "http://127.0.0.1:8899", // Local validator URL
        CommitmentConfig::confirmed(),
    );
 
    // Generate Keypairs and request airdrop
    let payer = Keypair::new();
    let counter = Keypair::new();
    println!("Generated Keypairs:");
    println!("   Payer: {}", payer.pubkey());
    println!("   Counter: {}", counter.pubkey());
 
    println!("\nRequesting xxx SOL airdrop to payer");
    let airdrop_signature = connection.request_airdrop(&payer.pubkey(), 50_000*LAMPORTS_PER_SOL)?;
 
    // Wait for airdrop confirmation
    while !connection.confirm_transaction(&airdrop_signature)? {
        std::thread::sleep(std::time::Duration::from_millis(100));
    }
    println!("   Airdrop confirmed!");
 
    // Create program client
    let provider = Client::new_with_options(
        Cluster::Localnet,
        Rc::new(payer),
        CommitmentConfig::confirmed(),
    );
    let program = provider.program(hello::ID)?;
    println!("\nUsing program Id {}", hello::ID);

    // Build and send instructions
    println!("\nSend transaction with initialize and do_pairing instructions");
    let initialize_ix = program
        .request()
        .accounts(accounts::Initialize {
            counter: counter.pubkey(),
            payer: program.payer(),
            system_program: system_program::ID,
        })
        .args(args::Initialize)
        .instructions()?
        .remove(0);
 

    // Commented out below (not necessary once we set the new compute limit in the test validator command-line)

    // let increase_compute_units_ix = ComputeBudgetInstruction::set_compute_unit_limit(40_000_000);
    // let decrease_compute_price_ix = ComputeBudgetInstruction::set_compute_unit_price(1);
    // let increase_heap_size_ix = ComputeBudgetInstruction::request_heap_frame(1024*128);

    // Get an RNG:
    
    let x = <G1Projective as Group>::random(OsRng);
    let xbytes = G1Affine::from(x).to_compressed();

    println!("x: {}", G1Affine::from(x));

    let do_pairing_ix = program
        .request()
        .accounts(accounts::DoPairing {
            counter: counter.pubkey(),
        })
        .args(args::DoPairing {
            x_serialized: xbytes,
        })
        .instructions()?
        .remove(0);
 
    let config = RpcSendTransactionConfig {
        skip_preflight: true,
        .. RpcSendTransactionConfig::default()
    };
    let signature = program
        .request()
        .instruction(initialize_ix)
        // .instruction(increase_compute_units_ix)
        // .instruction(decrease_compute_price_ix)
        // .instruction(increase_heap_size_ix)
        .instruction(do_pairing_ix)
        .signer(&counter)
        .send_with_spinner_and_config(config) // Skip preflight checks so that we can see log messages on validator
        // .send()
        .await?;
    println!("   Transaction confirmed: {}", signature);
 
    println!("\nFetch counter account data");
    let counter_account: Counter = program.account::<Counter>(counter.pubkey()).await?;
    println!("   Counter value: {}", counter_account.count);
    Ok(())
}