// use ark_bls12_381::{Fr, G1Affine, G1Projective as G1, G2Projective as G2};
// use ark_ec::Group;
// use ark_ec::{scalar_mul::ScalarMul};
// use ark_ec::CurveGroup;
// use ark_ff::{Field, One, PrimeField, UniformRand};
// use ark_poly::univariate::DensePolynomial;
// use ark_std::{rand::RngCore, vec::Vec};

use ark_bls12_381::{Fr, G1Affine, G1Projective as G1, G2Projective as G2};
use ark_ec::CurveGroup;
use ark_ec::AffineRepr;
use std::ops::Mul;
use ark_ec::scalar_mul::ScalarMul;
use ark_ff::{Field, One, PrimeField, UniformRand};
use ark_poly::univariate::DensePolynomial; 
use ark_ec::PrimeGroup;
use ark_poly::Polynomial;
use ark_poly::DenseUVPolynomial;
use ark_std::{rand::RngCore, vec::Vec,Zero};



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

// Powers Struct
pub struct Powers {
    pub powers_of_g: Vec<G1>,
    pub powers_of_gamma_g: Vec<G1>,
}

// Verification Key struct
pub struct VerifyingKey {
    pub g: G1,
    pub gamma_g: G1,
    pub h: G2,
    pub beta_h: G2,
}

/// A polynomial Commitment
pub struct Commitment(pub G1);

fn multi_scalar_mul(
    bases: &[G1Affine],
    scalars: &[<Fr as PrimeField>::BigInt],
) -> G1 {
    assert_eq!(bases.len(), scalars.len(), "Mismatched lengths");
    let mut acc = G1::zero();
    for (base, scalar) in bases.iter().zip(scalars.iter()) {
        // Convert from affine to projective and multiply
        let point = base.mul_bigint(*scalar);
        acc += point;
    }
    acc
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

    /// Trim function: selects a subset of the setup parameters for a given supported degree
    pub fn trim(&self, pp: &SetupParams, supported_degree: usize) -> (Powers, VerifyingKey) {
        let mut deg = supported_degree;
        if deg == 1 {
            deg += 1;
        }

        let powers_of_g = pp.powers_of_g[..=deg].to_vec();
        let powers_of_gamma_g = pp.powers_of_gamma_g[..=deg].to_vec();

        let powers = Powers {
            powers_of_g,
            powers_of_gamma_g,
        };

        let vk = VerifyingKey {
            g: pp.powers_of_g[0],
            gamma_g: pp.powers_of_gamma_g[0],
            h: pp.h,
            beta_h: pp.beta_h,
        };

        (powers, vk)
    }

    /// Commit function: commit to a polynomial using the given trimmed powers.
    ///
    /// # Arguments
    /// * `powers` - Powers to use for commitment (from trim)
    /// * `polynomial` - The polynomial to commit to
    /// * `hiding_bound` - Optional hiding degree
    /// * `rng` - RNG for hiding polynomial sampling if needed
    ///
    /// # Returns
    /// A tuple `(Commitment, Option<Vec<Fr>>)` where the second is the random ints used for hiding if hiding_bound is set.
    pub fn commit<R: RngCore>(
        &self,
        powers: &Powers,
        polynomial: &DensePolynomial<Fr>,
        hiding_bound: Option<usize>,
        rng: &mut R,
    ) -> (Commitment, Option<Vec<Fr>>) {
        let num_coefficients = polynomial.degree() + 1;
        let num_powers = powers.powers_of_g.len();
        assert!(
            num_coefficients <= num_powers,
            "Too many coefficients: {}, powers: {}",
            num_coefficients,
            num_powers
        );

        let coeffs = polynomial.coeffs();
        let mut last_non_zero = 0;
        for (i, c) in coeffs.iter().enumerate() {
            if !c.is_zero() {
                last_non_zero = i;
            }
        }
        let trimmed_coeffs = &coeffs[..=last_non_zero];
        let num_leading_zeros = 0; // Since we slice to last_non_zero, no leading zeros at the front

        // Prepare bases and scalars for MSM
        let bases: Vec<G1Affine> = powers.powers_of_g
            [num_leading_zeros..(num_leading_zeros + trimmed_coeffs.len())]
            .iter()
            .map(|g| g.into_affine())
            .collect();

        let scalars: Vec<<Fr as PrimeField>::BigInt> =
            trimmed_coeffs.iter().map(|c| c.into_bigint()).collect();

        let mut commitment = multi_scalar_mul(&bases, &scalars);

        // Hiding polynomial if needed
        let random_ints = if let Some(hb) = hiding_bound {
            // Generate a random polynomial with non-zero degree
            let mut rand_coeffs = Vec::new();
            while rand_coeffs.is_empty() || (rand_coeffs.len() - 1 == 0) {
                rand_coeffs.clear();
                for _ in 0..(hb + 1) {
                    rand_coeffs.push(Fr::rand(rng));
                }
            }

            let hiding_poly_degree = rand_coeffs.len() - 1;
            let gamma_num_powers = powers.powers_of_gamma_g.len();
            assert!(hb != 0, "Hiding bound is zero");
            assert!(
                hiding_poly_degree < gamma_num_powers,
                "Hiding bound is too large"
            );

            let gamma_bases: Vec<G1Affine> = powers.powers_of_gamma_g[..=hiding_poly_degree]
                .iter()
                .map(|g| g.into_affine())
                .collect();

            let gamma_scalars: Vec<<Fr as PrimeField>::BigInt> =
                rand_coeffs.iter().map(|c| c.into_bigint()).collect();

            let random_commitment = multi_scalar_mul(&gamma_bases, &gamma_scalars);
            commitment += random_commitment;

            Some(rand_coeffs)
        } else {
            None
        };

        (Commitment(commitment), random_ints)
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
        assert_eq!(params.powers_of_g.len(), 11); // max_degree + 1
        assert_eq!(params.powers_of_gamma_g.len(), 12); // max_degree + 2
        assert_eq!(params.neg_powers_of_h.len(), 11); // max_degree + 1
    }
}
