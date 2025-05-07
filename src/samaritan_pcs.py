#!/usr/bin/env python3

# WARNING: This implementation may contain bugs and has not undergone auditing. 
# It is intended for educational and research purposes only. 
# DO NOT use it in a production environment.

from utils import log_2, next_power_of_two
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

# Implementation of Samaritan-PCS [GPS25]:
#
#   [GPS25] Samaritan: Linear-time Prover SNARK from New Multilinear 
#           Polynomial Commitments
#       Author: Chaya Ganesh, Sikhar Patranabis and Nitin Singh
#    - URL: https://eprint.iacr.org/2025/419
# 
# Samaritan-PCS is an MLE polynomial commitment adapter, transforming a
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
#  - [ ] Bivariate polynomial division
#  - [ ] Remove t(1/delta) from the proof

def compute_product_poly(a: list[Field], b: list[Field]):
    assert len(a) == len(b), "Length of a and b must be the same"
    l = len(a)
    s = [Field.zero()] * (2*l-1)
    for i in range(l):
        for j in range(l):
            k = l - 1 + i - j
            s[k] += a[i] * b[j]
    return s[:l-1], s[l:], s[l-1]


class SAMARITAN_PCS:

    def __init__(self, kzg_pcs: KZG10_PCS, debug: int = 0):
        """
        Args:
            pcs: the PedersenCommitment instance to use for the proof
        """
        self.kzg_pcs = kzg_pcs
        self.rng = random.Random("samaritan-pcs")
        self.debug = debug

    def commit(self, f_mle: MLEPolynomial) -> Commitment:
        """
        Commit to a vector of coefficients.
        """

        evals = f_mle.evals
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
        
        # Evaluate f_mle at the point us
        v = f_mle.evaluate(us)
        f_coeffs = f_mle.evals
        
        # > Round 0

        n = 2**k
        l = next_power_of_two(k)
        m = n // l
        log_m = log_2(m)
        us_l = us[:log_m]
        us_r = us[log_m:]
        vec_eq_l = MLEPolynomial.eqs_over_hypercube(us_l)
        vec_eq_r = MLEPolynomial.eqs_over_hypercube(us_r)
    
        # Update transcript with the context
        tr.absorb(b"commitment", f_cm.cm)
        tr.absorb(b"point", us)
        tr.absorb(b"value", v)
        
        # Convert f_mle to univariate polynomial
        f_uni = UniPolynomial(f_coeffs)
        
        # > Round 1.

        # Compute v(X)
        g_vec = [f_coeffs[i*m:(i+1)*m] for i in range(l)]

        v_coeffs = []
        for i in range(l):
            v_coeffs.append(inner_product(g_vec[i], vec_eq_l, Field(0)))
        v_uni = UniPolynomial(v_coeffs)

        # Compute a(X) and b(X)
        b_coeffs, a_coeffs, v2 = compute_product_poly(v_coeffs, vec_eq_r)
        a_uni = UniPolynomial(a_coeffs)
        b_uni = UniPolynomial(b_coeffs)
        
        if self.debug > 1:
            print(f"P> check: a(X) and b(X)")
            r = Field.rand()
            v_at_r = v_uni.evaluate(r)
            p1_at_r = UniPolynomial(vec_eq_r[::-1]).evaluate(r)
            a_at_r = a_uni.evaluate(r)
            b_at_r = b_uni.evaluate(r)
            assert v_at_r * p1_at_r == r**(int(l))*a_at_r + v*r**(int(l-1)) + b_at_r
            print(f"P> check: a(X) and b(X) passed")
            
        # Commit to a(X) and v(X)
        a_cm = self.kzg_pcs.commit(a_uni)
        v_cm = self.kzg_pcs.commit(v_uni)

        # Send `[a(X)]` and `[v(X)]` to the verifier

        tr.absorb(b"v_commitment", v_cm.cm)
        tr.absorb(b"a_commitment", a_cm.cm)

        # > Round 2.

        # Receive challenge alpha, for polynomial aggregation
        gamma = tr.squeeze(Field, b"gamma", 4)
        if self.debug > 0:
            print(f"P> gamma = {gamma}")

        # Evalauate v(gamma)
        v_at_gamma = v_uni.evaluate(gamma)

        # Compute r(X) and h(X)

        divisor = [-gamma] + [Field.zero()] * (m-1) + [Field.one()]
        r_coeffs, p_coeffs = UniPolynomial.polynomial_division_with_remainder(f_coeffs, divisor)

        r_uni = UniPolynomial(r_coeffs)
        p_uni = UniPolynomial(p_coeffs)

        if self.debug > 1:
            print(f"P> check: quotient polynomial q(X) and remainder polynomial g(X)")
            q, r = f_uni.div_by_binomial(gamma, m)
            assert q == r_coeffs, f"q: {q}, r_coeffs: {r_coeffs}"
            print(f"P> check: quotient polynomial q(X) passed")
            assert r == p_coeffs, f"r: {r}, p_coeffs: {p_coeffs}"
            print(f"P> check: remainder polynomial g(X) passed")

        # Compute h(X) and u(X)
        u_coeffs, h_coeffs, v3 = compute_product_poly(p_coeffs, vec_eq_l)
        u_uni = UniPolynomial(u_coeffs)
        h_uni = UniPolynomial(h_coeffs)
        u_coeffs, h_coeffs, v3

        if self.debug > 1:
            print(f"P> check: h(X) and u(X)")
            assert v3 == v_at_gamma, f"v3: {v3}, v_at_gamma: {v_at_gamma}"
            r = Field.rand()
            p_at_r = p_uni.evaluate(r)
            e1_at_r = UniPolynomial(vec_eq_l[::-1]).evaluate(r)
            u_at_r = u_uni.evaluate(r)
            h_at_r = h_uni.evaluate(r)
            assert p_at_r * e1_at_r == r**(int(m))*h_at_r + v_at_gamma*r**(int(m-1)) + u_at_r
            print(f"P> check: h(X) and u(X) passed")

        # Commit and send p(X), r(X) and h(X)
        p_cm = self.kzg_pcs.commit(p_uni)
        r_cm = self.kzg_pcs.commit(r_uni)
        h_cm = self.kzg_pcs.commit(h_uni)

        tr.absorb(b"p_commitment", p_cm.cm)
        tr.absorb(b"r_commitment", r_cm.cm)
        tr.absorb(b"h_commitment", h_cm.cm)
        tr.absorb(b"v_at_gamma", v_at_gamma)

        # > Round 3.

        # Get evaluation challenge
        beta = tr.squeeze(Field, b"beta", 4)
        if self.debug > 0:
            print(f"P> beta = {beta}")

        # Compute t(X) where t(X) = X^{m-1}p(1/X) + beta * X^{m-2}u(1/X) + beta^2 * X^{l-2}b(1/X)

        assert p_uni.degree == m-1, f"p_uni.degree: {p_uni.degree}, m: {m}"
        assert u_uni.degree == m-2, f"u_uni.degree: {u_uni.degree}, l: {l}"
        assert b_uni.degree == l-2, f"b_uni.degree: {b_uni.degree}, l: {l}"

        t_uni = UniPolynomial(p_coeffs[::-1]) + Scalar(beta) * UniPolynomial(u_coeffs[::-1]) \
                + Scalar(beta * beta) * UniPolynomial(b_coeffs[::-1])

        if self.debug > 1:
            print(f"P> check: t(X)")
            z = Field.rand()
            z_inv = z.inv()
            t_z = t_uni.evaluate(z)
            p_z = p_uni.evaluate(z_inv)
            u_z = u_uni.evaluate(z_inv)
            b_z = b_uni.evaluate(z_inv)
            assert t_z == z**(int(m-1)) * p_z + beta * z**(int(m-2)) * u_z + beta**(int(2)) * z**(int(l-2)) * b_z
            print(f"P> check: t(X) passed")
        
        # Commit to t(X)
        t_cm = self.kzg_pcs.commit(t_uni)

        # Send `[t(X)]` to the verifier
        tr.absorb(b"t_commitment", t_cm.cm)

        ## >. Round 4.

        # Get evaluation challenge
        delta = tr.squeeze(Field, b"delta", 4)
        if self.debug > 0:
            print(f"P> delta = {delta}")
        
        delta_inv = delta.inv()

        # Evaluate t(X) at delta_inv
        t_at_delta_inv = t_uni.evaluate(delta_inv)
        # Evaluate f(X), p(X), h(X), v(X) and a(X) at delta
        f_at_delta = f_uni.evaluate(delta)
        p_at_delta = p_uni.evaluate(delta)
        h_at_delta = h_uni.evaluate(delta)
        v_at_delta = v_uni.evaluate(delta)
        a_at_delta = a_uni.evaluate(delta)


        # Send the evaluations above to the verifier
        tr.absorb(b"t_at_delta_inv", t_at_delta_inv)
        tr.absorb(b"f_at_delta", f_at_delta)
        tr.absorb(b"p_at_delta", p_at_delta)
        tr.absorb(b"h_at_delta", h_at_delta)
        tr.absorb(b"v_at_delta", v_at_delta)
        tr.absorb(b"a_at_delta", a_at_delta)

        # > Round 5.

        eta = tr.squeeze(Field, b"eta", 4)
        if self.debug > 0:
            print(f"P> eta = {eta}")
        
        # Compute the aggregated polynomial w(X)
        w_uni = f_uni + Scalar(eta) * p_uni + Scalar(eta*eta) * h_uni \
            + Scalar(eta*eta*eta) * v_uni + Scalar(eta*eta*eta*eta) * a_uni \
            + Scalar(eta*eta*eta*eta*eta) * r_uni

        if self.debug > 1:
            print(f"P> check: w(X)")
            w_at_delta = w_uni.evaluate(delta)
            r_at_delta = (f_at_delta - p_at_delta) / (delta**(int(m)) - gamma)
            assert r_uni.evaluate(delta) == r_at_delta, f"r_at_delta: {r_at_delta}"
            w_eval = f_at_delta + eta * p_at_delta + eta**(int(2)) * h_at_delta + \
                eta**(int(3)) * v_at_delta + eta**(int(4)) * a_at_delta + \
                eta**(int(5)) * r_at_delta
            assert w_at_delta == w_eval, f"w_at_delta: {w_at_delta}, w_eval: {w_eval}"
            print(f"P> check: w(X) passed")

        # Construct the proof arguments

        w_at_delta, w_at_delta_arg = self.kzg_pcs.prove_evaluation(w_uni, delta)
        v_at_gamma, v_at_gamma_arg = self.kzg_pcs.prove_evaluation(v_uni, gamma)
        t_at_delta_inv, t_at_delta_inv_arg = self.kzg_pcs.prove_evaluation(t_uni, delta_inv)

        if self.debug > 1:
            print(f"P> check: aggregate evaluation proofs")
            w_cm = f_cm.cm + p_cm.cm.ec_mul(eta) + h_cm.cm.ec_mul(eta*eta) \
                + v_cm.cm.ec_mul(eta*eta*eta) + a_cm.cm.ec_mul(eta*eta*eta*eta) \
                + r_cm.cm.ec_mul(eta*eta*eta*eta*eta)
            
            p1_uni = UniPolynomial(vec_eq_l[::-1])
            p2_uni = UniPolynomial(vec_eq_r[::-1])
            u_at_delta = p_at_delta * p1_uni.evaluate(delta) - delta**(int(m)) * h_at_delta - v_at_gamma * delta**(int(m-1))
            b_at_delta = v_at_delta * p2_uni.evaluate(delta) - delta**(int(l)) * a_at_delta - v * delta**(int(l-1))
            
            assert t_at_delta_inv == delta_inv**(int(m-1)) * p_at_delta \
                + beta * delta_inv**(int(m-2)) * u_at_delta \
                + beta**(int(2)) * delta_inv**(int(l-2)) * b_at_delta, f"t_at_delta_inv: {t_at_delta_inv}"
            
            checked1 = self.kzg_pcs.verify_evaluation(Commitment(w_cm), delta, w_at_delta, w_at_delta_arg)
            checked2 = self.kzg_pcs.verify_evaluation(v_cm, gamma, v_at_gamma, v_at_gamma_arg)
            checked3 = self.kzg_pcs.verify_evaluation(t_cm, delta_inv, t_at_delta_inv, t_at_delta_inv_arg)
            assert checked1 and checked2 and checked3, f"checked1: {checked1}, checked2: {checked2}, checked3: {checked3}"
            print(f"P> check: aggregate evaluation proofs passed")

        return v, {
            'v_commitment': v_cm,  # Round 1
            'a_commitment': a_cm,  # Round 1
            'p_commitment': p_cm,  # Round 2
            'r_commitment': r_cm,  # Round 2
            'h_commitment': h_cm,  # Round 2
            'v_at_gamma'  : v_at_gamma,        # Round 2
            't_commitment': t_cm,  # Round 3
            't_at_delta_inv': t_at_delta_inv,  # Round 4
            'f_at_delta': f_at_delta,          # Round 4
            'p_at_delta': p_at_delta,          # Round 4
            'h_at_delta': h_at_delta,          # Round 4
            'v_at_delta': v_at_delta,          # Round 4
            'a_at_delta': a_at_delta,          # Round 4
            'w_at_delta_arg': w_at_delta_arg,  # Round 5
            'v_at_gamma_arg': v_at_gamma_arg,  # Round 5
            't_at_delta_inv_arg': t_at_delta_inv_arg, # Round 5
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
        v_cm = arg['v_commitment']
        a_cm = arg['a_commitment']
        p_cm = arg['p_commitment']
        r_cm = arg['r_commitment']
        h_cm = arg['h_commitment']
        v_at_gamma = arg['v_at_gamma']
        t_cm = arg['t_commitment']
        t_at_delta_inv = arg['t_at_delta_inv']
        f_at_delta = arg['f_at_delta']
        p_at_delta = arg['p_at_delta']
        h_at_delta = arg['h_at_delta']
        v_at_delta = arg['v_at_delta']
        a_at_delta = arg['a_at_delta']
        w_at_delta_arg = arg['w_at_delta_arg']
        v_at_gamma_arg = arg['v_at_gamma_arg']
        t_at_delta_inv_arg = arg['t_at_delta_inv_arg']

        # > Round 0

        n = 2**k
        l = next_power_of_two(k)
        m = n // l
        log_m = log_2(m)
        us_l = us[:log_m]
        us_r = us[log_m:]
        vec_eq_l = MLEPolynomial.eqs_over_hypercube(us_l)
        vec_eq_r = MLEPolynomial.eqs_over_hypercube(us_r)

        tr.absorb(b"commitment", f_cm.cm)
        tr.absorb(b"point", us)
        tr.absorb(b"value", v)

        # > Round 1

        tr.absorb(b"v_commitment", v_cm.cm)
        tr.absorb(b"a_commitment", a_cm.cm)

        # > Round 2

        gamma = tr.squeeze(Field, b"gamma", 4)
        if self.debug > 0:
            print(f"V> gamma = {gamma}")

        tr.absorb(b"p_commitment", p_cm.cm)
        tr.absorb(b"r_commitment", r_cm.cm)
        tr.absorb(b"h_commitment", h_cm.cm)
        tr.absorb(b"v_at_gamma", v_at_gamma)

        # > Round 3

        beta = tr.squeeze(Field, b"beta", 4)
        if self.debug > 0:
            print(f"V> beta = {beta}")

        tr.absorb(b"t_commitment", t_cm.cm)

        # > Round 4

        delta = tr.squeeze(Field, b"delta", 4)
        if self.debug > 0:
            print(f"V> delta = {delta}")
        delta_inv = delta.inv()        

        tr.absorb(b"t_at_delta_inv", t_at_delta_inv)
        tr.absorb(b"f_at_delta", f_at_delta)
        tr.absorb(b"p_at_delta", p_at_delta)
        tr.absorb(b"h_at_delta", h_at_delta)
        tr.absorb(b"v_at_delta", v_at_delta)
        tr.absorb(b"a_at_delta", a_at_delta)

        # > Round 5

        eta = tr.squeeze(Field, b"eta", 4)
        if self.debug > 0:
            print(f"V> eta = {eta}")


        p1_uni = UniPolynomial(vec_eq_l[::-1])
        p2_uni = UniPolynomial(vec_eq_r[::-1])
        u_at_delta = p_at_delta * p1_uni.evaluate(delta) - delta**(int(m)) * h_at_delta - v_at_gamma * delta**(int(m-1))
        b_at_delta = v_at_delta * p2_uni.evaluate(delta) - delta**(int(l)) * a_at_delta - v * delta**(int(l-1))
        
        r_at_delta = (f_at_delta - p_at_delta) / (delta**(int(m)) - gamma)

        w_at_delta = f_at_delta + eta * p_at_delta + eta**(int(2)) * h_at_delta + \
                eta**(int(3)) * v_at_delta + eta**(int(4)) * a_at_delta + \
                eta**(int(5)) * r_at_delta

        w_cm = f_cm.cm + p_cm.cm.ec_mul(eta) + h_cm.cm.ec_mul(eta*eta) \
                + v_cm.cm.ec_mul(eta*eta*eta) + a_cm.cm.ec_mul(eta*eta*eta*eta) \
                + r_cm.cm.ec_mul(eta*eta*eta*eta*eta)
        
        # > Verification

        checked0 = t_at_delta_inv == delta_inv**(int(m-1)) * p_at_delta \
                + beta * delta_inv**(int(m-2)) * u_at_delta \
                + beta**(int(2)) * delta_inv**(int(l-2)) * b_at_delta
        if self.debug > 0:
            print(f"V> check: t(1/delta)")
            assert checked0
            print(f"V> check: t(1/delta) passed")

        checked1 = self.kzg_pcs.verify_evaluation(Commitment(w_cm), delta, w_at_delta, w_at_delta_arg)
        
        if self.debug > 0:
            print(f"V> check: w(delta)")
            assert checked1
            print(f"V> check: w(delta) passed")

        checked2 = self.kzg_pcs.verify_evaluation(v_cm, gamma, v_at_gamma, v_at_gamma_arg)
        
        if self.debug > 0:
            print(f"V> check: v(gamma)")
            assert checked2
            print(f"V> check: v(gamma) passed")
        
        checked3 = self.kzg_pcs.verify_evaluation(t_cm, delta_inv, t_at_delta_inv, t_at_delta_inv_arg)
        
        if self.debug > 0:
            print(f"V> check: t(1/delta)")
            assert checked3
            print(f"V> check: t(1/delta) passed")

        return checked0 and checked1 and checked2 and checked3


def test_pcs():

    # # initialize the PedersenCommitment and the IPA_PCS
    kzg = KZG10_PCS(G1Point, G2Point, Field, 32)
    kzg.debug = True

    pcs = SAMARITAN_PCS(kzg, debug = 1)

    tr = MerlinTranscript(b"samaritan-pcs")

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
    v, arg = pcs.prove_eval(f_cm, f_mle, us, tr.fork(b"samaritan_pcs"))
    print("ℹ️ Proof generated.")

    assert v == y
    print("🕐 Verifying proof ....")
    checked = pcs.verify_eval(f_cm, us, v, arg, tr.fork(b"samaritan_pcs"))
    assert checked
    print("✅ Proof verified")

if __name__ == "__main__":
    test_pcs()