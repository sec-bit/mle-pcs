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
    pub fn decompose_by_div(
        &self,
        point: &[Fr],
    ) -> Result<(Vec<MLEPolynomial>, Fr), MLEError> {
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
pub fn eqs_over_hypercube_slow(
    k: usize,
    indeterminates: &[Fr],
) -> Result<Vec<Fr>, MLEError> {
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

    #[test]
    fn test_basic_mle() {
        let mut rng = thread_rng();

        // Build a small example polynomial with k=3 => 2^3=8 evals
        let evals: Vec<Fr> = (0..8).map(|_| Fr::rand(&mut rng)).collect();
        let mle = MLEPolynomial::new(evals, 3).unwrap();

        // Just call get
        assert!(mle.get(8).is_none(), "Index out of range should be None");
        assert!(mle.get(0).is_some());

        // Evaluate at some random points
        let zs: Vec<Fr> = (0..3).map(|_| Fr::rand(&mut rng)).collect();
        let val = mle.evaluate(&zs).unwrap();
        println!("MLE evaluate = {:?}", val);

        // Convert to coeffs and back
        let coeffs = mle.to_coeffs();
        let evals_again = compute_evals_from_coeffs(&coeffs);
        assert_eq!(mle.evals, evals_again);
    }
}
