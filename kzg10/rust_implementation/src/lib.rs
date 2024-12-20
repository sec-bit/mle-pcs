use ark_bls12_381::{Fr, G1Affine, G1Projective as G1, G2Projective as G2};
use ark_ec::AffineRepr;
use ark_ec::CurveGroup;
use ark_ec::PrimeGroup;
use ark_ff::{Field, One, PrimeField, UniformRand};
use ark_poly::univariate::DensePolynomial;
use ark_poly::DenseUVPolynomial;
use ark_poly::Polynomial;
use ark_std::{rand::RngCore, vec::Vec, Zero};
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

fn multi_scalar_mul(bases: &[G1Affine], scalars: &[<Fr as PrimeField>::BigInt]) -> G1 {
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

    /// division_by_linear_divisor:
    /// Given f(x) in coeffs[0..n], dividing by (x - d) returns (q(x), remainder)
    /// Implemented from the Python code provided:
    /// coeffs are in ascending order: f(x) = coeffs[0] + coeffs[1]*x + ... + coeffs[n]*x^n
    fn division_by_linear_divisor(coeffs: &[Fr], d: Fr) -> (DensePolynomial<Fr>, Fr) {
        assert!(coeffs.len() > 1, "Polynomial degree must be at least 1");

        let mut quotient = vec![Fr::zero(); coeffs.len() - 1];
        let mut remainder = Fr::zero();

        
        for (i, &coeff) in coeffs.iter().rev().enumerate() {
            if i == 0 {
                remainder = coeff;
            } else {
                let q_len = quotient.len(); // store length beforehand
                quotient[q_len - i] = remainder;
                remainder = remainder * d + coeff;
            }
        }

        (DensePolynomial::from_coefficients_vec(quotient), remainder)
    }

    fn skip_leading_zeros_and_convert_to_fr(poly: &DensePolynomial<Fr>) -> (usize, Vec<Fr>) {
        let coeffs = poly.coeffs();
        let mut last_nonzero = 0;
        for (i, c) in coeffs.iter().enumerate() {
            if !c.is_zero() {
                last_nonzero = i;
            }
        }
        let trimmed = &coeffs[..=last_nonzero];
        (0, trimmed.to_vec()) // leading zeros at the high degree end handled by trimming
    }

    fn msm_bigint(bases: &[G1], scalars: &[Fr]) -> G1 {
        let affine_bases: Vec<G1Affine> = bases.iter().map(|g| g.into_affine()).collect();
        let bigint_scalars: Vec<<Fr as PrimeField>::BigInt> =
            scalars.iter().map(|s| s.into_bigint()).collect();
        multi_scalar_mul(&affine_bases, &bigint_scalars)
    }

    /// Compute the witness polynomial:
    /// This matches the Python logic:
    /// witness_polynomial, _pz = polynomial.division_by_linear_divisor(point)
    /// if hiding:
    ///     random_witness_polynomial, _pr = random_poly.division_by_linear_divisor(point)
    pub fn compute_witness_polynomial(
        &self,
        polynomial: &DensePolynomial<Fr>,
        point: Fr,
        random_ints: &[Fr],
        hiding: bool,
    ) -> (DensePolynomial<Fr>, Option<DensePolynomial<Fr>>) {
        let (witness_polynomial, _pz) =
            Self::division_by_linear_divisor(polynomial.coeffs(), point);

        let mut random_witness_polynomial = None;
        if hiding {
            let random_poly = DensePolynomial::from_coefficients_vec(random_ints.to_vec());
            if self.debug {
                assert!(random_poly.degree() > 0, "Degree of random poly is zero");
            }
            let (rw_poly, _pr) = Self::division_by_linear_divisor(random_poly.coeffs(), point);
            random_witness_polynomial = Some(rw_poly);
        }

        (witness_polynomial, random_witness_polynomial)
    }

    /// open_with_witness_polynomial:
    /// In Python:
    /// def open_with_witness_polynomial(self, powers, point, random_ints, witness_polynomial, hiding_witness_polynomial=None)
    ///
    /// This does no division. It just uses the witness_polynomial and optional hiding_witness_polynomial to produce a proof.
    /// Steps:
    /// 1) Convert witness_poly to bigint scalars and do MSM with powers_of_g.
    /// 2) If hiding witness provided, evaluate blinding polynomial at point, add MSM with powers_of_gamma_g.
    pub fn open_with_witness_polynomial(
        &self,
        powers: &Powers,
        point: Fr,
        random_ints: &[Fr],
        witness_polynomial: &DensePolynomial<Fr>,
        hiding_witness_polynomial: Option<&DensePolynomial<Fr>>,
    ) -> (G1, Option<Fr>) {
        let (num_leading_zeros, witness_coeffs) =
            KZG10Commitment::skip_leading_zeros_and_convert_to_fr(witness_polynomial);
        assert!(
            witness_polynomial.degree() + 1 < powers.powers_of_g.len(),
            "Too many coefficients"
        );

        let g_slice =
            &powers.powers_of_g[num_leading_zeros..(num_leading_zeros + witness_coeffs.len())];
        let mut w = Self::msm_bigint(g_slice, &witness_coeffs);

        let mut random_v = None;
        if let Some(hwp) = hiding_witness_polynomial {
            let blinding_p = DensePolynomial::from_coefficients_vec(random_ints.to_vec());
            random_v = Some(blinding_p.evaluate(&point));
            w += Self::msm_bigint(&powers.powers_of_gamma_g, hwp.coeffs());
        }

        (w, random_v)
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

    #[test]
    fn test_division_by_linear_divisor() {
        let a0 = Fr::from(3u64);
        let a1 = Fr::from(5u64);
        let a2 = Fr::from(2u64);
        let poly = DensePolynomial::from_coefficients_vec(vec![a0, a1, a2]); // 3 + 5x + 2x^2
        let point = Fr::from(2u64);
        let (q, r) = KZG10Commitment::division_by_linear_divisor(poly.coeffs(), point);
        // f(x) = 3 + 5x + 2x^2
        // f(2)=3 + 5*2 + 2*4=3+10+8=21
        assert_eq!(r, Fr::from(21u64));
        // q(x) = (f(x)-f(2))/(x-2) = ( (3+5x+2x^2)-21 )/(x-2)
        //     = (2x^2+5x+3 -21)/(x-2)
        //     = (2x^2+5x-18)/(x-2)
        // Synthetic: q should be degree 1.
        // Let's verify q * (x-2) + 21 = f(x)
        // q should have length 2 (degree 1): q(x)=2x+9?
        // 2x+9; (2x+9)*(x-2)=2x^2+9x -4x -18=2x^2+5x-18
        // Add 21: 2x^2+5x+3 = f(x)? Wait, f(x)=3+5x+2x^2
        // Mistake: remainder check again
        // Actually let's solve for q:
        // f(x)=q(x)*(x-2)+21
        // q(x)*x - 2q(x)=f(x)-21=2x^2+5x-18
        // If q(x)=2x+? => 2x*x=2x^2 good, so q's leading term is correct
        // Compare constant terms: -2 * q(x) must yield -18 at constant level:
        // q(x)=2x+9 yields (2x+9)*(x-2)=2x^2+9x -4x -18=2x^2+5x-18 correct.
        // So q's coeffs = [9,2]
        let q_coeffs = q.coeffs();
        assert_eq!(q_coeffs.len(), 2);
        assert_eq!(q_coeffs[0], Fr::from(9u64));
        assert_eq!(q_coeffs[1], Fr::from(2u64));
    }
}
