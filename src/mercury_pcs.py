#!/usr/bin/env python3

# WARNING: This implementation may contain bugs and has not undergone auditing. 
# It is intended for educational and research purposes only. 
# DO NOT use it in a production environment.

from utils import log_2
from utils import inner_product, Scalar

# WARNING: 
#   1. For demonstration, we deliberately use an insecure random number 
#      generator, random.Random. To generate secure randomness, use 
#      the standard library `secrets` instead.
#        
#      See more here: https://docs.python.org/3/library/secrets.html
#
#   2. Challenges are only 1 byte long for simplicity, which is not secure.

import random

# Implementation of Mercury [EG25]:
#
#   [EG25] MERCURY: A multilinear Polynomial Commitment Scheme with 
#           constant proof size and no prover FFTs.
#       Author: Liam Eagen and Ariel Gabizon
#    - URL: https://eprint.iacr.org/2025/385
# 
# PH23-PCS is an MLE polynomial commitment adapter, transforming a
# unvariate polynomial commitment scheme into a commitment scheme 
# for MLE polynomials. The univariate PCS in this implementation is 
# non-hiding KZG10 (BN254).

from curve import Fr as Field, G1Point, G2Point, ec_pairing_check
from merlin.merlin_transcript import MerlinTranscript
from mle2 import MLEPolynomial
from unipoly2 import UniPolynomial
from kzg10_non_hiding2 import KZG10_PCS, Commitment

# TODO:
#
#  - [ ] Add [BDFG20] optimization
#  - [ ] Add batching

def compute_product_poly(a: list[Field], b: list[Field]):
    assert len(a) == len(b), "Length of a and b must be the same"
    l = len(a)
    s = [Field.zero()] * (l-1)
    dot_product = Field.zero()
    for i in range(l):
        for j in range(l):
            if abs(i-j) == 0:
                dot_product += a[i] * b[j]
            else:
                s[abs(i-j)-1] += a[i] * b[j]
    return s, dot_product

class MERCURY_PCS:

    def __init__(self, kzg_pcs: KZG10_PCS, debug: int = 0):
        """
        Args:
            pcs: the PedersenCommitment instance to use for the proof
        """
        self.kzg_pcs = kzg_pcs
        self.rng = random.Random("mercury-pcs")
        self.debug = debug

    def commit(self, f_mle: MLEPolynomial) -> Commitment:
        """
        Commit to a vector of coefficients.
        """

        evals = f_mle.evals
        log_size = log_2(len(evals))
        cm = self.kzg_pcs.commit(UniPolynomial(evals))

        return cm

    def prove_eval(self, 
                    f_cm: Commitment, 
                    f_mle: MLEPolynomial, 
                    us: list[Field], 
                    tr: MerlinTranscript) -> tuple[Field, dict]:
        """
        Generate evaluation proof for f_mle(us) = v

        Args:
            f_cm: commitment to the polynomial f_mle
            f_mle: the MLE polynomial to prove the evaluation of
            us: the evaluation point
            tr: the transcript to use for the proof

        Returns: (v, arg)
            v: the evaluation of f_mle at us
            arg: the proof argument
        """

        assert f_mle.num_var == len(us), f"f_mle.num_var={f_mle.num_var}, len(us)={len(us)}"
        k = f_mle.num_var
        domain_size = 2**k
        # omega = Field.nth_root_of_unity(domain_size)
        
        # Evaluate f_mle at the point us
        v = f_mle.evaluate(us)
        f_vec = f_mle.evals
        
        # > Round 0
    
        # Update transcript with the context
        tr.absorb(b"commitment", f_cm.cm)
        tr.absorb(b"point", us)
        tr.absorb(b"value", v)
        
        # Convert f_mle to univariate polynomial
        f_uni = UniPolynomial(f_vec)
        
        # > Round 1.

        b = 2**(k//2)
        us_l = us[:k//2]
        us_r = us[k//2:]
        vec_eq_l = MLEPolynomial.eqs_over_hypercube(us_l)
        vec_eq_r = MLEPolynomial.eqs_over_hypercube(us_r)
        n_l = len(vec_eq_l) # column
        n_r = len(vec_eq_r) # row

        # Compute h(X)
        h_coeffs = []
        for i in range(n_r):
            h_coeffs.append(sum([f_mle.evals[i*n_l+j] * vec_eq_l[j] for j in range(n_r)], Field.zero()))
        h_uni = UniPolynomial(h_coeffs)

        # Commit to c(X)  and send it
        h_cm = self.kzg_pcs.commit(h_uni)
        tr.absorb(b"h_commitment", h_cm.cm)
        
        if self.debug > 1:
            print(f"P> check: folded polynomial h(X)")
            coeffs = f_mle.evals
            eqs = MLEPolynomial.eqs_over_hypercube(us)
            lhs = inner_product(h_coeffs, vec_eq_r, Field.zero()) 
            rhs = inner_product(coeffs, eqs, Field.zero())
            assert lhs == rhs, f"lhs: {lhs}, rhs: {rhs}"
            print(f"P> check: folded polynomial h(X) passed")
            
        # > Round 2.

        # Receive challenge alpha, for polynomial aggregation
        alpha = tr.squeeze(Field, b"alpha", 4)
        # alpha = Field(3194597718)
        if self.debug > 0:
            print(f"P> alpha = {alpha}")

        # Construct q(X) and g(X)
        #   where 
        #     f(X) = q(X) * (X^b - alpha) + g(X)
        q_uni, g_uni = f_uni.div_by_binomial(alpha, b)

        if self.debug > 1:
            print(f"P> check: quotient polynomial q(X) and remainder polynomial g(X)")
            divisor = [-alpha] + [Field.zero()] * (b-1) + [Field.one()]
            print(f"P> divisor = {divisor}")
            q, r = UniPolynomial.polynomial_division_with_remainder(f_uni.coeffs, divisor)
            print(f"P> q = {q}, r = {r}")
            assert q == q_uni.coeffs, f"q: {q}, q_uni: {q_uni}"
            print(f"P> check: quotient polynomial q(X) passed")
            assert r == g_uni.coeffs, f"r: {r}, g_uni: {g_uni}"
            print(f"P> check: remainder polynomial g(X) passed")

        # Commit to q(X) and g(X)
        q_cm = self.kzg_pcs.commit(q_uni)
        g_cm = self.kzg_pcs.commit(g_uni)

        # Send `[q(X)]` and `[g(X)]` to the verifier
        tr.absorb(b"q_commitment", q_cm.cm)
        tr.absorb(b"g_commitment", g_cm.cm)

        # > Round 3.

        # Get evaluation challenge
        gamma = tr.squeeze(Field, b"gamma", 4)
        if self.debug > 0:
            print(f"P> gamma = {gamma}")

        s1_coeffs, v1 = compute_product_poly(g_uni.coeffs, vec_eq_l)
        s2_coeffs, v2 = compute_product_poly(h_coeffs, vec_eq_r)
        s1_uni = UniPolynomial(s1_coeffs)
        s2_uni = UniPolynomial(s2_coeffs)
        s_uni = s1_uni + Scalar(gamma) * s2_uni

        if self.debug > 1:
            print(f"P> check: s1(X) and s2(X)")
            assert v1  == h_uni.evaluate(alpha), f"v1: {v1}, h(alpha): {h_uni.evaluate(alpha)}"
            assert v2  == v, f"v1: {v1}, v: {v}"

            z = Field.rand()
            z_inv = z.inv()
            p1_uni = UniPolynomial(vec_eq_l)
            p2_uni = UniPolynomial(vec_eq_r)
            assert g_uni.evaluate(z) * p1_uni.evaluate(z_inv) + g_uni.evaluate(z_inv) * p1_uni.evaluate(z) \
                == Field(2)*v1 + z*s1_uni.evaluate(z) + z_inv*s1_uni.evaluate(z_inv)
            print(f"P> check: s1(X) passed")
            assert h_uni.evaluate(z) * p2_uni.evaluate(z_inv) + h_uni.evaluate(z_inv) * p2_uni.evaluate(z) \
                == Field(2)*v2 + z*s2_uni.evaluate(z) + z_inv*s2_uni.evaluate(z_inv)
            print(f"P> check: s2(X) passed")
        
        # Compute d(X) where d(X) = X^{l-1} * g(1/X)

        d_uni = UniPolynomial(g_uni.coeffs[::-1])

        if self.debug > 1:
            print(f"P> check: d(X)")
            z = Field.rand()
            z_inv = z.inv()
            assert d_uni.evaluate(z) == z**(int(b-1)) * g_uni.evaluate(z_inv), f"d(z): {d_uni.evaluate(z)}, g(1/z): {g_uni.evaluate(z_inv)}"
            print(f"P> check: d(X) passed")

        # Commit to s(X) and d(X)
        s_cm = self.kzg_pcs.commit(s_uni)
        d_cm = self.kzg_pcs.commit(d_uni)

        tr.absorb(b"s_commitment", s_cm.cm)
        tr.absorb(b"d_commitment", d_cm.cm)

        ## >. Round 4.

        # Get evaluation challenge
        zeta = tr.squeeze(Field, b"zeta", 4)
        if self.debug > 0:
            print(f"P> zeta = {zeta}")
        
        zeta_inv = zeta.inv()

        g_at_zeta = g_uni.evaluate(zeta)
        g_at_zeta_inv = g_uni.evaluate(zeta_inv)
        h_at_zeta = h_uni.evaluate(zeta)
        h_at_zeta_inv = h_uni.evaluate(zeta_inv)
        s_at_zeta = s_uni.evaluate(zeta)
        s_at_zeta_inv = s_uni.evaluate(zeta_inv)

        # Compute u(X) = (f(X) - q(X) * (zeta^n_l - alpha) - g(zeta)) / (X - zeta)
        u_uni = f_uni - q_uni * Scalar(zeta**n_l - alpha) - Scalar(g_at_zeta)
        t_uni, t_r = u_uni.div_by_linear_divisor(zeta)

        if self.debug > 1:
            print(f"P> check: quotient polynomial t(X)")
            assert t_r == Field.zero(), f"t_r: {t_r}"

            z = Field.rand()
            t_z = t_uni.evaluate(z)
            f_z = f_uni.evaluate(z)
            q_z = q_uni.evaluate(z)
            assert t_z * (z - zeta) == f_z - q_z * (zeta**n_l - alpha) - g_at_zeta
            print(f"P> check: quotient polynomial t(X) passed")
        
        # Commit to t(X)
        t_cm = self.kzg_pcs.commit(t_uni)

        # Send `[t(X)]` to the verifier
        tr.absorb(b"t_commitment", t_cm.cm)
        tr.absorb(b"g_at_zeta", g_at_zeta)
        tr.absorb(b"g_at_zeta_inv", g_at_zeta_inv)
        tr.absorb(b"h_at_zeta", h_at_zeta)
        tr.absorb(b"h_at_zeta_inv", h_at_zeta_inv)
        tr.absorb(b"s_at_zeta", s_at_zeta)
        tr.absorb(b"s_at_zeta_inv", s_at_zeta_inv)

        # > Round 5.

        eta = tr.squeeze(Field, b"eta", 4)
        if self.debug > 0:
            print(f"P> eta = {eta}")
        
        a_uni = g_uni + Scalar(eta) * h_uni + Scalar(eta*eta) * s_uni
        a_at_zeta_inv, a_at_zeta_inv_arg = self.kzg_pcs.prove_evaluation(a_uni, zeta_inv)

        a_uni += Scalar(eta*eta*eta) * d_uni
        a_at_zeta, a_at_zeta_arg = self.kzg_pcs.prove_evaluation(a_uni, zeta)

        h_at_alpha, h_at_alpha_arg = self.kzg_pcs.prove_evaluation(h_uni, alpha)

        # tr.absorb(b"a_at_zeta_inv_arg", a_at_zeta_inv_arg)
        # tr.absorb(b"a_at_zeta_arg", a_at_zeta_arg)
        # tr.absorb(b"h_at_alpha_arg", h_at_alpha_arg)

        if self.debug > 1:
            print(f"P> check: h(alpha)")
            p1_uni = UniPolynomial(vec_eq_l)
            p2_uni = UniPolynomial(vec_eq_r)
            p1_at_zeta = p1_uni.evaluate(zeta)
            p2_at_zeta = p2_uni.evaluate(zeta)
            p1_at_zeta_inv = p1_uni.evaluate(zeta_inv)
            p2_at_zeta_inv = p2_uni.evaluate(zeta_inv)
            h_alpha = (h_at_zeta * p2_at_zeta_inv) + (h_at_zeta_inv * p2_at_zeta) - v - v
            h_alpha *= gamma 
            h_alpha += (g_at_zeta * p1_at_zeta_inv) + (g_at_zeta_inv * p1_at_zeta)
            h_alpha -= zeta * s_at_zeta + zeta_inv * s_at_zeta_inv

            d_at_zeta = zeta**(int(n_l-1)) * g_at_zeta_inv
            assert d_at_zeta == d_uni.evaluate(zeta), f"d_at_zeta: {d_at_zeta}, d_uni.evaluate(zeta): {d_uni.evaluate(zeta)}"
            assert h_at_alpha * Field(int(2)) == h_alpha, f"h_at_alpha: {h_at_alpha}, h_alpha: {h_alpha}"
            print(f"P> check: h(alpha) passed")

        return v, {
            'h_commitment': h_cm,  # Round 1
            'q_commitment': q_cm,  # Round 2 
            'g_commitment': g_cm,  # Round 2
            's_commitment': s_cm,  # Round 3
            'd_commitment': d_cm,  # Round 3
            't_commitment': t_cm,           # Round 4
            'g_at_zeta': g_at_zeta,            # Round 4
            'g_at_zeta_inv': g_at_zeta_inv,    # Round 4
            'h_at_zeta': h_at_zeta,            # Round 4
            'h_at_zeta_inv': h_at_zeta_inv,    # Round 4
            's_at_zeta': s_at_zeta,            # Round 4
            's_at_zeta_inv': s_at_zeta_inv,    # Round 4
            'a_at_zeta_inv_arg': a_at_zeta_inv_arg, # Round 5
            'a_at_zeta_arg': a_at_zeta_arg,       # Round 5
            'h_at_alpha_arg': h_at_alpha_arg,     # Round 5
        }

    def verify_eval(self, 
                    f_cm: Commitment, 
                    us: list[Field], 
                    v: Field,
                    arg: dict,
                    tr: MerlinTranscript) -> bool:
        """
        Verify the evaluation of a polynomial at a given point.

            arg: `f(us) = v`, 
            
                where f is an MLE polynomial, us is a log-n sized evaluation point.

        Args:
            f_cm: the commitment to the polynomial
            us: the evaluation point
            v: the evaluation value
            arg: the argument generated by the prover
            tr: the proof transcript

        Returns:
            bool: True if the argument is valid, False otherwise
        """
        k = len(us)

        # Load the argument
        h_cm = arg['h_commitment']
        q_cm = arg['q_commitment']
        g_cm = arg['g_commitment']
        s_cm = arg['s_commitment']
        d_cm = arg['d_commitment']
        t_cm = arg['t_commitment']
        g_at_zeta = arg['g_at_zeta']
        g_at_zeta_inv = arg['g_at_zeta_inv']
        h_at_zeta = arg['h_at_zeta']
        h_at_zeta_inv = arg['h_at_zeta_inv']
        s_at_zeta = arg['s_at_zeta']
        s_at_zeta_inv = arg['s_at_zeta_inv']
        a_at_zeta_inv_arg = arg['a_at_zeta_inv_arg']
        a_at_zeta_arg = arg['a_at_zeta_arg']
        h_at_alpha_arg = arg['h_at_alpha_arg']

        # > Round 0

        b = 2**(k//2)
        us_l = us[:k//2]
        us_r = us[k//2:]
        vec_eq_l = MLEPolynomial.eqs_over_hypercube(us_l)
        vec_eq_r = MLEPolynomial.eqs_over_hypercube(us_r)

        tr.absorb(b"commitment", f_cm.cm)
        tr.absorb(b"point", us)
        tr.absorb(b"value", v)

        # > Round 1
        
        tr.absorb(b"h_commitment", h_cm.cm)

        # > Round 2

        alpha = tr.squeeze(Field, b"alpha", 4)
        if self.debug > 0:
            print(f"V> alpha = {alpha}")

        tr.absorb(b"q_commitment", q_cm.cm)
        tr.absorb(b"g_commitment", g_cm.cm)

        # > Round 3

        gamma = tr.squeeze(Field, b"gamma", 4)
        if self.debug > 0:
            print(f"V> gamma = {gamma}")

        tr.absorb(b"s_commitment", s_cm.cm)
        tr.absorb(b"d_commitment", d_cm.cm)

        # > Round 4

        zeta = tr.squeeze(Field, b"zeta", 4)
        zeta_inv = zeta.inv()
        if self.debug > 0:
            print(f"V> zeta = {zeta}")

        p1_uni = UniPolynomial(vec_eq_l)
        p2_uni = UniPolynomial(vec_eq_r)
        p1_at_zeta = p1_uni.evaluate(zeta)
        p2_at_zeta = p2_uni.evaluate(zeta)
        p1_at_zeta_inv = p1_uni.evaluate(zeta_inv)
        p2_at_zeta_inv = p2_uni.evaluate(zeta_inv)

        d_at_zeta = zeta**(int(b-1)) * g_at_zeta_inv
        h_at_alpha = (h_at_zeta * p2_at_zeta_inv) + (h_at_zeta_inv * p2_at_zeta) - v - v
        h_at_alpha *= gamma 
        h_at_alpha += (g_at_zeta * p1_at_zeta_inv) + (g_at_zeta_inv * p1_at_zeta)
        h_at_alpha -= zeta * s_at_zeta + zeta_inv * s_at_zeta_inv
        h_at_alpha /= Field(2)

        tr.absorb(b"t_commitment", t_cm.cm)
        tr.absorb(b"g_at_zeta", g_at_zeta)
        tr.absorb(b"g_at_zeta_inv", g_at_zeta_inv)
        tr.absorb(b"h_at_zeta", h_at_zeta)
        tr.absorb(b"h_at_zeta_inv", h_at_zeta_inv)
        tr.absorb(b"s_at_zeta", s_at_zeta)
        tr.absorb(b"s_at_zeta_inv", s_at_zeta_inv)

        # > Round 5

        eta = tr.squeeze(Field, b"eta", 4)
        if self.debug > 0:
            print(f"V> eta = {eta}")

        C1 = g_cm.cm + h_cm.cm.ec_mul(eta) + s_cm.cm.ec_mul(eta*eta) 
        C2 = C1 + d_cm.cm.ec_mul(eta*eta*eta)
        a_at_zeta_inv = g_at_zeta_inv + h_at_zeta_inv * eta + s_at_zeta_inv * eta*eta
        a_at_zeta = g_at_zeta + h_at_zeta * eta + s_at_zeta * eta*eta + d_at_zeta * eta*eta*eta
        
        # > Verification

        evals_checked = self.kzg_pcs.batch_verify([Commitment(C1), Commitment(C2), h_cm], 
                                  [zeta_inv, zeta, alpha],
                                  [a_at_zeta_inv, a_at_zeta, h_at_alpha],
                                  [a_at_zeta_inv_arg, a_at_zeta_arg, h_at_alpha_arg])
        if self.debug > 1:
            print(f"V> check: batch C1, C2, h_cm")
            checked = self.kzg_pcs.verify_evaluation(Commitment(C1), zeta_inv, a_at_zeta_inv, a_at_zeta_inv_arg)
            assert checked
            checked = self.kzg_pcs.verify_evaluation(Commitment(C2), zeta, a_at_zeta, a_at_zeta_arg)
            assert checked
            checked = self.kzg_pcs.verify_evaluation(h_cm, alpha, h_at_alpha, h_at_alpha_arg)
            assert checked
            print(f"V> check: batch C1, C2, h_cm passed")

        
        g_G1 = self.kzg_pcs.params['g']
        h_tau_G2 = self.kzg_pcs.params['tau_h']
        h_G2 = self.kzg_pcs.params['h']

        lhs1 = f_cm.cm + t_cm.cm.ec_mul(zeta) - q_cm.cm.ec_mul(zeta**b - alpha) - g_G1.ec_mul(g_at_zeta)
        lhs2 = h_G2
        rhs1 = t_cm.cm
        rhs2 = h_tau_G2
        pairing_checked = ec_pairing_check([lhs1, rhs1], [-lhs2, rhs2])
        if self.debug > 1:
            print(f"V> check: pairing")
            assert pairing_checked
            print(f"V> check: pairing passed")

        return evals_checked and pairing_checked

def test_pcs():

    # # initialize the PedersenCommitment and the IPA_PCS
    kzg = KZG10_PCS(G1Point, G2Point, Field, 32)
    kzg.debug = True

    pcs = MERCURY_PCS(kzg, debug = 1)

    tr = MerlinTranscript(b"mercury-pcs")

    # A simple instance f(x) = y
    evals = [Field(2), Field(3), Field(4), Field(5), Field(6), Field(7), Field(8), Field(9), \
             Field(10), Field(11), Field(12), Field(13), Field(14), Field(15), Field(16), Field(17)]
    us = [Field(4), Field(2), Field(3), Field(0)]
    eqs = MLEPolynomial.eqs_over_hypercube(us)
    
    y = inner_product(evals, eqs, Field.zero())
    f_mle = MLEPolynomial(evals, 4)
    assert f_mle.evaluate(us) == y
    print(f"f(x[]) = {y}")
    f_cm = pcs.commit(f_mle)

    print("🕐 Generating proof ....")
    v, arg = pcs.prove_eval(f_cm, f_mle, us, tr.fork(b"mercury_pcs"))
    print("ℹ️ Proof generated.")

    assert v == y
    print("🕐 Verifying proof ....")
    checked = pcs.verify_eval(f_cm, us, v, arg, tr.fork(b"mercury_pcs"))
    assert checked
    print("✅ Proof verified")

if __name__ == "__main__":
    test_pcs()