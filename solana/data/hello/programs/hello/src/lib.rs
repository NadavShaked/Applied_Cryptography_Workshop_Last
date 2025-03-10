use anchor_lang::prelude::*;
use bls12_381::{G1Affine, G1Projective, G2Affine, G2Projective, Scalar, pairing};

 
declare_id!("RepLacethisiDWithTheReaLidFromAnchorKeysooo");
 
#[program]
pub mod hello {
    use super::*;
 
    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        let counter = &ctx.accounts.counter;
        msg!("Counter account created! Current count: {}", counter.count);
        Ok(())
    }
 
    // Do a pairing. Receives a serialized, compressed G1 point.
    pub fn do_pairing(ctx: Context<DoPairing>, x_serialized: [u8; 48]) -> Result<()> {
        let counter = &mut ctx.accounts.counter;
        msg!("Previous counter: {}", counter.count);
 
        let x = G1Affine::from_compressed(&x_serialized).unwrap();
        msg!("x {}", x);

        // let g1 = <G1Projective as PrimeGroup>::generator();
        let g1 = G1Projective::generator();
        msg!("g1 {}", g1);
        // let g2 = <G2Projective as PrimeGroup>::generator();
        
        let g2 = G2Projective::generator();
        msg!("g2 {}", g2);

        // let x = g1+g1; 
        // msg!("x {}", x);
        let x3 = Scalar::from(3)*x;

        let y = g2+g2+g2;
        msg!("y {}", y);

        // pairing
        let z = pairing(&x3.into(), &y.into());
        msg!("z {}", z);



        counter.count += 1;

        msg!("Counter incremented! Current count: {}", counter.count);

        // msg!("Pairing? {}", z1);
        
        Ok(())
    }


}
 
#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,
 
    #[account(
        init,
        payer = payer,
        space = 8 + 8
    )]
    pub counter: Account<'info, Counter>,
    pub system_program: Program<'info, System>,
}
 
#[derive(Accounts)]
pub struct DoPairing<'info> {
    #[account(mut)]
    pub counter: Account<'info, Counter>,
}
 
#[account]
pub struct Counter {
    pub count: u64,
}
