use ark_bls12_381::{Fr, G1Projective as G1, G2Projective as G2};
use ark_ec::Group;
use ark_ff::{Field, One, UniformRand};
use ark_std::rand::RngCore;
use ark_std::vec::Vec;
use std::ops::Mul;

pub struct KZG10Commitment {
    pub debug: bool,
}

pub struct SetupParams {
    pub powers_of_g: Vec<G1>,
    pub powers_of_gamma_g: Vec<G1>,
    pub h: G2,
    pub beta_h: G2,
    pub neg_powers_of_h: Vec<G2>,
}

impl KZG10Commitment {
    pub fn new(debug: bool) -> Self {
        Self { debug }
    }

    pub fn setup<R: RngCore>(
        &self,
        max_degree: usize,
        produce_g2_powers: bool,
        secret_symbol: Option<Fr>,
        g1_generator: Option<Fr>,
        g2_generator: Option<Fr>,
        rng: &mut R,
    ) -> SetupParams {
        // Default generators
        let default_g = G1::generator();
        let default_h = G2::generator();

        // Derive g and h from provided scalars or use default generators
        let g = if let Some(gen) = g1_generator {
            default_g.mul(gen)
        } else {
            default_g
        };

        let h = if let Some(gen) = g2_generator {
            default_h.mul(gen)
        } else {
            default_h
        };

        // Beta (the secret symbol)
        let beta = secret_symbol.unwrap_or_else(|| Fr::rand(rng));

        // gamma_g is another field element chosen at random
        let gamma_g = Fr::rand(rng);

        // Compute powers_of_s = [ 1, beta, beta^2,...., beta^(max_degree+1)]
        let mut powers_of_s = Vec::with_capacity(max_degree + 2);
        {
            let mut current = Fr::one();
            for _ in 0..(max_degree + 2) {
                powers_of_s.push(current);
                current *= beta;
            }
        }

        // powers_of_g[i] = g^{beta^i}
        let powers_of_g: Vec<G1> = powers_of_s[..=max_degree]
            .iter()
            .map(|exp| g.mul(*exp))
            .collect();

        let powers_of_gamma_g: Vec<G1> = powers_of_s
            .iter()
            .map(|exp| g.mul(gamma_g * (*exp)))
            .collect();

        let beta_h = h.mul(beta);

        let mut neg_powers_of_h = Vec::new();
        if produce_g2_powers {
            let beta_inv = beta.inverse().expect("beta must be invertible");
            let mut current_inv = Fr::one();
            neg_powers_of_h.push(h);

            for _ in 1..=max_degree {
                current_inv *= beta_inv;
                neg_powers_of_h.push(h.mul(current_inv));
            }
        }
        SetupParams {
            powers_of_g,
            powers_of_gamma_g,
            h,
            beta_h,
            neg_powers_of_h,
        }
    }
}



#[cfg(test)]
mod tests {
    use super::*;
    use ark_std::test_rng;

    #[test]
    fn test_setup() {
        let mut rng = test_rng();
        let kzg = KZG10Commitment::new(false);

        let params = kzg.setup(10, true, None, None, None, &mut rng);
        assert_eq!(params.powers_of_g.len(), 11);        // max_degree + 1
        assert_eq!(params.powers_of_gamma_g.len(), 12); // max_degree + 2
        assert_eq!(params.neg_powers_of_h.len(), 11);   // max_degree + 1
    }
}
