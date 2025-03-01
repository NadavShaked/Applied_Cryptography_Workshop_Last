// Solana SDK Imports
use solana_client::{rpc_client::RpcClient, client_error::ClientError};
use solana_sdk::{
    instruction::{Instruction, AccountMeta},
    signature::{Keypair, Signer},
    transaction::Transaction,
    program_pack::Pack,
    pubkey::Pubkey,
    system_program,
    compute_budget::ComputeBudgetInstruction,
};

// BLS Imports
use bls12_381::{pairing, G1Affine, G2Affine, G1Projective, Scalar};
use bls12_381::hash_to_curve::{ExpandMsgXmd, HashToCurve, HashToField};

// Anchor Imports
use anchor_lang::{AccountDeserialize, InstructionData};
use anchor_lang::solana_program::sysvar;

// Project-Specific Imports
use escrow_project::{
    Escrow,
    instruction::{AddFundsToSubscription, StartSubscription, ProveSubscription, ProveSubscriptionSimulation, EndSubscriptionByBuyer, EndSubscriptionBySeller, RequestFund, GenerateQueries},
};

// Serde Imports
use serde::{Deserialize, Serialize, Serializer, Deserializer};
use serde::de::{Error as DeError};

// Miscellaneous Imports
use std::str::FromStr;
use std::time::{SystemTime, UNIX_EPOCH};
use std::ops::Mul;

// Warp Imports
use warp::{Filter, reject::Reject};

// SHA2 Imports
use sha2::{Digest, Sha256};


const PROGRAM_ID: &str = "5LthHd6oNK3QkTwC59pnn1tPFK7JJUgNjNnEptxxXSei";

const DEV_RPC_URL: &str = "https://api.localnet.solana.com";
const LOCAL_RPC_URL: &str = "http://127.0.0.1:8899";


#[derive(Debug)]
struct HexArray<const N: usize>([u8; N]);

impl<const N: usize> Serialize for HexArray<N> {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        serializer.serialize_str(&hex::encode(self.0))
    }
}

impl<'de, const N: usize> Deserialize<'de> for HexArray<N> {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let s: &str = Deserialize::deserialize(deserializer)?;
        let bytes = hex::decode(s).map_err(DeError::custom)?;
        if bytes.len() != N {
            return Err(DeError::custom(format!(
                "Invalid length: expected {} bytes, got {} bytes",
                N,
                bytes.len()
            )));
        }
        let mut array = [0u8; N];
        array.copy_from_slice(&bytes);
        Ok(HexArray(array))
    }
}

mod hex_array_96 {
    use serde::{Deserialize, Serialize};
    use super::HexArray;

    pub fn serialize<S>(value: &[u8; 96], serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        HexArray(*value).serialize(serializer)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<[u8; 96], D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let array = HexArray::<96>::deserialize(deserializer)?;
        Ok(array.0)
    }
}

mod hex_array_48 {
    use serde::{Deserialize, Serialize};
    use super::HexArray;

    pub fn serialize<S>(value: &[u8; 48], serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        HexArray(*value).serialize(serializer)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<[u8; 48], D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let array = HexArray::<48>::deserialize(deserializer)?;
        Ok(array.0)
    }
}

mod hex_array_32 {
    use serde::{Deserialize, Serialize};
    use super::HexArray;

    pub fn serialize<S>(value: &[u8; 32], serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        HexArray(*value).serialize(serializer)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<[u8; 32], D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let array = HexArray::<32>::deserialize(deserializer)?;
        Ok(array.0)
    }
}

#[derive(Debug)]
struct CustomClientError(ClientError);

impl Reject for CustomClientError {}

#[derive(Serialize, Deserialize, Debug)]
struct StartSubscriptionRequest {
    /// The size of the query in bytes.
    query_size: u64,

    /// The duration of the subscription, measured in number of Solana blocks.
    number_of_blocks: u64,

    /// A 48-byte cryptographic value (`u`), serialized as a hex string.
    #[serde(with = "hex_array_48")]
    u: [u8; 48],

    /// A 96-byte cryptographic value (`g`), serialized as a hex string.
    #[serde(with = "hex_array_96")]
    g: [u8; 96],

    /// A 96-byte cryptographic value (`v`), serialized as a hex string.
    #[serde(with = "hex_array_96")]
    v: [u8; 96],

    /// The interval (in blocks) at which subscription validation should occur.
    validate_every: i64,

    /// The buyer's private key, encoded as a Base58 string.
    buyer_private_key: String,

    /// The seller's public key, encoded as a Base58 string.
    seller_pubkey: String,
}

#[derive(Serialize, Deserialize)]
struct AddFundsToSubscriptionRequest {
    /// Buyer's private key (Base58 encoded) used to authorize the transaction.
    buyer_private_key: String,

    /// Public key of the escrow account (Base58 encoded).
    escrow_pubkey: String,

    /// Amount (in lamports) to add to the subscription.
    amount: u64,
}

#[derive(Serialize, Deserialize, Debug)]
struct ProveRequest {
    seller_private_key: String,
    escrow_pubkey: String,
    #[serde(with = "hex_array_48")]
    sigma: [u8; 48],
    #[serde(with = "hex_array_32")]
    mu: [u8; 32],
}

#[derive(Serialize, Deserialize)]
struct EndSubscriptionByBuyerRequest {
    /// Buyer's private key (Base58 encoded) used to authorize the transaction.
    buyer_private_key: String,

    /// Public key of the escrow account (Base58 encoded).
    escrow_pubkey: String,
}

#[derive(Serialize, Deserialize)]
struct EndSubscriptionBySellerRequest {
    /// Seller's private key (Base58 encoded) used to authorize the transaction.
    seller_private_key: String,

    /// Public key of the escrow account (Base58 encoded).
    escrow_pubkey: String,
}

#[derive(Serialize, Deserialize)]
struct RequestFundsRequest {
    /// The private key of the user (either buyer or seller), used as a signer for the transaction.
    /// Private key (Base58 encoded) used to authorize the transaction.
    user_private_key: String,

    /// Public key of the escrow account (Base58 encoded).
    escrow_pubkey: String,
}

#[derive(Serialize, Deserialize)]
struct GenerateQueriesRequest {
    /// Public key of the escrow account (Base58 encoded).
    escrow_pubkey: String,

    /// Private key (Base58 encoded) used to authorize the transaction.
    user_private_key: String,
}

#[derive(Serialize, Deserialize)]
struct GetQueriesByEscrowRequest {
    /// Public key of the escrow account (Base58 encoded).
    escrow_pubkey: String,
}

#[derive(Serialize, Deserialize)]
struct GetEscrowDataRequest {
    /// Public key of the escrow account (Base58 encoded).
    escrow_pubkey: String,
}

#[derive(Serialize, Deserialize)]
struct StartSubscriptionResponse {
    /// Public key of the escrow account (Base58 encoded).
    escrow_pubkey: String,

    /// Subscription ID of escrow account (Base58 encoded).
    subscription_id: u64,
}

#[derive(Serialize, Deserialize)]
struct ExtendSubscriptionResponse {
    message: String,
}

#[derive(Serialize, Deserialize)]
struct ProveResponse {
    message: String,
}

#[derive(Serialize, Deserialize)]
struct GetQueriesByEscrowPubkeyResponse {
    queries: Vec<(u128, String)>, //(block index, v_i)
}

#[derive(Serialize, Deserialize)]
struct GetEscrowDataResponse {
    buyer_pubkey: String,
    seller_pubkey: String,

    u: String,
    g: String,
    v: String,

    number_of_blocks: u64,
    query_size: u64,
    validate_every: i64,
    last_prove_date: i64,
    balance: u64,

    queries: Vec<(u128, String)>, //(block index, v_i)
    queries_generation_time: i64,

    is_subscription_ended_by_buyer: bool,
    is_subscription_ended_by_seller: bool,

    subscription_duration: u64,
    subscription_id: u64,
}

#[tokio::main]
async fn main() {
    let start_subscription = warp::post()
        .and(warp::path("start_subscription"))
        .and(warp::body::json())
        .and_then(start_subscription_handler);
    
    let add_funds_to_subscription = warp::post()
        .and(warp::path("add_funds_to_subscription"))
        .and(warp::body::json())
        .and_then(add_funds_to_subscription_handler);

    let prove = warp::post()
        .and(warp::path("prove"))
        .and(warp::body::json())
        .and_then(prove_handler);

    let prove_simulation = warp::post()
        .and(warp::path("prove_simulation"))
        .and(warp::body::json())
        .and_then(prove_simulation_handler);

    let end_sub_by_buyer = warp::post()
        .and(warp::path("end_subscription_by_buyer"))
        .and(warp::body::json())
        .and_then(end_subscription_by_buyer_handler);

    let end_sub_by_seller = warp::post()
        .and(warp::path("end_subscription_by_seller"))
        .and(warp::body::json())
        .and_then(end_subscription_by_seller_handler);
    
    let generate_queries = warp::post()
        .and(warp::path("generate_queries"))
        .and(warp::body::json())
        .and_then(generate_queries_handler);

    let request_funds = warp::post()
        .and(warp::path("request_funds"))
        .and(warp::body::json())
        .and_then(request_funds_handler);

    let get_queries_by_escrow = warp::post()
        .and(warp::path("get_queries_by_escrow"))
        .and(warp::body::json())
        .and_then(get_queries_by_escrow_handler);

    let get_escrow_data = warp::post()
        .and(warp::path("get_escrow_data"))
        .and(warp::body::json())
        .and_then(get_escrow_data_handler);

    let routes = start_subscription
        .or(add_funds_to_subscription)
        .or(prove)
        .or(prove_simulation)
        .or(end_sub_by_buyer)
        .or(end_sub_by_seller)
        .or(generate_queries)
        .or(request_funds)
        .or(get_queries_by_escrow)
        .or(get_escrow_data);

    println!("Server running at http://127.0.0.1:3030/");
    warp::serve(routes).run(([127, 0, 0, 1], 3030)).await;
}

/// Handles the initiation of a subscription on the Solana blockchain.
///
/// This function:
/// - Parses the buyer's private key and seller's public key.
/// - Generates a unique subscription ID.
/// - Derives the escrow Program Derived Address (PDA).
/// - Constructs a Solana transaction to start the subscription.
/// - Signs and sends the transaction to the blockchain.
/// - Returns the subscription ID and escrow public key on success, or an error if the transaction fails.
///
/// # Arguments
/// - `request`: A `StartSubscriptionRequest` containing buyer's private key, seller's public key,
///   query size, number of blocks, and other subscription parameters.
///
/// # Returns
/// - `Ok(impl warp::Reply)`: A JSON response with the subscription ID and escrow public key on success.
/// - `Err(warp::Rejection)`: A rejection in case of failure.
async fn start_subscription_handler(request: StartSubscriptionRequest) -> Result<impl warp::Reply, warp::Rejection> {
    println!("Starting subscription handler...");

    let rpc_client = RpcClient::new(LOCAL_RPC_URL.to_string());
    let program_id = Pubkey::from_str(PROGRAM_ID).unwrap();

    // Parse buyer's private key
    let buyer_keypair = Keypair::from_base58_string(&request.buyer_private_key);
    let buyer_pubkey = buyer_keypair.pubkey();
    println!("Buyer public key: {}", buyer_pubkey);

    // Parse seller's public key
    let seller_pubkey = Pubkey::from_str(&request.seller_pubkey).unwrap();
    println!("Seller public key: {}", seller_pubkey);

    // Generate a unique subscription ID
    let subscription_id = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
    println!("Generated subscription ID: {}", subscription_id);

    // Derive the escrow PDA (Program Derived Address)
    let (escrow_pda, bump) = Pubkey::find_program_address(&[
        b"escrow",
        buyer_pubkey.as_ref(),
        seller_pubkey.as_ref(),
        &subscription_id.to_le_bytes()
    ], &program_id);
    println!("Escrow PDA: {}", escrow_pda);

    // Construct the transaction instruction
    let instruction = Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(escrow_pda, false), // Escrow PDA
            AccountMeta::new(buyer_pubkey, true), // Buyer account (signer)
            AccountMeta::new(seller_pubkey, false), // Seller account
            AccountMeta::new_readonly(system_program::ID, false), // System program
        ],
        data: StartSubscription {
            subscription_id,
            query_size: request.query_size,
            number_of_blocks: request.number_of_blocks,
            g: request.g,
            v: request.v,
            u: request.u,
            validate_every: request.validate_every,
        }.data(),
    };
    println!("Instruction created successfully");

    // Fetch latest blockhash
    let blockhash = rpc_client.get_latest_blockhash().unwrap();
    println!("Latest blockhash: {:?}", blockhash);

    // Create a signed transaction
    let tx = Transaction::new_signed_with_payer(
        &[instruction],
        Some(&buyer_pubkey),
        &[&buyer_keypair],
        blockhash,
    );
    println!("Transaction created successfully");

    // Send and confirm the transaction
    match rpc_client.send_and_confirm_transaction(&tx) {
        Ok(_) => {
            println!("Transaction sent successfully!");
            Ok(warp::reply::json(&StartSubscriptionResponse {
                subscription_id,
                escrow_pubkey: escrow_pda.to_string()
            }))
        },
        Err(err) => {
            println!("Transaction failed: {:?}", err);
            Err(warp::reject::custom(CustomClientError(err)))
        }
    }
}

/// Handles adding funds to an existing subscription.
///
/// This function:
/// - Parses the buyer's private key and escrow account public key.
/// - Constructs a transaction to add funds to the subscription.
/// - Signs and sends the transaction to the blockchain.
/// - Returns a success message upon successful transaction execution.
///
/// # Arguments
/// - `request`: An `AddFundsToSubscriptionRequest` containing:
///   - Buyer's private key (Base58 encoded).
///   - Escrow account public key.
///   - Amount to add to the subscription.
///
/// # Returns
/// - `Ok(impl warp::Reply)`: A JSON response confirming the extension.
/// - `Err(warp::Rejection)`: A rejection in case of transaction failure.
async fn add_funds_to_subscription_handler(request: AddFundsToSubscriptionRequest) -> Result<impl warp::Reply, warp::Rejection> {
    println!("Starting add funds to subscription handler...");

    let rpc_client = RpcClient::new(LOCAL_RPC_URL.to_string());
    let program_id = Pubkey::from_str(PROGRAM_ID).unwrap();

    // Parse the buyer's private key and extract the public key
    let buyer_keypair = Keypair::from_base58_string(&request.buyer_private_key);
    let buyer_pubkey = buyer_keypair.pubkey();
    println!("Buyer public key: {}", buyer_pubkey);

    // Parse the escrow account public key
    let escrow_pubkey = Pubkey::from_str(&request.escrow_pubkey).unwrap();
    println!("Escrow public key: {}", escrow_pubkey);

    // Construct the transaction instruction for adding funds
    let instruction = Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(escrow_pubkey, false), // Escrow account
            AccountMeta::new(buyer_pubkey, true), // Buyer account (signer)
            AccountMeta::new_readonly(system_program::ID, false), // System program
        ],
        data: AddFundsToSubscription {
            amount: request.amount,
        }.data(),
    };
    println!("Instruction for adding funds created successfully");

    // Fetch latest blockhash
    let blockhash = rpc_client.get_latest_blockhash().unwrap();
    println!("Latest blockhash: {:?}", blockhash);

    // Create a signed transaction
    let tx = Transaction::new_signed_with_payer(
        &[instruction],
        Some(&buyer_pubkey),
        &[&buyer_keypair],
        blockhash,
    );
    println!("Transaction created successfully");

    // Send and confirm the transaction
    match rpc_client.send_and_confirm_transaction(&tx) {
        Ok(_) => {
            println!("Transaction sent successfully!");
            Ok(warp::reply::json(&ExtendSubscriptionResponse {
                message: "Subscription extended successfully".to_string()
            }))
        },
        Err(err) => {
            println!("Transaction failed: {:?}", err);
            Err(warp::reject::custom(CustomClientError(err)))
        }
    }
}

/// Handles proving a subscription with the seller's proof.
///
/// This function:
/// - Parses the seller's private key and escrow account public key.
/// - Constructs the instruction for proving the subscription with the provided `sigma` and `mu` values.
/// - Increases compute unit limits and adjusts compute unit price to handle expensive BLS pairing operation (note: due to CU limits, this might fail).
/// - Signs and sends the transaction to the blockchain.
/// - Returns a success message upon successful transaction execution or an error if the transaction fails.
///
/// # Arguments
/// - `request`: A `ProveRequest` containing:
///   - Seller's private key (Base58 encoded).
///   - Escrow account public key.
///   - `sigma` and `mu` values for the proof.
///
/// # Returns
/// - `Ok(impl warp::Reply)`: A JSON response confirming the proof submission.
/// - `Err(warp::Rejection)`: A rejection in case of transaction failure.
async fn prove_handler(request: ProveRequest) -> Result<impl warp::Reply, warp::Rejection> {
    println!("Starting prove subscription handler...");

    let rpc_client = RpcClient::new(LOCAL_RPC_URL.to_string());
    let program_id = Pubkey::from_str(PROGRAM_ID).unwrap();

    // Parse the seller's private key and extract the public key
    let seller_keypair = Keypair::from_base58_string(&request.seller_private_key);
    let seller_pubkey = seller_keypair.pubkey();
    println!("Seller public key: {}", seller_pubkey);

    // Parse the escrow account public key
    let escrow_pubkey = Pubkey::from_str(&request.escrow_pubkey).unwrap();
    println!("Escrow public key: {}", escrow_pubkey);

    // Construct the transaction instruction for proving the subscription
    let instruction = Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(escrow_pubkey, false), // Escrow account
            AccountMeta::new(seller_pubkey, true),  // Seller account (signer)
        ],
        data: ProveSubscription {
            sigma: request.sigma,
            mu: request.mu,
        }
            .data(),
    };
    println!("Instruction for proving subscription created successfully");

    // Increase compute unit limit and set compute unit price to handle BLS pairing
    let increase_compute_units_ix = ComputeBudgetInstruction::set_compute_unit_limit(u32::MAX);
    let increase_compute_price_ix = ComputeBudgetInstruction::set_compute_unit_price(5);
    println!("Compute unit limit increased and price adjusted");

    // Fetch latest blockhash
    let blockhash = rpc_client.get_latest_blockhash().unwrap();
    println!("Latest blockhash: {:?}", blockhash);

    // Create a signed transaction
    let tx = Transaction::new_signed_with_payer(
        &[increase_compute_units_ix, increase_compute_price_ix, instruction],
        Some(&seller_pubkey),
        &[&seller_keypair],
        blockhash,
    );
    println!("Transaction created successfully");

    match rpc_client.send_and_confirm_transaction(&tx) {
        Ok(_) => {
            println!("Transaction sent successfully!");
            Ok(warp::reply::json(&ProveResponse {
                message: "Proof submitted successfully".to_string()
            }))
        },
        Err(err) => {
            println!("Transaction failed: {:?}", err);
            Err(warp::reject::custom(CustomClientError(err)))
        }
    }
}

/// Handles simulating the proof verification for a subscription due to compute unit limitations.
///
/// This function:
/// - Parses the seller's private key and escrow account public key.
/// - Retrieves and deserializes the escrow account data.
/// - Validates the proof (`sigma` and `mu`) using elliptic curve operations off-chain.
/// - Simulates the proof verification by sending a pre-verified result (`is_verified`) to the blockchain.
/// - Signs and sends the transaction to the blockchain.
/// - Returns a success message upon successful transaction execution or an error if the transaction fails.
///
/// # Arguments
/// - `request`: A `ProveRequest` containing:
///   - Seller's private key (Base58 encoded).
///   - Escrow account public key.
///   - `sigma` and `mu` values for the proof.
///
/// # Returns
/// - `Ok(impl warp::Reply)`: A JSON response confirming the proof submission.
/// - `Err(warp::Rejection)`: A rejection in case of transaction failure.
async fn prove_simulation_handler(request: ProveRequest) -> Result<impl warp::Reply, warp::Rejection> {
    println!("Starting prove simulation handler...");

    let rpc_client = RpcClient::new(LOCAL_RPC_URL.to_string());
    let program_id = Pubkey::from_str(PROGRAM_ID).unwrap();

    // Parse the seller's private key and extract the public key
    let seller_keypair = Keypair::from_base58_string(&request.seller_private_key);
    let seller_pubkey = seller_keypair.pubkey();
    println!("Seller public key: {}", seller_pubkey);

    // Parse the escrow account public key
    let escrow_pubkey = Pubkey::from_str(&request.escrow_pubkey).unwrap();
    println!("Escrow public key: {}", escrow_pubkey);

    // Retrieve and deserialize the escrow account data
    let account_data = rpc_client.get_account_data(&escrow_pubkey).unwrap();
    let escrow_account = Escrow::try_deserialize(&mut &account_data[..]).unwrap();
    println!("Escrow account data successfully retrieved and deserialized");

    // Deserialize the elliptic curve points
    let g_norm = G2Affine::from_compressed(&escrow_account.g).unwrap();
    let v_norm = G2Affine::from_compressed(&escrow_account.v).unwrap();
    let u = G1Affine::from_compressed(&escrow_account.u).unwrap();
    println!("Elliptic curve points deserialized successfully");

    // Reverse endianness for the mu value and compute the scalar
    let mu_in_little_endian: [u8; 32] = reverse_endianness(request.mu);
    let mu_scalar = Scalar::from_bytes(&mu_in_little_endian).unwrap();
    println!("Mu value processed");

    // Deserialize sigma
    let sigma = G1Affine::from_compressed(&request.sigma).unwrap();
    println!("Sigma value deserialized");

    // Compute the multiplicative sums for validation
    let queries = escrow_account.queries;
    let all_h_i_multiply_vi = compute_h_i_multiply_vi(queries);
    let u_multiply_mu = u.mul(mu_scalar);
    let multiplication_sum = all_h_i_multiply_vi.add(&u_multiply_mu);
    let multiplication_sum_affine = G1Affine::from(multiplication_sum);
    println!("Multiplicative sums calculated");

    // Compute pairings for validation
    let right_pairing = pairing(&multiplication_sum_affine, &v_norm);
    let left_pairing = pairing(&sigma, &g_norm);
    let is_verified = left_pairing.eq(&right_pairing);
    println!("Proof verification result: {}", is_verified);

    // Construct the instruction to simulate the proof validation
    let instruction = Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(escrow_pubkey, false), // Escrow account
            AccountMeta::new(seller_pubkey, true),  // Seller account (signer)
        ],
        data: ProveSubscriptionSimulation {
            is_verified: is_verified    // Send the simulated result
        }
            .data(),
    };
    println!("Instruction for proof simulation created successfully");

    // Fetch latest blockhash
    let blockhash = rpc_client.get_latest_blockhash().unwrap();
    println!("Latest blockhash: {:?}", blockhash);

    // Create a signed transaction
    let tx = Transaction::new_signed_with_payer(
        &[instruction],
        Some(&seller_pubkey),
        &[&seller_keypair],
        blockhash,
    );
    println!("Transaction created successfully");

    // Send and confirm the transaction
    match rpc_client.send_and_confirm_transaction(&tx) {
        Ok(_) => {
            println!("Transaction sent successfully!");
            Ok(warp::reply::json(&ProveResponse { message: "Proof submitted successfully".to_string() }))
        },
        Err(err) => {
            println!("Transaction failed: {:?}", err);
            Err(warp::reject::custom(CustomClientError(err)))
        }
    }
}

/// Handles the request to end a subscription by the buyer.
///
/// This function:
/// - Parses the buyer's private key and escrow account public key.
/// - Constructs a transaction to end the subscription by the buyer.
/// - Signs and sends the transaction to the blockchain.
/// - Returns a success message if the transaction is successful.
///
/// # Arguments
/// - `request`: An `EndSubscriptionByBuyerRequest` containing:
///   - Buyer's private key (Base58 encoded).
///   - Escrow account public key.
///
/// # Returns
/// - `Ok(impl warp::Reply)`: A JSON response confirming the subscription has ended.
/// - `Err(warp::Rejection)`: A rejection in case of transaction failure.
async fn end_subscription_by_buyer_handler(request: EndSubscriptionByBuyerRequest) -> Result<impl warp::Reply, warp::Rejection> {
    println!("Starting end subscription by buyer handler...");

    let rpc_client = RpcClient::new(LOCAL_RPC_URL.to_string());
    let program_id = Pubkey::from_str(PROGRAM_ID).unwrap();

    // Parse the buyer's private key and extract the public key
    let buyer_keypair = Keypair::from_base58_string(&request.buyer_private_key);
    let buyer_pubkey = buyer_keypair.pubkey();
    println!("Buyer public key: {}", buyer_pubkey);

    // Parse the escrow account public key
    let escrow_pubkey = Pubkey::from_str(&request.escrow_pubkey).unwrap();
    println!("Escrow public key: {}", escrow_pubkey);

    // Construct the transaction instruction for ending the subscription
    let instruction = Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(escrow_pubkey, false), // Escrow account
            AccountMeta::new(buyer_pubkey, true), // Buyer account (signer)
            // AccountMeta::new_readonly(system_program::ID, false), // Uncomment if system program needed
        ],
        data: EndSubscriptionByBuyer {}.data(),
    };
    println!("Instruction for ending subscription created successfully");

    // Fetch latest blockhash
    let blockhash = rpc_client.get_latest_blockhash().unwrap();
    println!("Latest blockhash: {:?}", blockhash);

    // Create a signed transaction
    let tx = Transaction::new_signed_with_payer(
        &[instruction],
        Some(&buyer_pubkey),
        &[&buyer_keypair],
        blockhash,
    );
    println!("Transaction created successfully");

    // Send and confirm the transaction
    match rpc_client.send_and_confirm_transaction(&tx) {
        Ok(_) => {
            println!("Transaction sent successfully!");
            Ok(warp::reply::json(&ExtendSubscriptionResponse {
                message: "Subscription ended successfully by buyer".to_string()
            }))
        },
        Err(err) => {
            println!("Transaction failed: {:?}", err);
            Err(warp::reject::custom(CustomClientError(err)))
        }
    }
}

/// Handles the request to end a subscription by the seller.
///
/// This function:
/// - Parses the seller's private key and escrow account public key.
/// - Constructs a transaction to end the subscription by the seller.
/// - Signs and sends the transaction to the blockchain.
/// - Returns a success message if the transaction is successful.
///
/// # Arguments
/// - `request`: An `EndSubscriptionBySellerRequest` containing:
///   - Seller's private key (Base58 encoded).
///   - Escrow account public key.
///
/// # Returns
/// - `Ok(impl warp::Reply)`: A JSON response confirming the subscription has ended.
/// - `Err(warp::Rejection)`: A rejection in case of transaction failure.
async fn end_subscription_by_seller_handler(request: EndSubscriptionBySellerRequest) -> Result<impl warp::Reply, warp::Rejection> {
    println!("Starting end subscription by seller handler...");

    let rpc_client = RpcClient::new(LOCAL_RPC_URL.to_string());
    let program_id = Pubkey::from_str(PROGRAM_ID).unwrap();

    // Parse the seller's private key and extract the public key
    let seller_keypair = Keypair::from_base58_string(&request.seller_private_key);
    let seller_pubkey = seller_keypair.pubkey();
    println!("Seller public key: {}", seller_pubkey);

    // Parse the escrow account public key
    let escrow_pubkey = Pubkey::from_str(&request.escrow_pubkey).unwrap();
    println!("Escrow public key: {}", escrow_pubkey);

    // Construct the transaction instruction for ending the subscription
    let instruction = Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(escrow_pubkey, false), // Escrow account
            AccountMeta::new(seller_pubkey, true), // Seller account (signer)
        ],
        data: EndSubscriptionBySeller {}.data(),
    };
    println!("Instruction for ending subscription created successfully");

    // Fetch latest blockhash
    let blockhash = rpc_client.get_latest_blockhash().unwrap();
    println!("Latest blockhash: {:?}", blockhash);

    // Create a signed transaction
    let tx = Transaction::new_signed_with_payer(
        &[instruction],
        Some(&seller_pubkey),
        &[&seller_keypair],
        blockhash,
    );
    println!("Transaction created successfully");

    // Send and confirm the transaction
    match rpc_client.send_and_confirm_transaction(&tx) {
        Ok(_) => {
            println!("Transaction sent successfully!");
            Ok(warp::reply::json(&ExtendSubscriptionResponse {
                message: "Subscription ended successfully by seller".to_string()
            }))
        },
        Err(err) => {
            println!("Transaction failed: {:?}", err);
            Err(warp::reject::custom(CustomClientError(err)))
        }
    }
}

/// Handles the request to request funds from an escrow account.
///
/// This function:
/// - Parses the user's private key and escrow account public key.
/// - Constructs a transaction to request funds from the escrow account.
/// - Signs and sends the transaction to the blockchain.
/// - Returns a success message if the transaction is successful.
///
/// # Arguments
/// - `request`: A `RequestFundsRequest` containing:
///   - User's private key (Base58 encoded).
///   - Escrow account public key.
///
/// # Returns
/// - `Ok(impl warp::Reply)`: A JSON response confirming the fund request was successful.
/// - `Err(warp::Rejection)`: A rejection in case of transaction failure.
async fn request_funds_handler(request: RequestFundsRequest) -> Result<impl warp::Reply, warp::Rejection> {
    println!("Starting request funds handler...");

    let rpc_client = RpcClient::new(LOCAL_RPC_URL.to_string());
    let program_id = Pubkey::from_str(PROGRAM_ID).unwrap();

    // Parse the user's private key and extract the public key
    let user_keypair = Keypair::from_base58_string(&request.user_private_key);
    let user_pubkey = user_keypair.pubkey();
    println!("User public key: {}", user_pubkey);

    // Parse the escrow account public key
    let escrow_pubkey = Pubkey::from_str(&request.escrow_pubkey).unwrap();
    println!("Escrow public key: {}", escrow_pubkey);

    // Construct the transaction instruction for requesting funds
    let instruction = Instruction {
        program_id,
        accounts: vec![
            // AccountMeta::new(escrow_pda, false), // Uncomment if you have a PDA for the escrow
            AccountMeta::new(escrow_pubkey, false), // Escrow account
            AccountMeta::new(user_pubkey, true), // User account (signer)
            AccountMeta::new_readonly(system_program::ID, false), // System program (read-only)
        ],
        data: RequestFund {}.data(),
    };
    println!("Instruction for requesting funds created successfully");

    // Fetch the latest blockhash
    let blockhash = rpc_client.get_latest_blockhash().unwrap();
    println!("Latest blockhash: {:?}", blockhash);

    // Create a signed transaction
    let tx = Transaction::new_signed_with_payer(
        &[instruction],
        Some(&user_pubkey),
        &[&user_keypair],
        blockhash,
    );
    println!("Transaction created successfully");

    // Send and confirm the transaction
    match rpc_client.send_and_confirm_transaction(&tx) {
        Ok(_) => {
            println!("Transaction sent successfully!");
            Ok(warp::reply::json(&ExtendSubscriptionResponse {
                message: "Funds requested successfully".to_string()
            }))
        },
        Err(err) => {
            println!("Transaction failed: {:?}", err);
            Err(warp::reject::custom(CustomClientError(err)))
        }
    }
}

/// Handles the request to generate queries for an escrow account.
///
/// This function:
/// - Parses the user's private key and escrow account public key.
/// - Constructs a transaction to generate queries related to the escrow account.
/// - Signs and sends the transaction to the blockchain.
/// - Returns a success message if the transaction is successful.
///
/// # Arguments
/// - `request`: A `GenerateQueriesRequest` containing:
///   - User's private key (Base58 encoded).
///   - Escrow account public key.
///
/// # Returns
/// - `Ok(impl warp::Reply)`: A JSON response confirming the query generation was successful.
/// - `Err(warp::Rejection)`: A rejection in case of transaction failure.
async fn generate_queries_handler(request: GenerateQueriesRequest) -> Result<impl warp::Reply, warp::Rejection> {
    println!("Starting generate queries handler...");

    let rpc_client = RpcClient::new(LOCAL_RPC_URL.to_string());
    let program_id = Pubkey::from_str(PROGRAM_ID).unwrap();

    // Parse the escrow account public key
    let escrow_pubkey = Pubkey::from_str(&request.escrow_pubkey).unwrap();
    println!("Escrow public key: {}", escrow_pubkey);

    // Parse the user's private key and extract the public key
    let user_keypair = Keypair::from_base58_string(&request.user_private_key);
    let user_pubkey = user_keypair.pubkey();
    println!("User public key: {}", user_pubkey);

    // Construct the instruction to generate queries
    let instruction = Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(escrow_pubkey, false), // Escrow account
            AccountMeta::new_readonly(sysvar::slot_hashes::id(), false), // Sysvar slot_hashes (read-only)
            AccountMeta::new_readonly(system_program::ID, false), // System program (read-only)
        ],
        data: GenerateQueries {}.data(),
    };
    println!("Instruction to generate queries created successfully");

    // Fetch the latest blockhash
    let blockhash = rpc_client.get_latest_blockhash().unwrap();
    println!("Latest blockhash: {:?}", blockhash);

    // Create a signed transaction
    let signers = [&user_keypair];
    let tx = Transaction::new_signed_with_payer(
        &[instruction],
        Some(&user_pubkey),
        &signers,
        blockhash,
    );
    println!("Transaction created successfully");

    // Send and confirm the transaction
    match rpc_client.send_and_confirm_transaction(&tx) {
        Ok(_) => {
            println!("Transaction sent successfully!");
            Ok(warp::reply::json(&ExtendSubscriptionResponse {
                message: "Queries generated successfully".to_string()
            }))
        },
        Err(err) => {
            println!("Transaction failed: {:?}", err);
            Err(warp::reject::custom(CustomClientError(err)))
        }
    }
}

/// Handles the request to retrieve queries from an escrow account based on its public key.
///
/// This function:
/// - Fetches account data for the provided escrow account.
/// - Deserializes the account data into an `Escrow` struct.
/// - Extracts and transforms the queries from the escrow account.
/// - Returns the transformed queries as a JSON response.
///
/// # Arguments
/// - `request`: A `GetQueriesByEscrowRequest` containing:
///   - The public key of the escrow account.
///
/// # Returns
/// - `Ok(impl warp::Reply)`: A JSON response with the transformed queries.
/// - `Err(warp::Rejection)`: A rejection in case of an error.
async fn get_queries_by_escrow_handler(
    request: GetQueriesByEscrowRequest,
) -> Result<impl warp::Reply, warp::Rejection> {
    println!("Fetching queries for escrow pubkey: {}", request.escrow_pubkey);

    let rpc_client = RpcClient::new(LOCAL_RPC_URL.to_string());

    // Parse the escrow account's public key
    let escrow_pubkey = Pubkey::from_str(&request.escrow_pubkey).unwrap();
    println!("Escrow public key parsed: {}", escrow_pubkey);

    // Fetch account data for the escrow account
    let account_data = rpc_client.get_account_data(&escrow_pubkey).unwrap();
    println!("Account data fetched for escrow account");

    // Deserialize the account data into an `Escrow` struct
    let escrow_account = Escrow::try_deserialize(&mut &account_data[..]).unwrap();
    println!("Escrow account deserialized successfully");

    // Extract queries from the escrow account
    let queries: Vec<(u128, [u8; 32])> = escrow_account.queries;
    println!("Extracted {} queries from escrow account", queries.len());

    // Transform the queries into the desired format
    let transformed_queries: Vec<(u128, String)> = queries
        .into_iter()
        .map(|(num, bytes)| {
            // Reverse the endianness of the bytes
            let le_num_modulus_p = reverse_endianness(bytes);

            // Convert bytes to Scalar and then to a string
            let v_i = Scalar::from_bytes(&le_num_modulus_p).unwrap();

            (num, v_i.to_string())
        })
        .collect();
    println!("Transformed queries successfully");

    // Return the transformed queries as a JSON response
    Ok(warp::reply::json(&GetQueriesByEscrowPubkeyResponse { queries: transformed_queries }))
}

/// Handles the request to fetch data from an escrow account.
///
/// This function:
/// - Fetches account data for the provided escrow account.
/// - Deserializes the account data into an `Escrow` struct.
/// - Extracts and transforms the queries from the escrow account.
/// - Returns the escrow account data as a JSON response.
///
/// # Arguments
/// - `request`: A `GetEscrowDataRequest` containing:
///   - The public key of the escrow account.
///
/// # Returns
/// - `Ok(impl warp::Reply)`: A JSON response containing escrow account data.
/// - `Err(warp::Rejection)`: A rejection in case of an error.
async fn get_escrow_data_handler(
    request: GetEscrowDataRequest,
) -> Result<impl warp::Reply, warp::Rejection> {
    println!("Fetching escrow data for escrow pubkey: {}", request.escrow_pubkey);

    let rpc_client = RpcClient::new(LOCAL_RPC_URL.to_string());

    // Parse the escrow account's public key
    let escrow_pubkey = Pubkey::from_str(&request.escrow_pubkey).unwrap();
    println!("Escrow public key parsed: {}", escrow_pubkey);

    // Fetch account data for the escrow account
    let account_data = rpc_client.get_account_data(&escrow_pubkey).unwrap();
    println!("Account data fetched for escrow account");

    // Deserialize the account data into an `Escrow` struct
    let escrow_account = Escrow::try_deserialize(&mut &account_data[..]).unwrap();
    println!("Escrow account deserialized successfully");

    // Extract queries from the escrow account
    let queries: Vec<(u128, [u8; 32])> = escrow_account.queries;
    println!("Extracted {} queries from escrow account", queries.len());

    // Transform the queries into the desired format
    let transformed_queries: Vec<(u128, String)> = queries
        .into_iter()
        .map(|(num, bytes)| {
            // Reverse the endianness of the bytes
            let le_num_modulus_p = reverse_endianness(bytes);

            // Convert bytes to Scalar and then to a string
            let v_i = Scalar::from_bytes(&le_num_modulus_p).unwrap();

            (num, v_i.to_string())
        })
        .collect();
    println!("Transformed queries successfully");

    // Return the escrow account data as a JSON response
    Ok(warp::reply::json(&GetEscrowDataResponse {
        buyer_pubkey: escrow_account.buyer_pubkey.to_string(),
        seller_pubkey: escrow_account.seller_pubkey.to_string(),
        u: hex::encode(escrow_account.u),
        g: hex::encode(escrow_account.g),
        v: hex::encode(escrow_account.v),
        number_of_blocks: escrow_account.number_of_blocks,
        query_size: escrow_account.query_size,
        validate_every: escrow_account.validate_every,
        last_prove_date: escrow_account.last_prove_date,
        balance: escrow_account.balance,
        queries: transformed_queries,
        queries_generation_time: escrow_account.queries_generation_time,
        is_subscription_ended_by_buyer: escrow_account.is_subscription_ended_by_buyer,
        is_subscription_ended_by_seller: escrow_account.is_subscription_ended_by_seller,
        subscription_duration: escrow_account.subscription_duration,
        subscription_id: escrow_account.subscription_id,
    }))
}

/// Converts a `u128` into a 32-byte array, placing it in the last 16 bytes of the array.
/// The first 16 bytes are set to zero, and the `u128` value is represented in big-endian format.
/// This function is useful for converting a `u128` value into a fixed-size array for cryptographic operations, such as hashing.
///
/// # Parameters
/// - `i`: A `u128` value to be converted into a 32-byte array.
///
/// # Returns
/// - `[u8; 32]`: A 32-byte array where the first 16 bytes are zero, and the last 16 bytes contain the `u128` value in big-endian format.
fn convert_u128_to_32_bytes(i: u128) -> [u8; 32] {
    let mut bytes = [0u8; 32];  // Create a 32-byte array, initially all zeros

    // Convert the u128 into bytes (16 bytes) and place it in the last 16 bytes of the array
    // Using big-endian format to ensure the bytes are arranged from most significant to least significant
    bytes[16..32].copy_from_slice(&i.to_be_bytes());  // Using big-endian format

    // Return the 32-byte array, where the first 16 bytes are zeros and the last 16 bytes hold the u128 value
    bytes
}

/// Performs a hash-to-curve operation on a u128 value to generate a point on the BLS12-381 curve (G1).
/// It uses the XMD-based SHA-256 expansion method for hashing and converts the result into a G1Affine point.
///
/// This method is typically used in cryptographic applications where mapping arbitrary values (like `u128`)
/// to a point on the elliptic curve is required, such as in pairing-based cryptography or signatures.
///
/// # Parameters
/// - `i`: A `u128` value to be hashed and mapped to a point on the curve.
///
/// # Returns
/// - `G1Affine`: A point on the BLS12-381 G1 curve in affine coordinates, suitable for cryptographic operations.
fn perform_hash_to_curve(i: u128) -> G1Affine {
    // Define the domain separation tag (DST) for the hash-to-curve operation.
    // This DST is specific to the BLS12-381 G1 curve and the XMD SHA-256 expansion method.
    let dst = b"BLS_SIG_BLS12381G1_XMD:SHA-256_SSWU_RO_";

    // Convert the input u128 into a 32-byte array for hashing.
    let msg = convert_u128_to_32_bytes(i);

    // Perform the hash-to-curve operation using the ExpandMsgXmd method and SHA-256 as the hash function.
    // The result is a point on the curve in the projective space (G1Projective).
    let g = <G1Projective as HashToCurve<ExpandMsgXmd<Sha256>>>::hash_to_curve(&msg, dst);

    // Convert the projective point (G1Projective) to affine coordinates (G1Affine).
    // G1Affine is a more compact representation of the point, suitable for use in cryptographic operations.
    G1Affine::from(&g)
}

/// Reverses the endianness of a 32-byte array.
/// This function takes a 32-byte array and reverses the order of its elements.
/// It's typically used when dealing with systems that use different byte orders (endianness).
///
/// # Parameters
/// - `input`: A 32-byte array that represents the data whose endianness is to be reversed.
///
/// # Returns
/// - Returns a new 32-byte array with the bytes in reversed order.
fn reverse_endianness(input: [u8; 32]) -> [u8; 32] {
    let mut reversed = input;
    reversed.reverse(); // Reverse the byte order in place
    reversed
}

/// Computes the sum of H(i)^(v_i) for a list of queries.
/// This function iterates over each query and performs the following steps:
/// 1. Computes H(i) using a hash-to-curve function.
/// 2. Converts v_i (a 32-byte array) to a scalar using reverse endianness.
/// 3. Computes H(i)^(v_i), where `^` denotes scalar multiplication.
/// 4. Adds the result to the cumulative sum `all_h_i_multiply_vi`.
///
/// # Parameters
/// - `queries`: A vector of tuples, where each tuple contains a u128 value `i` and a 32-byte array `v_i_bytes`.
///   The vector represents a series of queries to process.
///
/// # Returns
/// - `G1Projective`: The resulting projective point after adding up all H(i)^(v_i) for each query - [Π(H(i)^(v_i))].
fn compute_h_i_multiply_vi(queries: Vec<(u128, [u8; 32])>) -> G1Projective {
    let mut all_h_i_multiply_vi = G1Projective::identity();

    for (i, v_i_hex) in queries {
        let h_i = perform_hash_to_curve(i);  // H(i)
        let v_i = Scalar::from_bytes(&reverse_endianness(v_i_hex)).unwrap();  // v_i
        let h_i_multiply_v_i = h_i.mul(v_i);  // H(i)^(v_i)

        all_h_i_multiply_vi = all_h_i_multiply_vi.add(&h_i_multiply_v_i);  // Add to total
    }

    all_h_i_multiply_vi  // Return the final product [Π(H(i)^(v_i))]
}
