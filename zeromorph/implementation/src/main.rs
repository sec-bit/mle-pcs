use ark_bls12_381::{Bls12_381, Fr, G1Projective, G2Projective};
use ark_ec::{pairing::Pairing, Group};
use ark_ff::{PrimeField, One};
use ark_poly::{Polynomial, DenseUVPolynomial};
use ark_poly::polynomial::univariate::DensePolynomial;
use ark_std::{vec::Vec, Zero};

/// We'll assume that `D` is the maximum degree for our KZG commitments.
const D: usize = 1024; // Example value, adjust as needed

/// SRS structure for KZG commitments.
pub struct KZGSRS<P: Pairing> {
    pub g1_powers: Vec<P::G1>,
    pub g2_powers: Vec<P::G2>,
}

impl KZGSRS<Bls12_381> {
    /// Generate an SRS given τ.
    /// Note: This is for testing and demonstration only.
    pub fn generate_srs(d: usize, tau: Fr) -> Self {
        // For BLS12_381:
        // G1Projective::generator() and G2Projective::generator() give the base generators.
        let g1 = G1Projective::generator();
        let h = G2Projective::generator();

        let mut g1_powers = Vec::with_capacity(d + 1);
        let mut g2_powers = Vec::with_capacity(d + 1);

        let mut cur_tau = Fr::one();
        for _ in 0..=d {
            let g1_elem = g1.mul_bigint(cur_tau.into_bigint());
            let g2_elem = h.mul_bigint(cur_tau.into_bigint());
            g1_powers.push(g1_elem);
            g2_powers.push(g2_elem);
            cur_tau *= Fr::from(2u64); // Example: increment tau's power. Replace as needed.
        }

        Self { g1_powers, g2_powers }
    }
}

/// A simple wrapper for a univariate polynomial in Fr.
pub struct UniPoly {
    pub poly: DensePolynomial<Fr>,
}

impl UniPoly {
    /// Create a polynomial from coefficients (constant term first).
    pub fn from_coefficients(coeffs: Vec<Fr>) -> Self {
        Self {
            poly: DensePolynomial::from_coefficients_vec(coeffs),
        }
    }

    /// Evaluate polynomial at a field element.
    pub fn evaluate(&self, x: &Fr) -> Fr {
        self.poly.evaluate(x)
    }

    /// Degree of the polynomial.
    pub fn degree(&self) -> usize {
        self.poly.degree()
    }
}

/// Commitment to a polynomial using KZG:
/// cm(P) = Σ a_i * g1_powers[i], where P(x) = Σ a_i x^i.
pub fn kzg_commit(srs: &KZGSRS<Bls12_381>, poly: &UniPoly) -> G1Projective {
    let coeffs = &poly.poly.coeffs;
    let mut commitment = G1Projective::zero();
    for (i, &coeff) in coeffs.iter().enumerate() {
        let term = srs.g1_powers[i].mul_bigint(coeff.into_bigint());
        commitment += term;
    }
    commitment
}

fn main() {
    let tau = Fr::from(2u64); // Just a test value
    let srs = KZGSRS::<Bls12_381>::generate_srs(D, tau);

    let coeffs = vec![Fr::from(1u64), Fr::from(2u64), Fr::from(3u64)]; // P(x) = 1 + 2x + 3x²
    let poly = UniPoly::from_coefficients(coeffs);
    let cm = kzg_commit(&srs, &poly);

    println!("Commitment: {:?}", cm);
}
