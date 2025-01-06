use ark_bls12_381::{Fr, Bls12_381, G1Affine, G1Projective as G1, G2Projective as G2};
use ark_ec::AffineRepr;
use ark_ec::CurveGroup;
use ark_ec::PrimeGroup;
use ark_ec::pairing::Pairing;
use ark_ff::{Field, One, PrimeField, UniformRand};
use ark_poly::univariate::DensePolynomial;
use ark_poly::DenseUVPolynomial;
use ark_poly::Polynomial;
use ark_std::{rand::RngCore, vec::Vec, Zero};
use std::ops::Mul;
use ark_ec::pairing::PairingOutput;


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

/// A proof that includes the witness `w` and optional random value `random_v`.
pub struct Proof {
    pub w: G1,
    pub random_v: Option<Fr>,
}

/// A helper function to do pairings in BLS12_381
/// and return the PairingOutput<Bls12_381>.
fn pairing(g1: &G1, g2: &G2) -> PairingOutput<Bls12_381> {
    let g1_affine = g1.into_affine();
    let g2_affine = g2.into_affine();
    Bls12_381::pairing(g1_affine, g2_affine)
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

    /// `open`: Evaluate polynomial at `point`, produce proof (w + optional random_v).
    pub fn open(
        &self,
        powers: &Powers,
        polynomial: &DensePolynomial<Fr>,
        point: Fr,
        random_ints: &[Fr],
        hiding: bool,
    ) -> Proof {
        let degree = polynomial.degree();
        assert!(
            degree + 1 < powers.powers_of_g.len(),
            "Too many coefficients, polynomial.degree: {}",
            degree
        );

        let (witness_poly, hiding_witness_poly) = self.compute_witness_polynomial(polynomial, point, random_ints, hiding);
        let (w_g1, random_v) =
            self.open_with_witness_polynomial(powers, point, random_ints, &witness_poly, hiding_witness_poly.as_ref());
        
        Proof {
            w: w_g1,
            random_v,
        }
    }

    /// `check`: verify the opening proof
    pub fn check(
        &self,
        vk: &VerifyingKey,
        comm: &Commitment,
        point: Fr,
        value: Fr,
        proof: &Proof,
        hiding: bool,
    ) -> bool {
        // inner = comm.value - g*value
        let mut inner = comm.0 - (vk.g * value);

        // if hiding, subtract gamma_g * proof.random_v
        if hiding {
            if let Some(rv) = proof.random_v {
                // remove unnecessary parentheses
                inner -= vk.gamma_g * rv;
            }
        }

        // LHS = pairing(inner, h)
        let lhs = pairing(&inner, &vk.h);

        // RHS = pairing(proof.w, beta_h - h*point)
        let beta_h_minus_h_point = vk.beta_h - (vk.h * point);
        let rhs = pairing(&proof.w, &beta_h_minus_h_point);

        lhs == rhs
    }

    pub fn batch_check<R: RngCore>(
        &self,
        vk: &VerifyingKey,
        commitments: &[Commitment],
        points: &[Fr],
        values: &[Fr],
        proofs: &[Proof],
        hiding: bool,
        rng: &mut R,
    ) -> bool {
        assert_eq!(commitments.len(), points.len());
        assert_eq!(points.len(), values.len());
        assert_eq!(values.len(), proofs.len());

        let mut total_c = G1::zero();
        let mut total_w = G1::zero();
        let mut g_multiplier = Fr::zero();
        let mut gamma_g_multiplier = Fr::zero();

        for ((comm, &z), (&v, proof)) in commitments
            .iter()
            .zip(points)
            .zip(values.iter().zip(proofs))
        {
            let randomizer = Fr::rand(rng);

            // c' = comm.value + z * proof.w
            let c_prime = comm.0 + (proof.w * z);

            total_c += c_prime * randomizer;
            total_w += proof.w * randomizer;
            g_multiplier += v * randomizer;

            if hiding {
                if let Some(rv) = proof.random_v {
                    gamma_g_multiplier += rv * randomizer;
                }
            }
        }

        total_c -= vk.g * g_multiplier;
        if hiding {
            total_c -= vk.gamma_g * gamma_g_multiplier;
        }

        let lhs = pairing(&total_w, &vk.beta_h);
        let rhs = pairing(&total_c, &vk.h);

        lhs == rhs
    }
}

