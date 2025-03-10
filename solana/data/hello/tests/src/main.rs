use bls12_381::{G1Affine, G2Affine, Scalar, pairing};

fn main() {
    let g1 = G1Affine::generator();
    let g2 = G2Affine::generator();
    let x = Scalar::from(2)*g1;
    let y = Scalar::from(3)*g2;
    let z = pairing(&x.into(), &y.into());

    println!("Hello, world: {}", z);
}
