#!/usr/bin/env python3

# WARNING: This implementation may contain bugs and has not been audited. 
# It is only for research purposes. DO NOT use it in production.

# Implementation of Hyrax-PCS with sqrt(n) commitments from Section 6.1 in [WTSTW17]:
#
#   Hyrax: https://eprint.iacr.org/2017/1132.pdf

# TODO:
# - add batch proving 

from curve import Fr as Field, ec_mul, G1Point as G1
from merlin.merlin_transcript import MerlinTranscript
from mle2 import MLEPolynomial
from utils import log_2

# WARNING: 
#   1. For demonstration, we deliberately use an insecure random number 
#      generator, random.Random. To generate secure randomness, use 
#      the standard library `secrets` instead.
#
#      See more here: https://docs.python.org/3/library/secrets.html
#
#   2. Challenges are only 1 byte long for simplicity, which is not secure.

import random

from ipa import BULLETPROOF_IPA_PCS, PedersenCommitment

class Hyrax_PCS(BULLETPROOF_IPA_PCS):

    def commit(self, vec_a: list[Field]) -> tuple[list[G1], list[Field]]:
        """
        Commit to a vector of coefficients.
        """
        logn = log_2(len(vec_a))
        half = logn // 2
        row, col = 2**half, 2**(logn - half)
        
        print(f"row: {row}, col: {col}")

        blinders = Field.rands(self.rnd_gen, row)

        a_cm = []
        for i in range(row):
            a_row = vec_a[i*row:(i+1)*row]
            a_cm += [self.pcs.commit_with_blinder(a_row, blinders[i])]
        return a_cm, blinders
    
    def batch_inner_product_prove(self, cm_a: list[G1], vec_a: list[Field], blinders: list[Field],
                vec_b0: list[Field], vec_b1: list[Field], v: Field, tr: MerlinTranscript):
        n = len(vec_a)
        col = len(vec_b0)
        row = len(vec_b1)
        assert col * row == n, \
            f"vec_b0 and vec_b1 must have {n} elements, but got {col} and {row}"
        assert len(blinders) == col, f"blinders must have {col} elements, but got {len(blinders)}"

        f_folded = [0] * col
        f_folded_cm = G1.zero()
        blinders_folded = Field(0)
        for i in range(row):
            for j in range(col):
                f_folded[j] += vec_b1[i] * vec_a[i * row + j]
            blinders_folded += vec_b1[i] * blinders[i]
            f_folded_cm += ec_mul(cm_a[i], vec_b1[i])
        
        if self.debug:
            sum_f_folded_vec_b0 = sum([f_folded[i] * vec_b0[i] for i in range(col)])
            if sum_f_folded_vec_b0 == v:
                print(f"batch_inner_product_prove> ipa(f_folded, vec_b0) == v, v={v}")
            else:
                print(f"batch_inner_product_prove> ipa(f_folded, vec_b0) must be {v}, but got {sum_f_folded_vec_b0}")

            if self.pcs.commit_with_blinder(f_folded, blinders_folded) == f_folded_cm:
                print(f"batch_inner_product_prove> cm(f_folded) + cm(blinders_folded) == f_folded_cm")
            else:
                print(f"batch_inner_product_prove> cm(G, f_folded) + cm(H, blinders_folded) must be {f_folded_cm}, but got {self.pcs.commit_with_pp(G, f_folded) + ec_mul(H, blinders_folded)}")

        arg = self.inner_product_prove(f_folded_cm, f_folded, blinders_folded, vec_b0, v, tr)
        return arg
    
    def batch_inner_product_verify(self, cm_a: list[G1], vec_b0: list[Field], vec_b1: list[Field], v: Field,
                arg: tuple[int,G1, G1, G1, list[Field]], tr: MerlinTranscript) -> bool:

        col = len(vec_b0)
        row = len(vec_b1)

        f_folded_cm = G1.zero()
        for i in range(row):
            f_folded_cm += ec_mul(cm_a[i], vec_b1[i])
        verified = self.inner_product_verify(f_folded_cm, vec_b0, v, arg, tr)
        return verified

    def prove_evaluation(self, f_cm: G1, us: list[Field], v: Field, f: MLEPolynomial, blinders_f: list[Field], \
                tr: MerlinTranscript) -> tuple[int,G1, G1, G1, list[Field]]:
        """
        Prove that an MLE polynomial f(u0, u1, ..., u_{n-1}) = v.

            f(X0, X1, ..., X_{n-1}) = a0 * eq(bits(0), X0, X1, ..., X_{n-1}) 
                                    + a1 * eq(bits(1), X0, X1, ..., X_{n-1}) 
                                    + ... 
                                    + a_{2^n-1} * eq(bits(2^n-1), X0, X1, ..., X_{n-1})

        Args:
            f_cm: the commitment to the MLE polynomial f(X0, X1, ..., X_{n-1})
            us: the evaluation point (u0, u1, ..., u_{n-1})
            v: the evaluation of f(u0, u1, ..., u_{n-1})
            f: the MLE polynomial in evaluation form
            blinders_f: the blinding factors for the commitment to f
            tr: the Merlin transcript to use for the proof
            debug: whether to print debug information
        Returns:
            an IPA_PCS_Argument tuple
        """

        k = f.num_var
        assert len(us) == k, f"us must have {k} elements, but got {len(us)}"

        us_l = us[:k//2]
        us_r = us[k//2:]
        vec_eq_l = MLEPolynomial.eqs_over_hypercube(us_l)
        vec_eq_r = MLEPolynomial.eqs_over_hypercube(us_r)
        
        if self.debug > 1:
            vec_eq = MLEPolynomial.eqs_over_hypercube(us)
            sum_fevals_eq = sum([f.evals[i] * vec_eq[i] for i in range(len(f.evals))])
            assert v == sum_fevals_eq, f"v must be {sum_fevals_eq}, but got {v}"
        
        arg = self.batch_inner_product_prove(f_cm, f.evals, blinders_f, vec_eq_l, vec_eq_r, v, tr)
        return arg
        
    def verify_evaluation(self, f_cm: G1, us: list[Field], v: Field, 
                arg: tuple[int,G1, G1, G1, list[Field]], tr: MerlinTranscript) -> bool:
        """
        Verify an evaluation argument for a polynomial f, st. f(x) = y.

            f(X0, X1, ..., X_{n-1}) = a0 * eq(bits(0), X0, X1, ..., X_{n-1}) 
                                    + a1 * eq(bits(1), X0, X1, ..., X_{n-1}) 
                                    + ... 
                                    + a_{2^n-1} * eq(bits(2^n-1), X0, X1, ..., X_{n-1})
        Args:
            f_cm: the commitment to the polynomial f(X)
            us: the evaluation point (u0, u1, ..., u_{n-1})
            v: the evaluation of f(u0, u1, ..., u_{n-1})
            arg: the IPA_PCS_Argument (proof transcript)
            tr: the Merlin transcript to use for the proof
        """
        k = len(us)
        us_l = us[:k//2]
        us_r = us[k//2:]

        vec_eq_l = MLEPolynomial.eqs_over_hypercube(us_l)
        vec_eq_r = MLEPolynomial.eqs_over_hypercube(us_r)
        
        verified = self.batch_inner_product_verify(f_cm, vec_eq_l, vec_eq_r, v, arg, tr)
        return verified

def test_ipa_mle_pcs():

    # initialize the PedersenCommitment and the IPA_PCS
    pc = PedersenCommitment.setup(20)
    hyrax_pcs = Hyrax_PCS(pc)
    hyrax_pcs.debug = True

    tr = MerlinTranscript(b"ipa-mle-pcs")

    # A simple instance f(x) = y
    f = MLEPolynomial([Field(2), Field(3), Field(4), Field(5), Field(6), Field(7), Field(8), Field(9), 
                       Field(10), Field(11), Field(10), Field(11), Field(6), Field(7), Field(8), Field(9)], 4)
    us = [Field(2), Field(3), Field(3), Field(2)]
    v = f.evaluate(us)
    print(f"v: {v}")

    # commit to the polynomial
    cm_f, rho_f = hyrax_pcs.commit(f.evals)

    # fork the transcript for both prover and verifier
    tr_prover = tr.fork(b"test")
    tr_verifier = tr.fork(b"test")

    # prover proves f(x) = y and sends an argument to the verifier
    arg = hyrax_pcs.mle_poly_eval_prove(cm_f, us, v, f, rho_f, tr_prover)
    print(f"arg: {arg}")

    # verifier verifies the argument
    verified = hyrax_pcs.mle_poly_eval_verify(cm_f, us, v, arg, tr_verifier)
    print(f"mle_polycom verified: {verified}")
    assert verified, "MLE polynomial evaluation verification failed"

def test_inner_product():

    # initialize the PedersenCommitment and the IPA_PCS
    pc = PedersenCommitment.setup(20)
    hyrax_pcs = Hyrax_PCS(pc)
    hyrax_pcs.debug = True

    tr = MerlinTranscript(b"ipa-mle-pcs")

    # A simple instance f(x) = y
    vec_b =[Field(6), Field(7), Field(8), Field(9)]
    vec_a = [Field(1), Field(2), Field(3), Field(4)]
    c = sum([vec_a[i] * vec_b[i] for i in range(len(vec_a))])
    print(f"inner product: {c}")

    # commit to the polynomial
    rho_a = Field.rand()
    cm_a = pc.commit_with_blinder(vec_a, rho_a)

    # fork the transcript for both prover and verifier
    tr_prover = tr.fork(b"xx")
    tr_verifier = tr.fork(b"xx")

    # prover proves f(x) = y and sends an argument to the verifier
    arg = hyrax_pcs.inner_product_prove(cm_a, vec_a, rho_a, vec_b, c, tr_prover)
    print(f"arg: {arg}")

    # verifier verifies the argument
    verified = hyrax_pcs.inner_product_verify(cm_a, vec_b, c, arg, tr_verifier)
    print(f"inner_product verified: {verified}")
    assert verified, "inner product verification failed"

if __name__ == "__main__":
    test_inner_product()

    test_ipa_mle_pcs()