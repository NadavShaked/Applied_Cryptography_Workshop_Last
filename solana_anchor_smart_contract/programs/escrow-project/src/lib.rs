// Solana SDK Imports
use solana_program::{
    program::invoke,
    program::invoke_signed,
    sysvar::{clock::Clock, slot_hashes},
    system_instruction,
    keccak,
};

// Anchor Imports
use anchor_lang::prelude::*;
use anchor_lang::solana_program::sysvar;

// BLS Imports
use bls12_381::{
    pairing,
    G1Affine,
    G2Affine,
    G1Projective,
    Scalar,
    G2Projective
};
use bls12_381::hash_to_curve::{ExpandMsgXmd, HashToCurve, HashToField};

// Miscellaneous Imports
use std::ops::{Add, Mul};
use std::str::FromStr;
use std::time::{SystemTime, UNIX_EPOCH};

// Cryptography Imports
use sha2::{Digest, Sha256};

// Number Imports
use num_bigint::BigUint;


declare_id!("5LthHd6oNK3QkTwC59pnn1tPFK7JJUgNjNnEptxxXSei");

pub const MIN_IN_SECOND: i64 = 60;
pub const HOUR_IN_SECOND: i64 = 60 * MIN_IN_SECOND;
pub const DAY_IN_SECOND: i64 = 24 * HOUR_IN_SECOND;

#[program]
mod escrow_project {
    use super::*;

    /// Starts a new subscription by initializing an escrow account with the provided parameters.
    /// The escrow account stores subscription details and tracks the buyer, seller, and other related data.
    ///
    /// # Parameters
    /// - `ctx`: The context containing the buyer, seller, and escrow accounts.
    /// - `subscription_id`: The unique ID for the subscription being started.
    /// - `query_size`: The size of the query for the subscription.
    /// - `number_of_blocks`: The number of blocks involved in the subscription.
    /// - `u`: A parameter for the subscription (a 48-byte array).
    /// - `g`: A parameter for the subscription (a 96-byte array).
    /// - `v`: A parameter for the subscription (a 96-byte array).
    /// - `validate_every`: The validation interval for the subscription.
    ///
    /// # Returns
    /// - `Result<Pubkey>`: Returns the public key of the initialized escrow account.
    pub fn start_subscription(
        ctx: Context<StartSubscription>,
        subscription_id: u64,
        query_size: u64,
        number_of_blocks: u64,
        u: [u8; 48],
        g: [u8; 96],
        v: [u8; 96],
        validate_every: i64,
    ) -> Result<Pubkey> {
        msg!("Starting subscription with ID: {}", subscription_id);

        let escrow = &mut ctx.accounts.escrow;

        escrow.buyer_pubkey = *ctx.accounts.buyer.key;
        escrow.seller_pubkey = *ctx.accounts.seller.key;

        msg!("Assigned buyer pubkey: {}, seller pubkey: {}", escrow.buyer_pubkey, escrow.seller_pubkey);

        escrow.query_size = query_size;
        escrow.number_of_blocks = number_of_blocks;
        escrow.validate_every = validate_every;
        escrow.u = u;
        escrow.g = g;
        escrow.v = v;

        msg!("Query size: {}, Number of blocks: {}, Validate every: {}", query_size, number_of_blocks, validate_every);

        escrow.balance = 0;
        escrow.subscription_duration = 0;
        escrow.subscription_id = subscription_id;
        escrow.bump = ctx.bumps.escrow;

        msg!("Initialized escrow with subscription ID: {}, bump: {}", escrow.subscription_id, escrow.bump);

        Ok(escrow.key())
    }

    /// Adds funds to an existing subscription by transferring the specified amount from the buyer's account to the escrow account.
    ///
    /// # Parameters
    /// - `ctx`: The context containing the buyer, escrow, and system program accounts.
    /// - `amount`: The amount to be transferred and added to the escrow's balance.
    ///
    /// # Returns
    /// - `Result<()>`: Returns `Ok(())` if the transfer and balance update are successful, or an error if any operation fails.
    pub fn add_funds_to_subscription(ctx: Context<AddFundsToSubscription>, amount: u64) -> Result<()> {
        msg!("Adding funds to subscription: {} units", amount);

        let escrow = &mut ctx.accounts.escrow;
        let buyer = &ctx.accounts.buyer;
        let system_program = &ctx.accounts.system_program;

        msg!("Transferring {} units from buyer: {} to escrow: {}", amount, buyer.key(), escrow.key());

        invoke(
            &system_instruction::transfer(
                &buyer.key(),
                &escrow.key(),
                amount
            ),
            &[buyer.to_account_info(), escrow.to_account_info(), system_program.to_account_info()],
        )?;

        escrow.balance += amount;
        msg!("New balance of escrow after adding funds: {}", escrow.balance);

        Ok(())
    }

    /// Generates queries for a subscription by processing slot hashes from the system's slot hash data.
    /// Each query consists of a slot (modulo the number of blocks) and a value derived from a slot hash.
    /// The generated queries are saved in the escrow account, along with the timestamp of query generation.
    ///
    /// # Parameters
    /// - `ctx`: The context containing the escrow account and slot hashes system account.
    ///
    /// # Returns
    /// - `Result<()>`: Returns `Ok(())` if the queries are successfully generated and saved.
    pub fn generate_queries(ctx: Context<GenerateQueries>) -> Result<()> {
        msg!("Generating queries for subscription...");

        let escrow = &mut ctx.accounts.escrow;
        let slot_hashes = &ctx.accounts.slot_hashes;

        // Get the current timestamp
        let clock = Clock::get()?;
        let current_time = clock.unix_timestamp;
        msg!("Current timestamp: {}", current_time);

        require!(
            *slot_hashes.to_account_info().key == slot_hashes::id(),
            ErrorCode::InvalidSlotHashSysvar);

        msg!("Slot hashes account ID validated: {}", slot_hashes.to_account_info().key);

        let binding = slot_hashes.to_account_info();
        let data = binding.try_borrow_data()?;
        let num_slot_hashes = u64::from_le_bytes(data[0..8].try_into().unwrap());
        let mut pos = 8;

        msg!("Number of slot hashes: {}", num_slot_hashes);

        let mut queries = Vec::new();

        for i in 0..escrow.query_size.min(num_slot_hashes) {
            let slot = u64::from_le_bytes(data[pos..pos + 8].try_into().unwrap()) % escrow.number_of_blocks as u64;
            pos += 8;
            let hash = &data[pos..pos + 32]; // Slot hash (32 bytes)
            pos += 32;

            let v_i: [u8; 32] = num_modulus_p(hash.try_into().unwrap());

            // Use slot as block index and hash as v_i
            queries.push((slot as u128, v_i));

            msg!("Generated query: Slot: {}, v_i: {:?}", slot, v_i);
        }

        escrow.queries = queries;
        escrow.queries_generation_time = current_time;

        msg!("Queries generation completed at: {}", current_time);

        Ok(())
    }

    /// Proves the subscription and validates the sigma and mu values provided. This function ensures the validity
    /// of a subscription, checking the timestamps and the cryptographic proofs, then updates the escrow account accordingly.
    /// If the subscription is valid and meets the conditions, it will increase the subscription duration and transfer funds
    /// to the seller after a successful proof.
    ///
    /// **Note:** This instruction will likely fail due to compute unit (CU) limitations on Solana. The BLS pairing operation
    /// required for proof verification is too costly to execute within the available compute units, even when the maximum CU limit
    /// is set. As a result, this function is intended for simulation purposes and will not work as expected on-chain.
    ///
    /// # Parameters
    /// - `ctx`: The context containing the escrow account and the seller's account.
    /// - `sigma`: A 48-byte array representing the proof.
    /// - `mu`: A 32-byte array representing the challenge scalar.
    ///
    /// # Returns
    /// - `Result<()>`: Returns `Ok(())` if the subscription is successfully proved, or an error if validation fails.
    pub fn prove_subscription(ctx: Context<ProveSubscription>, sigma: [u8; 48], mu: [u8; 32]) -> Result<()> {
        msg!("Proving subscription...");

        let escrow = &mut ctx.accounts.escrow;
        let seller = &ctx.accounts.seller;

        // Get the current timestamp from the system clock
        let clock = Clock::get()?;
        let now = clock.unix_timestamp;

        if now < escrow.last_prove_date + escrow.validate_every {
            msg!("No validation needed yet. Skipping validation.");
            return Err(ErrorCode::NoValidationNeeded.into());
        }
        if now > escrow.queries_generation_time + 30 * MIN_IN_SECOND {
            msg!("Query generation expired. Cannot prove subscription.");
            return Err(ErrorCode::GenerateAnotherQuery.into());
        }

        // Deserialize compressed G2Affine and G1Affine points
        let g_norm = G2Affine::from_compressed(&escrow.g).unwrap();
        let v_norm = G2Affine::from_compressed(&escrow.v).unwrap();
        let u = G1Affine::from_compressed(&escrow.u).unwrap();
        msg!("Deserialized group elements: g_norm, v_norm, u.");

        // Reverse the endianness of the challenge (μ) and convert it to a scalar
        let le_mu: [u8; 32] = reverse_endianness(mu);
        let mu_scalar = Scalar::from_bytes(&le_mu).unwrap();
        let sigma_affine = G1Affine::from_compressed(&sigma).unwrap();

        // Compute the sum of all H_i * v_i and the term u * mu
        let all_h_i_multiply_vi = compute_h_i_multiply_vi(&escrow.queries); // Π(H(i)^(v_i))
        let u_multiply_mu = u.mul(mu_scalar);   // u^μ

        let multiplication_sum = all_h_i_multiply_vi.add(&u_multiply_mu);   // Π(H(i)^(v_i)) * u^μ
        let multiplication_sum_affine = G1Affine::from(multiplication_sum);

        // Perform the pairings and check if the proof is valid
        let left_pairing = pairing(&sigma_affine, &g_norm); // e(σ, g)
        let right_pairing = pairing(&multiplication_sum_affine, &v_norm);   // e(Π(H(i)^(v_i)) * u^μ, v)

        msg!("Pairing left: {:?}, Pairing right: {:?}", left_pairing, right_pairing);

        let is_verified = left_pairing.eq(&right_pairing); // e(σ, g) == e(Π(H(i)^(v_i)) * u^μ, v)

        // If the proof is valid, proceed with the subscription logic
        if is_verified {
            msg!("Proof successfully verified.");

            escrow.subscription_duration += 1;
            if escrow.subscription_duration > 5 {
                let transfer_amount = (1.0 + 0.05 * escrow.query_size as f64) as u64;
                msg!("Transferring {} lamports to the seller...", transfer_amount);

                **seller.to_account_info().try_borrow_mut_lamports()? += transfer_amount;
                **escrow.to_account_info().try_borrow_mut_lamports()? -= transfer_amount;
                escrow.balance -= transfer_amount;
            }
            escrow.last_prove_date = now;

            msg!("Subscription successfully proved, last prove date updated to: {}", now);
            Ok(())
        } else {
            msg!("Proof verification failed. Unauthorized.");
            Err(ErrorCode::Unauthorized.into())
        }
    }

    /// Simulates the proof verification for a subscription due to Solana's compute unit limitations.
    /// This function does not perform the actual BLS pairing operation, as even with the maximum allowed
    /// compute units, the verification is too costly. Instead, it accepts a boolean flag (`is_verified`)
    /// representing whether the proof was successfully verified off-chain.
    ///
    /// If `is_verified` is `true`, the function updates the escrow account by extending the subscription
    /// duration and transferring funds to the seller once the subscription meets the required conditions.
    ///
    /// # Parameters
    /// - `ctx`: The context containing the escrow account and the seller's account.
    /// - `is_verified`: A boolean value indicating whether the proof was verified off-chain.
    ///
    /// # Returns
    /// - `Result<()>`: Returns `Ok(())` if the subscription is successfully updated, or an error if
    ///   validation is not needed or the proof verification failed.
    pub fn prove_subscription_simulation(ctx: Context<ProveSubscriptionSimulation>, is_verified: bool) -> Result<()> {
        msg!("Proving subscription...");

        let escrow = &mut ctx.accounts.escrow;
        let seller = &ctx.accounts.seller;

        // Get the current timestamp from the system clock
        let clock = Clock::get()?;
        let now = clock.unix_timestamp;

        if now < escrow.last_prove_date + escrow.validate_every {
            msg!("No validation needed yet. Skipping validation.");
            return Err(ErrorCode::NoValidationNeeded.into());
        }
        if now > escrow.queries_generation_time + 30 * MIN_IN_SECOND {
            msg!("Query generation expired. Cannot prove subscription.");
            return Err(ErrorCode::GenerateAnotherQuery.into());
        }

        // If the proof is valid, proceed with the subscription logic
        if is_verified {
            msg!("Proof successfully verified.");

            escrow.subscription_duration += 1;
            if escrow.subscription_duration > 5 {
                let transfer_amount = (1.0 + 0.05 * escrow.query_size as f64) as u64;
                msg!("Transferring {} lamports to the seller...", transfer_amount);

                **seller.to_account_info().try_borrow_mut_lamports()? += transfer_amount;
                **escrow.to_account_info().try_borrow_mut_lamports()? -= transfer_amount;
                escrow.balance -= transfer_amount;
            }
            escrow.last_prove_date = now;

            msg!("Subscription successfully proved, last prove date updated to: {}", now);
            Ok(())
        } else {
            msg!("Proof verification failed. Unauthorized.");
            Err(ErrorCode::Unauthorized.into())
        }
    }

    /// Ends a subscription by the buyer. This function ensures that only the buyer can end the subscription.
    /// The function checks that the buyer attempting to end the subscription matches the one who started it.
    /// If valid, it marks the subscription as ended by the buyer.
    ///
    /// # Parameters
    /// - `ctx`: The context containing the escrow account and the buyer's account.
    ///
    /// # Returns
    /// - `Result<()>`: Returns `Ok(())` if the subscription is successfully ended by the buyer.
    pub fn end_subscription_by_buyer(ctx: Context<EndSubscriptionByBuyer>) -> Result<()> {
        msg!("Ending subscription by buyer...");

        let escrow = &mut ctx.accounts.escrow;
        let buyer = &ctx.accounts.buyer;

        // Ensure that only the buyer can end the subscription
        require!(escrow.buyer_pubkey == buyer.key(), ErrorCode::Unauthorized);

        msg!("Subscription ending authorized for buyer: {}", buyer.key());

        // Mark the subscription as ended by the buyer
        escrow.is_subscription_ended_by_buyer = true;

        msg!("Subscription successfully ended by buyer: {}", buyer.key());

        Ok(())
    }

    /// Ends a subscription by the seller. This function ensures that only the seller can end the subscription.
    /// The function checks that the seller attempting to end the subscription matches the one who started it.
    /// If valid, it marks the subscription as ended by the seller.
    ///
    /// # Parameters
    /// - `ctx`: The context containing the escrow account and the seller's account.
    ///
    /// # Returns
    /// - `Result<()>`: Returns `Ok(())` if the subscription is successfully ended by the seller.
    pub fn end_subscription_by_seller(ctx: Context<EndSubscriptionBySeller>) -> Result<()> {
        msg!("Ending subscription by seller...");

        let escrow = &mut ctx.accounts.escrow;
        let seller = &ctx.accounts.seller;

        // Ensure that only the seller can end the subscription
        require!(escrow.seller_pubkey == seller.key(), ErrorCode::Unauthorized);

        msg!("Subscription ending authorized for seller: {}", seller.key());

        // Mark the subscription as ended by the seller
        escrow.is_subscription_ended_by_seller = true;

        msg!("Subscription successfully ended by seller: {}", seller.key());

        Ok(())
    }

    /// Handles the fund request process for both the buyer and the seller.
    /// This function checks whether the user requesting the funds is the buyer or the seller
    /// and ensures the correct conditions are met for each case. If the conditions are satisfied,
    /// the requested funds are transferred from the escrow account to the user.
    ///
    /// # Parameters
    /// - `ctx`: The context containing the escrow account, user account, and system program.
    ///
    /// # Returns
    /// - `Result<()>`: Returns `Ok(())` if the funds are successfully transferred. Returns an error if the conditions are not met.
    pub fn request_fund(ctx: Context<RequestFund>) -> Result<()> {
        let escrow = &ctx.accounts.escrow;
        let user = &ctx.accounts.user;
        let system_program = &ctx.accounts.system_program;

        let now = Clock::get()?.unix_timestamp as u64;

        msg!("Subscription Id from program {}", escrow.subscription_id);

        // If the buyer is requesting funds
        if user.key() == escrow.buyer_pubkey {
            msg!("Buyer is requesting funds");

            require!(
            escrow.is_subscription_ended_by_seller || now > (escrow.last_prove_date + 3 * DAY_IN_SECOND).try_into().unwrap(),
            ErrorCode::Unauthorized
        );

            let transfer_amount = escrow.balance;

            msg!("Transferring {} lamports from escrow to buyer", transfer_amount);

            **ctx.accounts.user.try_borrow_mut_lamports()? = ctx
                .accounts
                .user
                .lamports()
                .checked_add(transfer_amount)
                .ok_or(ErrorCode::AmountOverflow)?;

            **ctx
                .accounts
                .escrow
                .to_account_info()
                .try_borrow_mut_lamports()? = ctx
                .accounts
                .escrow
                .to_account_info()
                .lamports()
                .checked_sub(transfer_amount)
                .ok_or(ErrorCode::InsufficientFunds)?;

            msg!("Funds successfully transferred to buyer");

            return Ok(());
        }

        // If the seller is requesting funds
        if user.key() == escrow.seller_pubkey {
            msg!("Seller is requesting funds");

            require!(escrow.is_subscription_ended_by_buyer, ErrorCode::Unauthorized);

            let transfer_amount = escrow.balance;

            msg!("Transferring {} lamports from escrow to seller", transfer_amount);

            **ctx.accounts.user.try_borrow_mut_lamports()? = ctx
                .accounts
                .user
                .lamports()
                .checked_add(transfer_amount)
                .ok_or(ErrorCode::AmountOverflow)?;

            **ctx
                .accounts
                .escrow
                .to_account_info()
                .try_borrow_mut_lamports()? = ctx
                .accounts
                .escrow
                .to_account_info()
                .lamports()
                .checked_sub(transfer_amount)
                .ok_or(ErrorCode::InsufficientFunds)?;

            msg!("Funds successfully transferred to seller");

            return Ok(());
        }

        // If none of the conditions are met
        msg!("Unauthorized fund request attempt");
        Err(ErrorCode::Unauthorized.into())
    }
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
    bytes[16..32].copy_from_slice(&i.to_be_bytes());  // Using big-endian format

    bytes
}

/// Performs a modulus operation on a 32-byte number with a predefined modulus (p).
/// The input `num` is reduced modulo a fixed constant `p`, and the result is returned as a 32-byte array.
/// This is typically used for cryptographic operations that require working with large integers.
///
/// # Parameters
/// - `num`: A 32-byte array representing the number to be reduced modulo `p`.
///
/// # Returns
/// - `[u8; 32]`: A 32-byte array representing the result of the modulus operation (`num % p`).
fn num_modulus_p(num: [u8; 32]) -> [u8; 32] {
    let p_modulus_bytes: [u8; 32] = [
        0x73, 0xed, 0xa7, 0x53, // 0x73ed_a753
        0x29, 0x9d, 0x7d, 0x48, // 0x299d_7d48
        0x33, 0x39, 0xd8, 0x08, // 0x3339_d808
        0x09, 0xa1, 0xd8, 0x05, // 0x09a1_d805
        0x53, 0xbd, 0xa4, 0x02, // 0x53bd_a402
        0xff, 0xfe, 0x5b, 0xfe, // 0xfffe_5bfe
        0xff, 0xff, 0xff, 0xff, // 0xffff_ffff
        0x00, 0x00, 0x00, 0x01  // 0x0000_0001
    ];

    // Convert both [u8; 32] arrays to BigUint (Little-Endian format)
    let num = BigUint::from_bytes_be(&num);
    let p = BigUint::from_bytes_be(&p_modulus_bytes);

    // Perform modulo operation (num_a % p)
    let result = &num % &p;

    // Convert the result back to bytes (little-endian format)
    let mut result_bytes: [u8; 32] = [0; 32]; // Initialize array with zeros
    let result_vec = result.to_bytes_be(); // Get Vec<u8> in little-endian format

    // Copy the Vec<u8> into the fixed-size array, handling cases where it's smaller than 32 bytes
    let len = result_vec.len().min(32);
    result_bytes[..len].copy_from_slice(&result_vec[..len]);

    result_bytes
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
pub fn compute_h_i_multiply_vi(queries: &Vec<(u128, [u8; 32])>) -> G1Projective {
    let mut all_h_i_multiply_vi = G1Projective::identity();

    for (i, v_i_bytes) in queries {
        let h_i = perform_hash_to_curve(*i); // Compute H(i)
        let v_i_scalar = Scalar::from_bytes(&reverse_endianness(*v_i_bytes)).unwrap(); // Convert v_i to Scalar
        let h_i_multiply_v_i = h_i.mul(v_i_scalar); // Compute H(i)^(v_i)

        all_h_i_multiply_vi = all_h_i_multiply_vi.add(&h_i_multiply_v_i);
    }

    all_h_i_multiply_vi
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
    let dst = b"BLS_SIG_BLS12381G1_XMD:SHA-256_SSWU_RO_";

    // Convert u128 to 32-byte array
    let msg = convert_u128_to_32_bytes(i);

    // Perform hash-to-curve
    let g = <G1Projective as HashToCurve<ExpandMsgXmd<Sha256>>>::hash_to_curve(&msg, dst);

    // Convert from G1Projective to G1Affine
    G1Affine::from(&g)
}

#[derive(Accounts)]
pub struct AddFundsToSubscription<'info> {
    #[account(mut)]
    pub escrow: Account<'info, Escrow>,
    #[account(mut)]
    pub buyer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(subscription_id: u64)]
pub struct StartSubscription<'info> {
    #[account(init, seeds = [b"escrow", buyer.key().as_ref(), seller.key().as_ref(), &subscription_id.to_le_bytes()], bump, payer = buyer, space = 4096)]
    pub escrow: Account<'info, Escrow>,
    #[account(mut)]
    pub buyer: Signer<'info>,
    /// CHECK: This is safe.
    #[account(mut)]
    pub seller: AccountInfo<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct EndSubscriptionByBuyer<'info> {
    #[account(mut)]
    pub escrow: Account<'info, Escrow>,
    #[account(mut)]
    pub buyer: Signer<'info>,
}

#[derive(Accounts)]
pub struct EndSubscriptionBySeller<'info> {
    #[account(mut)]
    pub escrow: Account<'info, Escrow>,
    #[account(mut)]
    pub seller: Signer<'info>,
}

#[derive(Accounts)]
pub struct RequestFund<'info> {
    #[account(mut, seeds = [
        b"escrow",
        // user.key().as_ref(),
        escrow.buyer_pubkey.as_ref(),
        escrow.seller_pubkey.as_ref(),
        &escrow.subscription_id.to_le_bytes(),
    ],
    bump,
    close = user,
    )]
    pub escrow: Account<'info, Escrow>,
    #[account(mut)]
    pub user: Signer<'info>, // Can be buyer or seller
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct GetQueryValues<'info> {
    #[account(mut)]
    pub escrow: Account<'info, Escrow>,
}

#[derive(Accounts)]
pub struct ProveSubscription<'info> {
    #[account(mut)]
    pub escrow: Account<'info, Escrow>,
    #[account(mut)]
    pub seller: Signer<'info>,
}

#[derive(Accounts)]
pub struct ProveSubscriptionSimulation<'info> {
    #[account(mut)]
    pub escrow: Account<'info, Escrow>,
    #[account(mut)]
    pub seller: Signer<'info>,
}

#[derive(Accounts)]
pub struct GenerateQueries<'info> {
    #[account(mut)]
    pub escrow: Account<'info, Escrow>,
    /// CHECK: This is a sysvar account required for verifying slot hashes
    #[account(address = slot_hashes::id())]
    pub slot_hashes: AccountInfo<'info>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct Escrow {
    pub buyer_pubkey: Pubkey,
    pub seller_pubkey: Pubkey,
    pub query_size: u64,
    pub number_of_blocks: u64,
    pub u: [u8; 48], 
    pub g: [u8; 96], 
    pub v: [u8; 96],
    pub subscription_duration: u64,
    pub validate_every: i64,
    pub queries: Vec<(u128, [u8; 32])>,
    pub queries_generation_time: i64,
    pub balance: u64,
    pub last_prove_date: i64,
    pub is_subscription_ended_by_buyer: bool,
    pub is_subscription_ended_by_seller: bool,
    pub subscription_id: u64,
    pub bump: u8,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Insufficient funds")]
    InsufficientFunds,

    #[msg("Amount overflow")]
    AmountOverflow,
    
    #[msg("Payment count overflow")]
    PaymentCountOverflow,

    #[msg("No validation needed at this time")]
    NoValidationNeeded,

    #[msg("Generate another query before proving")]
    GenerateAnotherQuery,

    #[msg("Unauthorized operation.")]
    Unauthorized,

    #[msg("Invalid SlotHashes sysvar provided.")]
    InvalidSlotHashSysvar,
}