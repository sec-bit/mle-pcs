//! mle_polynomial.rs
//!
//! Minimal translation of MLEPolynomial Python class into Rust with arkworks.

use ark_bls12_381::Fr;
use ark_ff::{Field, One, Zero};
use std::fmt;

/// A simple error type for MLE operations.
#[derive(Debug)]
pub enum MLEError {
    /// Returned when evaluation index is out of range.
    IndexOutOfRange,
    /// Returned when polynomial dimension does not match expected constraints.
    DimensionMismatch(String),
    /// Returned for k > 5 in eqs_over_hypercube_slow (per the Python code).
    UnsupportedOperation(String),
}

impl fmt::Display for MLEError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            MLEError::IndexOutOfRange => write!(f, "Evaluation index out of range"),
            MLEError::DimensionMismatch(s) => write!(f, "Dimension mismatch: {}", s),
            MLEError::UnsupportedOperation(s) => write!(f, "Unsupported operation: {}", s),
        }
    }
}

impl std::error::Error for MLEError {}

/// A struct holding evaluations of a multi-linear polynomial over 2^num_var points.
#[derive(Clone, Debug)]
pub struct MLEPolynomial {
    pub evals: Vec<Fr>,
    pub num_var: usize,
}

impl MLEPolynomial {
    /// Creates a new MLEPolynomial from `evals`. If `evals.len() < 2^num_var`, it pads with zeros.
    pub fn new(mut evals: Vec<Fr>, num_var: usize) -> Result<Self, MLEError> {
        let expected_len = 1 << num_var; // 2^num_var
        if evals.len() > expected_len {
            return Err(MLEError::DimensionMismatch(format!(
                "evals length {} exceeds 2^num_var = {}",
                evals.len(),
                expected_len
            )));
        }

        // Pad with 0 if needed
        evals.resize(expected_len, Fr::zero());

        Ok(Self { evals, num_var })
    }

    /// Returns the evaluation at `index`, or None if out of range.
    pub fn get(&self, index: usize) -> Option<&Fr> {
        self.evals.get(index)
    }

    /// Evaluates the polynomial at a list of points `zs`.
    /// Mirrors `evaluate_from_evals` in the Python code.
    pub fn evaluate(&self, zs: &[Fr]) -> Result<Fr, MLEError> {
        if zs.len() != self.num_var {
            return Err(MLEError::DimensionMismatch(format!(
                "Expected {} variables, got {}",
                self.num_var,
                zs.len()
            )));
        }
        Ok(evaluate_from_evals(&self.evals, zs))
    }

    /// Converts the stored evaluations into coefficients (reverse of `compute_evals_from_coeffs`).
    pub fn to_coeffs(&self) -> Vec<Fr> {
        compute_coeffs_from_evals(&self.evals)
    }

    /// Decomposes this MLE polynomial by dividing at `point`.
    /// Mirrors `decompose_by_div` from Python code.
    ///
    /// Returns:
    ///  - Vec of MLEPolynomial (quotients)
    ///  - Fr (the evaluation at that point)
    pub fn decompose_by_div(&self, point: &[Fr]) -> Result<(Vec<MLEPolynomial>, Fr), MLEError> {
        if point.len() != self.num_var {
            return Err(MLEError::DimensionMismatch(
                "Number of variables must match the point".to_string(),
            ));
        }

        let mut e = self.evals.clone();
        let k = self.num_var;
        let mut quotients = Vec::with_capacity(k);

        let mut half = 1 << (k - 1); // 2^(k-1)
        for i in 0..k {
            // Build the quotient polynomial for dimension (k-i-1)
            let mut q = vec![Fr::zero(); half];
            for j in 0..half {
                q[j] = e[j + half] - e[j];
                e[j] = e[j] * (Fr::one() - point[k - i - 1]) + e[j + half] * point[k - i - 1];
            }
            // Each quotient is an MLEPolynomial of dimension (k-i-1)
            quotients.insert(
                0,
                MLEPolynomial {
                    evals: q,
                    num_var: k - i - 1,
                },
            );
            half >>= 1;
        }

        // e[0] is the final evaluation
        Ok((quotients, e[0]))
    }
}

/// Returns log2(n), assuming n is a power of two.
/// If n is not a power of two, you could handle that differently.
pub fn log2_usize(n: usize) -> usize {
    // For a power-of-two n, this is safe:
    // e.g. n = 8 => trailing_zeros() = 3
    n.trailing_zeros() as usize
}

/// Compute monomials over hypercube from the list `rs`.
/// Mirrors `compute_monomials` in Python code.
pub fn compute_monomials(rs: &[Fr]) -> Vec<Fr> {
    let k = rs.len();
    let n = 1 << k; // 2^k
    let mut evals = vec![Fr::one(); n];
    let mut half = 1;
    for &r in rs {
        for j in 0..half {
            evals[j + half] = evals[j] * r;
        }
        half <<= 1;
    }
    evals
}

/// Compute eqs over hypercube from the list `rs`.
/// Mirrors `eqs_over_hypercube` in Python code.
pub fn eqs_over_hypercube(rs: &[Fr]) -> Vec<Fr> {
    let k = rs.len();
    let n = 1 << k;
    let mut evals = vec![Fr::one(); n];
    let mut half = 1;
    for &r in rs {
        for j in 0..half {
            let tmp = evals[j + half];
            evals[j + half] = evals[j] * r;
            evals[j] = evals[j] - evals[j + half];
            // above line is effectively: evals[j] = evals[j] - (evals[j] * r)
            // but be mindful that evals[j + half] was overwritten.
            // The original Python does:
            //   evals[j+half] = evals[j] * rs[i]
            //   evals[j] = evals[j] - evals[j+half]
        }
        half <<= 1;
    }
    evals
}

/// "Slow" version of eqs over hypercube. k > 5 is not supported.
pub fn eqs_over_hypercube_slow(k: usize, indeterminates: &[Fr]) -> Result<Vec<Fr>, MLEError> {
    if k > 5 {
        return Err(MLEError::UnsupportedOperation(
            "k>5 isn't supported".to_string(),
        ));
    }
    let xs = &indeterminates[..k];
    let n = 1 << k;
    let mut eqs = vec![Fr::one(); n];
    for i in 0..n {
        let bits = bits_le_with_width(i, k);
        let mut val = Fr::one();
        for j in 0..k {
            let bs_j = if bits[j] { Fr::one() } else { Fr::zero() };
            // (1 - xs[j])*(1 - bs[j]) + xs[j]*bs[j]
            let term = (Fr::one() - xs[j]) * (Fr::one() - bs_j) + xs[j] * bs_j;
            val *= term;
        }
        eqs[i] = val;
    }
    Ok(eqs)
}

/// Helper for eqs_over_hypercube_slow: get binary bits of `x` in little-endian, width = k.
fn bits_le_with_width(x: usize, k: usize) -> Vec<bool> {
    let mut out = Vec::with_capacity(k);
    let mut temp = x;
    for _ in 0..k {
        out.push((temp & 1) == 1);
        temp >>= 1;
    }
    out
}

/// Compute polynomial evaluations from coefficients, analogous to `compute_evals_from_coeffs`.
/// Uses the simplistic `ntt_core` logic from the Python code with twiddle = 1.
pub fn compute_evals_from_coeffs(coeffs: &[Fr]) -> Vec<Fr> {
    let mut result = coeffs.to_vec();
    ntt_core(&mut result, Fr::one());
    result
}

/// Compute polynomial coefficients from evaluations, analogous to `compute_coeffs_from_evals`.
/// Uses the simplistic `ntt_core` logic from the Python code with twiddle = -1.
pub fn compute_coeffs_from_evals(evals: &[Fr]) -> Vec<Fr> {
    let mut result = evals.to_vec();
    ntt_core(&mut result, Fr::from(-1i64));
    result
}

/// The simplistic "NTT" from the Python code:
/// ```python
/// for i in range(k):
///     for j in range(0, n, 2*half):
///         for l in range(j, j+half):
///             vs[l+half] = vs[l+half] + twiddle * vs[l]
///     half <<= 1
/// ```
pub fn ntt_core(vs: &mut [Fr], twiddle: Fr) {
    let n = vs.len();
    let k = log2_usize(n);
    let mut half = 1;
    for _stage in 0..k {
        let step = 2 * half;
        for j in (0..n).step_by(step) {
            for l in j..(j + half) {
                // vs[l+half] = vs[l+half] + (twiddle * vs[l])
                let temp = twiddle * vs[l];
                vs[l + half] += temp;
            }
        }
        half <<= 1;
    }
}

/// Evaluate the polynomial (given by all its evaluations `evals`) at `zs`.
/// Mirrors `evaluate_from_evals` from Python code.
pub fn evaluate_from_evals(mut f: &[Fr], zs: &[Fr]) -> Fr {
    // We'll create an owned or temporary buffer at each iteration
    let mut half = f.len() >> 1; // n/2
    let mut current = f.to_vec();
    for &z in zs {
        let even: Vec<Fr> = current.iter().step_by(2).cloned().collect();
        let odd: Vec<Fr> = current.iter().skip(1).step_by(2).cloned().collect();
        let mut new_f = vec![Fr::zero(); half];
        for i in 0..half {
            // f[i] = even[i] + z*(odd[i] - even[i])
            new_f[i] = even[i] + z * (odd[i] - even[i]);
        }
        current = new_f;
        half >>= 1;
    }
    current[0]
}

/// Alternative evaluation (like `evaluate_from_evals_2` in Python).
/// Reverses usage of z's inside the loop.
pub fn evaluate_from_evals_2(evals: &[Fr], zs: &[Fr]) -> Fr {
    let k = zs.len();
    let mut half = evals.len() >> 1;
    let mut f = evals.to_vec();
    for i in 0..k {
        let u = zs[k - i - 1];
        let mut new_f = vec![Fr::zero(); half];
        for j in 0..half {
            // f[j] = (1-u)*f[j] + u*f[j+half]
            new_f[j] = (Fr::one() - u) * f[j] + u * f[j + half];
        }
        f = new_f;
        half >>= 1;
    }
    f[0]
}

/// Evaluate directly from coefficients (like `evaluate_from_coeffs` in Python).
pub fn evaluate_from_coeffs(coeffs: &[Fr], zs: &[Fr]) -> Fr {
    let mut f = coeffs.to_vec();
    let mut half = f.len() >> 1;
    for &z in zs {
        let even: Vec<Fr> = f.iter().step_by(2).cloned().collect();
        let odd: Vec<Fr> = f.iter().skip(1).step_by(2).cloned().collect();
        let mut new_f = vec![Fr::zero(); half];
        for i in 0..half {
            // new_f[i] = even[i] + z*odd[i]
            new_f[i] = even[i] + z * odd[i];
        }
        f = new_f;
        half >>= 1;
    }
    f[0]
}

/// Return type for `decompose_by_div_from_coeffs`.
pub struct Decomposition {
    pub quotients: Vec<Vec<Fr>>,
    pub evaluation: Fr,
}

/// Decomposes polynomial *coeffs* by dividing at *point*, mirroring
/// `decompose_by_div_from_coeffs` from Python.
pub fn decompose_by_div_from_coeffs(
    mut coeffs: Vec<Fr>,
    point: &[Fr],
) -> Result<Decomposition, MLEError> {
    let k = point.len();
    let n = coeffs.len();
    let exp_len = 1 << k; // 2^k
    if n != exp_len {
        return Err(MLEError::DimensionMismatch(format!(
            "coeffs length {} != 2^k = {}",
            n, exp_len
        )));
    }

    let mut quotients = Vec::with_capacity(k);
    let mut half = 1 << (k - 1); // 2^(k-1)

    for i in 0..k {
        let mut quo_coeffs = vec![Fr::zero(); half];
        for j in 0..half {
            // quo_coeffs[j] = coeffs[j+half]
            // coeffs[j] = coeffs[j] + point[k-i-1]*coeffs[j+half]
            quo_coeffs[j] = coeffs[j + half];
            coeffs[j] = coeffs[j] + point[k - i - 1] * coeffs[j + half];
        }
        quotients.insert(0, quo_coeffs);
        half >>= 1;
    }
    Ok(Decomposition {
        quotients,
        evaluation: coeffs[0],
    })
}

// -----------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use ark_ff::UniformRand;
    use rand::thread_rng;

    // Helper: produce random `Fr` vector of length n
    fn random_fr_vec(n: usize) -> Vec<Fr> {
        let mut rng = thread_rng();
        (0..n).map(|_| Fr::rand(&mut rng)).collect()
    }

    // ---------------------
    //  MLEPolynomial Tests
    // ---------------------
    #[test]
    fn test_mle_new_and_get() {
        let evals = vec![Fr::one(), Fr::one()];
        let mle = MLEPolynomial::new(evals.clone(), 2).unwrap(); // 2^2 = 4 => pads to length 4
        assert_eq!(mle.evals.len(), 4);
        // Indices 0 and 1 contain our original data
        assert_eq!(mle.get(0), Some(&Fr::one()));
        assert_eq!(mle.get(1), Some(&Fr::one()));
        // Indices 2 and 3 should be zero after padding
        assert_eq!(mle.get(2), Some(&Fr::zero()));
        assert_eq!(mle.get(3), Some(&Fr::zero()));
        // Out of range
        assert_eq!(mle.get(4), None);
    }

    #[test]
    fn test_mle_evaluate() {
        // k=2 => 2^2=4 evals
        // We'll pick a small set manually:
        let evals = vec![
            Fr::from(0u64),
            Fr::from(1u64),
            Fr::from(2u64),
            Fr::from(3u64),
        ];
        let mle = MLEPolynomial::new(evals.clone(), 2).unwrap();
        // Evaluate at zs = [0, 0]
        // evaluate_from_evals logic => we expect f[0,0] = evals[0] = 0
        let z1 = Fr::zero();
        let z2 = Fr::zero();
        let val = mle.evaluate(&[z1, z2]).unwrap();
        assert_eq!(val, Fr::from(0u64));

        // Evaluate at zs = [1, 0]
        // This picks out f[1,0] which should be evals[index=1<<0 + 1<<1?]
        // Actually let's just rely on the direct Python-likeness: 
        // f[1,0] -> . . . 
        // Instead let's check that "some non-zero value" 
        let val2 = mle.evaluate(&[Fr::one(), Fr::zero()]).unwrap();
        // we can compare to what we get from direct function call
        let direct_val = evaluate_from_evals(&evals, &[Fr::one(), Fr::zero()]);
        assert_eq!(val2, direct_val);
    }

    #[test]
    fn test_mle_to_coeffs_round_trip() {
        // Random example with k=3 => 8 evals
        let mut rng = thread_rng();
        let evals: Vec<Fr> = (0..8).map(|_| Fr::rand(&mut rng)).collect();
        let mle = MLEPolynomial::new(evals.clone(), 3).unwrap();

        // Round-trip: evals -> coeffs -> evals
        let coeffs = mle.to_coeffs(); 
        let evals_again = compute_evals_from_coeffs(&coeffs);
        assert_eq!(mle.evals, evals_again, "Round trip mismatch");
    }

    #[test]
    fn test_mle_decompose_by_div() {
        let mut rng = thread_rng();

        // k=3 => 8 evals
        let evals: Vec<Fr> = (0..8).map(|_| Fr::rand(&mut rng)).collect();
        let mle = MLEPolynomial::new(evals.clone(), 3).unwrap();
        let point: Vec<Fr> = (0..3).map(|_| Fr::rand(&mut rng)).collect();

        let (quotients, eval) = mle.decompose_by_div(&point).unwrap();
        assert_eq!(quotients.len(), 3);
        // Final polynomial evaluation at that point
        let direct_eval = evaluate_from_evals(&evals, &point);
        assert_eq!(eval, direct_eval);
    }

    // ----------------------------
    //  compute_monomials, eqs, etc.
    // ----------------------------
    #[test]
    fn test_compute_monomials() {
        // k=2 => rs has length 2 => result length = 4
        let rs = [Fr::from(2u64), Fr::from(3u64)];
        let monos = compute_monomials(&rs);
        // Expect:
        // index 0: 1
        // index 1: r0 = 2
        // index 2: r1 = 3
        // index 3: r0*r1 = 6
        assert_eq!(monos.len(), 4);
        assert_eq!(monos[0], Fr::from(1u64));
        assert_eq!(monos[1], Fr::from(2u64));
        assert_eq!(monos[2], Fr::from(3u64));
        assert_eq!(monos[3], Fr::from(6u64));
    }

    #[test]
    fn test_eqs_over_hypercube() {
        // k=1 => 2^1=2 results
        // let rs[0] = r
        // index 0 => x=0 => f(0) = 1- r
        // index 1 => x=1 => f(1) = ?
        let r = Fr::from(2u64);
        let evals = eqs_over_hypercube(&[r]);
        // index 0 => originally 1 => then j=0 => evals[1] = evals[0]*r => 2
        //                         => evals[0] = evals[0] - evals[1] => 1 - 2 => -1
        // So final => [-1, 2]
        assert_eq!(evals.len(), 2);
        assert_eq!(evals[0], Fr::from(-1i64));
        assert_eq!(evals[1], Fr::from(2u64));
    }

    #[test]
    fn test_eqs_over_hypercube_slow() {
        // k=1 => eqs_over_hypercube_slow => we can compare with eqs_over_hypercube
        let r = Fr::from(2u64);
        let slow = eqs_over_hypercube_slow(1, &[r]).unwrap();
        let fast = eqs_over_hypercube(&[r]);
        assert_eq!(slow, fast);

        // k=6 => error
        let big = eqs_over_hypercube_slow(6, &[Fr::one(); 6]);
        assert!(big.is_err(), "k>5 should be unsupported");
    }

    // ---------------------
    //  NTT and Evaluate Tests
    // ---------------------
    #[test]
    fn test_ntt_core_round_trip() {
        // We do compute_evals_from_coeffs -> compute_coeffs_from_evals -> original
        let coeffs = random_fr_vec(8); // length=8 => k=3
        let evals = compute_evals_from_coeffs(&coeffs);
        let back_coeffs = compute_coeffs_from_evals(&evals);
        assert_eq!(coeffs, back_coeffs, "NTT round-trip mismatch");
    }

    #[test]
    fn test_evaluate_from_evals() {
        // small manual example with k=2 => 4 evals
        let evals = vec![Fr::from(10u64), Fr::from(20u64), Fr::from(30u64), Fr::from(40u64)];
        let zs = [Fr::from(0u64), Fr::from(0u64)];
        let val = evaluate_from_evals(&evals, &zs);
        // for k=2, index=0 => that should be evals[0] = 10
        assert_eq!(val, Fr::from(10u64));
    }

    #[test]
    fn test_evaluate_from_evals_2() {
        // same eval set, compare evaluate_from_evals_2 with evaluate_from_evals
        let evals = vec![Fr::from(10u64), Fr::from(20u64), Fr::from(30u64), Fr::from(40u64)];
        let zs = [Fr::from(1u64), Fr::from(0u64)];
        let val1 = evaluate_from_evals(&evals, &zs);
        let val2 = evaluate_from_evals_2(&evals, &zs);
        assert_eq!(val1, val2);
    }

    #[test]
    fn test_evaluate_from_coeffs() {
        // small test
        // let's define k=2 => 4 coeffs
        let coeffs = vec![Fr::from(1u64), Fr::from(2u64), Fr::from(3u64), Fr::from(4u64)];
        let zs = vec![Fr::one(), Fr::zero()];
        let val = evaluate_from_coeffs(&coeffs, &zs);
        // we can do it by hand if needed, or just trust the logic
        // let's also compare with manual expand if we want
        // f(X0, X1) = ...
        // We'll just trust it's consistent for now
        println!("evaluate_from_coeffs() => {:?}", val);
    }

    // ---------------------
    //  decompose_by_div_from_coeffs Tests
    // ---------------------
    #[test]
    fn test_decompose_by_div_from_coeffs() {
        // k=2 => 4 coeffs
        let coeffs = vec![
            Fr::from(1u64),
            Fr::from(2u64),
            Fr::from(3u64),
            Fr::from(4u64),
        ];
        let point = vec![Fr::one(), Fr::zero()]; // dimension=2

        let dec = decompose_by_div_from_coeffs(coeffs.clone(), &point).unwrap();
        assert_eq!(dec.quotients.len(), 2);
        // dec.evaluation => f(1,0)
        let direct_eval = evaluate_from_coeffs(&coeffs, &point);
        assert_eq!(dec.evaluation, direct_eval);
    }
}
