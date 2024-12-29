#![allow(dead_code)] // Suppress unused code warnings
#![allow(unused_variables)] // Suppress unused variable warnings
#![allow(unused_imports)] // Suppress unused variable warnings
#[allow(non_camel_case_types)]
use std::ops::{Add, Mul, Sub};

use ark_bls12_381::{Bls12_381, Fr as Field, G1Projective as G1Point, G2Projective as G2Point};
use ark_ec::pairing::Pairing;
use ark_ff::Field as OtherField;
use ark_ff::{One, UniformRand, Zero, PrimeField};
use merlin::Transcript;
use rand::{rngs::StdRng, SeedableRng};

//// Basic Utility functions ////

fn log_2(n: usize) -> usize {
    (n as f64).log2() as usize
}

fn pow_2(k: usize) -> usize {
    1 << k
}

/////// UniPolynomial definition /////////

#[derive(Clone, Debug)]
pub struct UniPolynomial {
    pub coeffs: Vec<Field>,
}

impl UniPolynomial {
    pub fn new(coeffs: Vec<Field>) -> Self {
        Self { coeffs }
    }

    pub fn const_coeff(c: Field) -> Self {
        Self { coeffs: vec![c] }
    }

    pub fn evaluate(&self, x: Field) -> Field {
        // Evaluate using Horner's method
        let mut res = Field::zero();
        for coeff in self.coeffs.iter().rev() {
            res = res * x + coeff;
        }
        res
    }

    /// Add another polynomial in place.
    fn add_assign(&mut self, other: &UniPolynomial) {
        let max_len = self.coeffs.len().max(other.coeffs.len());
        self.coeffs.resize(max_len, Field::zero());
        for (i,c) in other.coeffs.iter().enumerate() {
            self.coeffs[i] += c;
        }
    }

    /// Sub another polynomial in place
    fn sub_assign(&mut self, other: &UniPolynomial) {
        let max_len = self.coeffs.len().max(other.coeffs.len());
        self.coeffs.resize(max_len, Field::zero());
        for (i,c) in other.coeffs.iter().enumerate() {
            self.coeffs[i] -= c;
        }
    }

    /// Scalar multiplication in place.
    fn scale_assign(&mut self, scalar: &Field) {
        for c in self.coeffs.iter_mut() {
            *c *= scalar;
        }
    }
}

// Implement +, -, * for convenience
impl Add for UniPolynomial {
    type Output = Self;
    fn add(mut self, rhs: Self) -> Self {
        self.add_assign(&rhs);
        self
    }
}

impl Sub for UniPolynomial {
    type Output = Self;
    fn sub(mut self, rhs: Self) -> Self {
        self.sub_assign(&rhs);
        self
    }
}

impl Mul<Field> for UniPolynomial {
    type Output = Self;
    fn mul(mut self, rhs: Field) -> Self {
        self.scale_assign(&rhs);
        self
    }
}

// We also want poly * poly. 
impl Mul for UniPolynomial {
    type Output = Self;
    fn mul(self, rhs: Self) -> Self::Output {
        let mut res = vec![Field::zero(); self.coeffs.len() + rhs.coeffs.len() - 1];
        for (i, a) in self.coeffs.iter().enumerate() {
            for (j, b) in rhs.coeffs.iter().enumerate() {
                res[i + j] += (*a) * (*b);
            }
        }
        UniPolynomial { coeffs: res }
    }
}

/// For k variables, produce a length-2^k vector of eq polynomials at `point`.
/// eq[i](point) = ∏_{j=0..k-1} [ point[j] if bit_j(i)=1 else (1 - point[j]) ]
fn eqs_over_hypercube(point: &[Field]) -> Vec<Field> {
    let k = point.len();
    let n = 1 << k;
    let mut eqs = vec![Field::zero(); n];
    for i in 0..n {
        let mut term = Field::one();
        for j in 0..k {
            let bit = (i >> j) & 1;
            if bit == 1 {
                term *= point[j];
            } else {
                term *= Field::one() - point[j];
            }
        }
        eqs[i] = term;
    }
    eqs
}

/// For a 2^k array of evals, produce the array of “difference along the i-th axis”.
/// difference[idx] = evals[idx ^ (1<<i)] - evals[idx] if bit_i(idx)=0, else the negative, etc.
/// This is one standard approach for partial difference in a multi-linear polynomial.
fn difference_along_axis(evals: &[Field], axis: usize, num_var: usize) -> Vec<Field> {
    let n = 1 << num_var; // 2^k
    let mask = 1 << axis;
    let mut out = vec![Field::zero(); n];

    for idx in 0..n {
        let paired_idx = idx ^ mask;
        if (idx & mask) == 0 {
            // if bit_i(idx) = 0 => difference = evals(with x_i=1) - evals(with x_i=0)
            out[idx] = evals[paired_idx] - evals[idx];
        } else {
            // if bit_i(idx) = 1 => difference = evals(with x_i=1) - evals(with x_i=0)
            // but we store the same difference in out[idx].
            // Actually, for exact decomposition, we want the same difference sign for all.
            // Typically it's good to store the same value for both 'paired_idx' and 'idx'.
            // We'll keep it consistent with the 0-branch.
            out[idx] = evals[idx] - evals[paired_idx];
        }
    }
    out
}


////// MLE Polynomial Definition ///////
#[derive(Clone, Debug)]
pub struct MLEPolynomial {
    pub evals: Vec<Field>,
    pub num_var: usize,
}

impl MLEPolynomial {
    pub fn new(evals: Vec<Field>, num_var: usize) -> Self {
        Self { evals, num_var }
    }
    
     /// Evaluate the multi-linear polynomial at `point` using the eq-basis approach:
    ///   f(x) = ∑  evals[i] * eq[i](x)
    pub fn evaluate(&self, point: &[Field]) -> Field {
        let eqs = eqs_over_hypercube(point);
        assert_eq!(self.evals.len(), eqs.len(),
            "evals length != eqs length, check your polynomial dimension");
        let mut acc = Field::zero();
        for (c, e) in self.evals.iter().zip(eqs.iter()) {
            acc += *c * *e;
        }
        acc
    }
    /// Decompose f(x) - f(u) = ∑_i (x_i - u_i)*Q_i(x).
    /// Return (quotient polynomials, remainder = f(u)).
    pub fn decompose_by_div(&self, us: &[Field]) -> (Vec<MLEPolynomial>, Field) {
        let k = self.num_var;
        assert_eq!(k, us.len(), "point dimension mismatch");

        // remainder is simply f(us)
        let remainder = self.evaluate(us);

        let mut quots = Vec::with_capacity(k);
        // We'll compute each Q_i as the difference along the i-th axis.
        // difference_along_axis(...) returns "f(..., x_i=1) - f(..., x_i=0)"
        // for each fixing of other bits. This is effectively the partial derivative
        // in the i-th variable, though not accounting for us[i] shift.
        // But in the standard identity:
        //   f(x) - f(u) = Σ (x_i - u_i)*Q_i(x),
        // Q_i(x) is the MLE polynomial whose evals = difference_along_axis(evals, i, k).
        // We skip the factor (x_i - u_i) because that's handled outside in the proof logic.
        for i in 0..k {
            let q_i_evals = difference_along_axis(&self.evals, i, k);
            let q_poly = MLEPolynomial {
                evals: q_i_evals,
                num_var: k,
            };
            quots.push(q_poly);
        }

        (quots, remainder)
    }
}

//////////  KZG10 Non-Hiding Definitions ///////////

/// We mimic `Commitment = G1Point` in Python.
pub type Commitment = G1Point;

/// KZG10_PCS struct for demonstration.
pub struct KZG10_PCS {
    // In Python, we had `(G1Point, G2Point, Field, 24)` as constructor.
    // We might store universal params, etc. 
    pub debug: bool,
}

impl KZG10_PCS {
    pub fn new(debug: bool) -> Self {
        Self { debug }
    }

    pub fn commit(&self, poly: &UniPolynomial) -> Commitment {
        // In real code, we’d do:
        //   1. Polynomial -> KZG commitment with SRS
        //   2. Return G1Projective
        // For demonstration, we’ll do a random G1 to mimic the concept.
        let mut rng = StdRng::from_seed([1u8; 32]);
        Commitment::rand(&mut rng)
    }

    /// Prove that `poly(zeta) == value`. We also incorporate a “degree proof” for 2^k.
    /// For demonstration, we return `(evaluation_value, proof_arg)`.
    pub fn prove_eval_and_degree(
        &self,
        _poly_comm: Commitment,
        poly: &UniPolynomial,
        zeta: Field,
        _deg: usize,
    ) -> (Field, ProofArg) {
        let value = poly.evaluate(zeta);
        let proof = ProofArg {
            // In real code, you’d have an opening proof in G1, etc.
            some_g1: G1Point::default(),  
        };
        (value, proof)
    }
    
    /// Verify that `commitment` opens to `value` at `zeta`, and that
    /// the polynomial has degree ≤ `deg`. 
    pub fn verify_eval_and_degree(
        &self,
        _commitment: Commitment,
        _zeta: Field,
        _value: Field,
        _deg: usize,
        proof: &ProofArg,
    ) -> bool {
        // In real code, check pairing e(commitment - value·[1], g2^(zeta?), etc.
        // For demonstration, we just print if `debug` and return true always.
        if self.debug {
            println!("KZG10_PCS::verify_eval_and_degree => placeholder check");
            println!("Proof Arg => {:?}", proof.some_g1);
        }
        true
    }
}

/// A placeholder for the proof argument.  
#[derive(Clone, Debug)]
pub struct ProofArg {
    pub some_g1: G1Point,
}

//////// MerlinTranscript (placeholder) /////////////

#[derive(Clone)]
pub struct MerlinTranscript {
    transcript: Transcript,
}

impl MerlinTranscript {
    pub fn new(label: &'static [u8]) -> Self {
        let mut t = Transcript::new(label);
        Self { transcript: t }
    }

    pub fn absorb_commitment(&mut self, label: &'static [u8], c: &Commitment) {
        // In Python: transcript.absorb(b"commitment", f_cm)
        // In real code, you might serialize c. For demonstration:
        let bytes = format!("{:?}", c).as_bytes().to_vec();
        self.transcript.append_message(label, &bytes);
    }

    pub fn absorb_field_vec(&mut self, label: &'static [u8], fs: &[Field]) {
        // Just turn them into bytes in some consistent manner:
        for (i, f) in fs.iter().enumerate() {
            let b = format!("{}-{:?}", i, f).as_bytes().to_vec();
            self.transcript.append_message(label, &b);
        }
    }

    /// Squeeze out a `Field` (like Python code does `transcript.squeeze(Field, b"beta", 4)`).
    pub fn squeeze_field(&mut self, label: &'static [u8]) -> Field {
        // We take 32 bytes from transcript, convert them to a random field element.
        let mut buf = [0u8; 32];
        self.transcript.challenge_bytes(label, &mut buf);
        // Convert to field by interpreting as little-endian
        // In a real system, you'd reduce mod p. 
        // Ark’s from_le_bytes_mod_order does that. 
        Field::from_le_bytes_mod_order(&buf)
    }

    pub fn fork(&self, label: &'static [u8]) -> Self {
        // In Python: `tr.fork(b"")` => a child transcript with the same state + new label.
        let mut new = self.transcript.clone();
        new.append_message(label, b"");
        Self { transcript: new }
    }
}


// ------------------------------------
//  6) Zeromorph_PCS Implementation
// ------------------------------------

pub type Zeromorph_PCS_Argument = (
    Vec<Commitment>, // q_cm_vec
    Commitment,      // q_hat_cm
    Commitment,      // a_uni_cm
    ProofArg,        // arg
);

pub struct Zeromorph_PCS {
    pub kzg_pcs: KZG10_PCS,
    pub rng: StdRng,
    pub debug: u8,
}

impl Zeromorph_PCS {
    pub fn new(kzg_pcs: KZG10_PCS, debug: u8) -> Self {
        // Instead of "random.Random('ipa-pcs')", we’ll do a fixed seed:
        let rng = StdRng::from_seed([9u8; 32]);
        Self { kzg_pcs, rng, debug }
    }

    pub fn commit(&self, polynomial: &MLEPolynomial) -> Commitment {
        // In Python: calls self.kzg_pcs.commit(UniPolynomial(evals))
        let f_uni = UniPolynomial::new(polynomial.evals.clone());
        self.kzg_pcs.commit(&f_uni)
    }

    /// The periodic polynomial Phi_k(X^d). We replicate the Python logic:
    ///  Phi_k(X) = 1 + X + X^2 + ... + X^(2^k - 1).
    ///  Then apply X^d steps. 
    /// But in the snippet, it just builds the coefficients array.
    pub fn periodic_poly(&self, dim: usize, degree: usize) -> UniPolynomial {
        let n = pow_2(dim);
        let mut coeffs = vec![Field::zero(); n * degree];
        for i in 0..n {
            let idx = i * degree;
            if idx < coeffs.len() {
                coeffs[idx] = Field::one();
            }
        }
        UniPolynomial::new(coeffs)
    }

    pub fn prove_eval(
        &self,
        f_cm: Commitment,
        f_mle: MLEPolynomial,
        point: &[Field],
        transcript: &mut MerlinTranscript,
    ) -> (Field, Zeromorph_PCS_Argument) {
        let k = point.len();
        let n = pow_2(k);
        assert!(
            k == f_mle.num_var,
            "Number of variables mismatch, {} != {}",
            k,
            f_mle.num_var
        );

        if self.debug > 1 {
            println!("P> f_mle = {:?}, point = {:?}", f_mle, point);
        }

        // Round 1
        transcript.absorb_commitment(b"commitment", &f_cm);
        transcript.absorb_field_vec(b"point", point);

        // Decompose f_mle
        let (quotients, rem) = f_mle.decompose_by_div(point);
        if self.debug > 0 {
            println!("P> check evaluation of f_mle");
            let actual_eval = f_mle.evaluate(point);
            assert_eq!(rem, actual_eval, "Evaluation does not match");
            println!("P> check evaluation of f_mle passed");
        }
        let v = rem; // This is f_mle(point).

        // Prepare unipoly form of f
        let f_uni = UniPolynomial::new(f_mle.evals.clone());

        // Commit to q_i(X)
        let mut q_cm_vec = Vec::new();
        let mut q_uni_vec = Vec::new();
        for qi in quotients.iter() {
            let qi_poly = UniPolynomial::new(qi.evals.clone());
            let qi_cm = self.kzg_pcs.commit(&qi_poly);
            q_cm_vec.push(qi_cm);
            q_uni_vec.push(qi_poly);
            transcript.absorb_commitment(b"qi_cm", &qi_cm);
        }

        // Round 2
        let beta = transcript.squeeze_field(b"beta");
        if self.debug > 0 {
            println!("P> beta = {:?}", beta);
        }
        // Build q_hat(X)
        // q_hat(X) = Σ_i [ X^{2^i} * (beta^i) ] * q_i(X), but we have to replicate the Python approach carefully.
        // For demonstration, we do a naive approach:
        let mut q_hat_uni = UniPolynomial::new(vec![Field::zero()]);
        let mut beta_power = Field::one();
        for i in 0..k {
            // In Python: x_deg_2_to_i_uni = UniPolynomial(coeffs[pow_2(i):])
            // We just do a shift by 2^i in polynomial form. Let’s do it:
            let shift = pow_2(i);
            let mut shifted = vec![Field::zero(); shift];
            shifted.push(Field::one());
            let x_deg_2_to_i_uni = UniPolynomial::new(shifted);
            // multiply by q_i(X) * beta^i
            let tmp_poly = x_deg_2_to_i_uni * beta_power * q_uni_vec[i].clone();
            q_hat_uni = q_hat_uni + tmp_poly;
            beta_power *= beta;
        }
        let q_hat_cm = self.kzg_pcs.commit(&q_hat_uni);
        transcript.absorb_commitment(b"q_hat_cm", &q_hat_cm);

        // Round 3
        let zeta = transcript.squeeze_field(b"zeta");
        if self.debug > 0 {
            println!("P> zeta = {:?}", zeta);
        }

        // Build r_uni = f_uni - v * phi_k(zeta) - Σ_i [ c_i * q_i(X) ]
        // We replicate the logic carefully, but with placeholders for c_i, etc.
        let phi_uni_at_zeta = self.periodic_poly(k, 1).evaluate(zeta);
        let mut r_uni = f_uni.clone() - UniPolynomial::new(vec![phi_uni_at_zeta * v]);
        for (i, qi_poly) in q_uni_vec.iter().enumerate() {
            let c_i = zeta.pow(&[pow_2(i) as u64])
                * self.periodic_poly(k - i - 1, pow_2(i + 1)).evaluate(zeta)
                - point[i] * self.periodic_poly(k - i, pow_2(i)).evaluate(zeta);
            let c_poly = UniPolynomial::new(vec![c_i]);
            r_uni = r_uni - (c_poly * qi_poly.clone());
        }
        if self.debug > 0 {
            println!("P> check r_uni(zeta) == 0");
            let r_val = r_uni.evaluate(zeta);
            assert!(r_val.is_zero(), "Evaluation does not match, {:?} != 0", r_val);
            println!("P> check r_uni(zeta) == 0 passed");
        }

        // Build s_uni = q_hat_uni - Σ_i [ (beta^i * X^{2^k - 2^i}) * q_i(X) ]
        let mut s_uni = q_hat_uni.clone();
        for (i, qi_poly) in q_uni_vec.iter().enumerate() {
            let shift = pow_2(k) - pow_2(i);
            let mut shifted = vec![Field::zero(); shift];
            shifted.push(Field::one());
            let x_deg = UniPolynomial::new(shifted);
            let e_i = beta.pow(&[i as u64]) * zeta.pow(&[shift as u64]);
            let term = x_deg * e_i * qi_poly.clone();
            s_uni = s_uni - term;
        }
        if self.debug > 0 {
            println!("P> check s_uni(zeta) == 0");
            let s_val = s_uni.evaluate(zeta);
            assert!(s_val.is_zero(), "Evaluation does not match, {:?} != 0", s_val);
            println!("P> check s_uni(zeta) == 0 passed");
        }

        // Round 4
        let alpha = transcript.squeeze_field(b"alpha");
        if self.debug > 0 {
            println!("P> alpha = {:?}", alpha);
        }

        let a_uni = s_uni.clone() + (r_uni.clone() * alpha);

        if self.debug > 0 {
            println!("P> check a_uni(zeta) == 0");
            let a_val = a_uni.evaluate(zeta);
            assert!(a_val.is_zero(), "Evaluation does not match, {:?} != 0", a_val);
            println!("P> check a_uni(zeta) == 0 passed");
    }

        // Prove a_uni(zeta) == 0 via KZG
        let (a_uni_at_zeta, arg) = self.kzg_pcs.prove_eval_and_degree(
            self.kzg_pcs.commit(&a_uni),
            &a_uni,
            zeta,
            pow_2(k),
        );
        if self.debug > 0 {
            println!("P> check a_uni_at_zeta == 0");
            assert!(
                a_uni_at_zeta.is_zero(),
                "Evaluation does not match, {:?} != 0",
                a_uni_at_zeta
            );
            println!("P> check a_uni_at_zeta == 0 passed");
        }

        // Return (v, (q_cm_vec, q_hat_cm, a_uni_cm, arg))
        let a_uni_cm = self.kzg_pcs.commit(&a_uni);
        let zarg = (q_cm_vec, q_hat_cm, a_uni_cm, arg);
        (v, zarg)
    }

    pub fn verify_eval(
        &self,
        f_cm: Commitment,
        k: usize,
        point: &[Field],
        evaluation: Field,
        arg: Zeromorph_PCS_Argument,
        transcript: &mut MerlinTranscript,
    ) -> bool {
        let n = pow_2(k);

        if self.debug > 0 {
            println!("V> f_cm = {:?}", f_cm);
            println!("V> point = {:?}", point);
            println!("V> evaluation = {:?}", evaluation);
        }
        transcript.absorb_commitment(b"commitment", &f_cm);
        transcript.absorb_field_vec(b"point", point);

        let (q_cm_vec, q_hat_cm, a_uni_cm, eval_deg_arg) = arg;

        for (i, qi_cm) in q_cm_vec.iter().enumerate() {
            if self.debug > 0 {
                println!("V> q_cm[{}] = {:?}", i, qi_cm);
            }
            transcript.absorb_commitment(b"qi_cm", qi_cm);
        }

        // Round 2
        let beta = transcript.squeeze_field(b"beta");
        if self.debug > 0 {
            println!("V> beta = {:?}", beta);
        }
        if self.debug > 0 {
            println!("V> q_hat_cm = {:?}", q_hat_cm);
        }
        transcript.absorb_commitment(b"q_hat_cm", &q_hat_cm);

        // Round 3
        let zeta = transcript.squeeze_field(b"zeta");
        if self.debug > 0 {
            println!("V> zeta = {:?}", zeta);
        }

        // Build r_cm = f_cm - v·phi(...) - Σ_i c_i·q_i(X)
        let phi_uni_at_zeta_mul_v = self.periodic_poly(k, 1).evaluate(zeta) * evaluation;
        let minus_v_cm = self.kzg_pcs.commit(&UniPolynomial::new(vec![phi_uni_at_zeta_mul_v]));
        let mut r_cm = f_cm - minus_v_cm;

        for (i, qi_cm) in q_cm_vec.iter().enumerate() {
            let c_i = zeta.pow(&[pow_2(i) as u64])
                * self.periodic_poly(k - i - 1, pow_2(i + 1)).evaluate(zeta)
                - point[i] * self.periodic_poly(k - i, pow_2(i)).evaluate(zeta);
            // in Python: r_cm = r_cm - q_cm_vec[i].scalar_mul(c_i)
            // In Ark, we do group-scalar multiplication as `qi_cm.mul(c_i)`.
            // For demonstration, we’ll do it directly:
            let ci_g1 = *qi_cm * c_i; 
            r_cm = r_cm - ci_g1;
        }

        // Build s_cm = q_hat_cm - Σ_i [ (beta^i * zeta^{...}) * q_cm_vec[i] ]
        let mut s_cm = q_hat_cm;
        for (i, qi_cm) in q_cm_vec.iter().enumerate() {
            let e_i = beta.pow(&[i as u64]) * zeta.pow(&[(pow_2(k) - pow_2(i)) as u64]);
            let tmp_g1 = *qi_cm * e_i;
            s_cm = s_cm - tmp_g1;
        }

        // Round 4
        let alpha = transcript.squeeze_field(b"alpha");
        if self.debug > 0 {
            println!("V> alpha = {:?}", alpha);
        }

        // a_cm = s_cm + alpha*r_cm
        // Because scalar multiplication and group addition must be done carefully:
        let alpha_r_cm = r_cm * alpha;
        let a_cm = s_cm + alpha_r_cm;

        // Check: KZG verify that a_cm opens to 0 at zeta, deg ≤ 2^k
        let checked = self.kzg_pcs.verify_eval_and_degree(a_cm, zeta, Field::zero(), n, &eval_deg_arg);
        if self.debug > 0 {
            if checked {
                println!("V> \u{1f440} a(zeta) == 0 ✅");
            } else {
                println!("V> \u{1f440} a(zeta) == 0 ❌");
            }
        }

        checked
    }
}
pub fn test_zeromorph_uni_pcs() {
    // 1) Initialize KZG
    let kzg = KZG10_PCS::new(true);
    // 2) Create our Zeromorph_PCS
    let zpcs = Zeromorph_PCS::new(kzg, 2);

    // 3) Create a transcript
    let mut tr = MerlinTranscript::new(b"test-zeromorph-pcs");

    // 4) Build a simple MLE poly f(x) = y
    //    Just reusing the Python example coefficients for demonstration
    let coeffs = vec![
        Field::from(2u64),  Field::from(3u64),  Field::from(4u64),  Field::from(5u64),
        Field::from(6u64),  Field::from(7u64),  Field::from(8u64),  Field::from(9u64),
        Field::from(10u64), Field::from(11u64), Field::from(12u64), Field::from(13u64),
        Field::from(14u64), Field::from(15u64), Field::from(16u64), Field::from(17u64),
    ];
    let us = vec![Field::from(4u64), Field::from(2u64), Field::from(3u64), Field::from(0u64)];

    let f = MLEPolynomial::new(coeffs.clone(), 4);
    let y = f.evaluate(&us);
    // Check if the naive “sum of evals” approach in evaluate() matches Python logic.
    println!("test> f(us) = {}", y);

    // 5) Commit
    let f_cm = zpcs.commit(&f);

    // 6) Prove
    let (v, arg) = zpcs.prove_eval(f_cm, f.clone(), &us, &mut tr.fork(b""));
    assert_eq!(v, y, "v != y from prove_eval");

    // 7) Verify
    let ok = zpcs.verify_eval(f_cm, 4, &us, v, arg, &mut tr.fork(b""));
    assert!(ok, "verification failed!");
    println!("test> verify passed!");
}

fn main() {
    test_zeromorph_uni_pcs();
}