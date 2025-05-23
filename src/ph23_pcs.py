#!/usr/bin/env python3

from functools import reduce

# WARNING: This implementation may contain bugs and has not been audited. 
# It is only for educational purposes. DO NOT use it in production.

from utils import log_2, bits_le_with_width
from curve import Fr as Field, G1Point, G2Point, ec_pairing_check
from merlin.merlin_transcript import MerlinTranscript
from mle2 import MLEPolynomial

from unipoly2 import UniPolynomial, UniPolynomialWithFft
from kzg10_non_hiding2 import KZG10_PCS, Commitment

# WARNING: 
#   1. For demonstration, we deliberately use an insecure random number 
#      generator, random.Random. To generate secure randomness, use 
#      the standard library `secrets` instead.
#        
#      See more here: https://docs.python.org/3/library/secrets.html
#
#   2. Challenges are only 1 byte long for simplicity, which is not secure.

import random

# Implementation of PH23-PCS from Section 6.1 in [PH23]:
#
#   [PH23]: Improving logarithmic derivative lookups using GKR.
#       Author: Shahar Papini and Ulrich Haböck
#    - URL: https://eprint.iacr.org/2023/1284.pdf
# 
# PH23-PCS is an MLE polynomial commitment adapter, transforming a
# unvariate polynomial commitment scheme into a commitment scheme 
# for MLE polynomials. The univariate PCS in this implementation is 
# non-hiding KZG10 (BN254).


# TODO:
#
#  - [ ] Add precomputation optimization
#  - [ ] Add debug assertions
#  - [ ] Add batching

PH23_PCS_Argument = tuple[int,G1Point, G1Point, G1Point, list[Field]]

CnstPoly = UniPolynomial.const

class PH23_PCS:

    def __init__(self, kzg_pcs: KZG10_PCS, debug: int = 0):
        """
        Args:
            pcs: the PedersenCommitment instance to use for the proof
        """
        self.kzg_pcs = kzg_pcs
        self.rng = random.Random("ipa-pcs")
        self.debug = debug

    def commit(self, f_mle: MLEPolynomial) -> Commitment:
        """
        Commit to a vector of coefficients.
        """

        evals = f_mle.evals
        logn = log_2(len(evals))
        cm = self.kzg_pcs.commit(UniPolynomialWithFft.interpolate(evals, len(evals)))

        return cm

    def prove_eval(self, 
                    f_cm: Commitment, 
                    f_mle: MLEPolynomial, 
                    us: list[Field], 
                    tr: MerlinTranscript) -> tuple[Field, PH23_PCS_Argument]:
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

        assert f_mle.num_var == len(us), \
            f"f_mle.num_var={f_mle.num_var}, len(us)={len(us)}"
        log_n = f_mle.num_var
        domain_size = 2**log_n
        omega = Field.nth_root_of_unity(domain_size)
        
        # Evaluate f_mle at the point us
        v = f_mle.evaluate(us)
        f_vec = f_mle.evals
        
        # > Round 0
    
        # Update transcript with the context
        tr.absorb(b"commitment", f_cm.cm)
        tr.absorb(b"point", us)
        tr.absorb(b"value", v)
        
        # Convert f_mle to univariate polynomial
        f_poly = UniPolynomialWithFft.interpolate(f_vec, len(f_vec))
        
        # > Round 1.

        # Construct c(X) (whose evaluations are the eq polynomial evaluations)
        c_vec = MLEPolynomial.eqs_over_hypercube(us)
        c_poly = UniPolynomialWithFft.interpolate(c_vec, len(c_vec))

        if self.debug > 1:
            print(f"P> check v")
            inner_prod_c_f = sum([ai * bi for ai, bi in zip(c_vec, f_vec)])
            assert v == inner_prod_c_f, f"v={v}, sum_c_f={inner_prod_c_f}"
            print(f"P> check v passed")

        if self.debug > 1:
            print(f"P> check c_vec")
            for i in range(len(c_vec)):
                i_bits = bits_le_with_width(i, log_n)
                prod = Field.one()
                for j in range(len(i_bits)):
                    if i_bits[j] == Field.one():
                        prod *= us[j]
                    else:
                        prod *= (Field(1) - us[j])
                assert prod == c_vec[i]
            print(f"P> check c_vec passed")
        
        if self.debug > 1:
            print(f"P> check c_poly...")
            for i in range(len(c_vec)):
                assert c_poly.evaluate(omega**i) == c_vec[i]
            print(f"check c_poly passed")

        # Commit to c(X) polynomial
        c_cm = self.kzg_pcs.commit(c_poly)
        tr.absorb(b"c_commitment", c_cm.cm)
        
        # > Round 2.

        # Receive challenge alpha, for polynomial aggregation
        alpha = tr.squeeze(Field, b"alpha", 1)
        if self.debug > 0:
            print(f"P> alpha = {alpha}")

        # Construct vH(X), the vanishing polynomial for domain H
        vH_poly = UniPolynomialWithFft.vanishing_polynomial(domain_size)
        
        # Construct selector polynomials
        s_poly_vec = []
        for k in range(log_n):
            vH_k = UniPolynomialWithFft.vanishing_polynomial(2**k)
            s_poly, r_poly = divmod(vH_poly, vH_k)
            assert r_poly.is_zero(), f"r_poly={r_poly}, r_poly.coeffs={r_poly.coeffs}, r_poly.degree={r_poly.degree}, type(r_poly)={type(r_poly)}"
            s_poly_vec.append(s_poly)
            
        # Construct h(X), the overall constraint polynomial
        #
        #    h(X) = p_0(X) + alpha * p_1(X) + ... + alpha^logn * p_{logn-1}(X)
        #          + alpha^{logn+1} * h_1(X) 
        #          + alpha^{logn+2} * h_2(X) 
        #          + alpha^{logn+3} * h_3(X)

        # Define p_0(X) polynomial
        p0_poly = s_poly_vec[0] * (c_poly - CnstPoly(c_vec[0]))
        h_poly = p0_poly
        if self.debug > 1:
            print(f"P> check p0_poly")
            _, r_x = divmod(p0_poly, vH_poly)
            assert r_x.is_zero(), f"p0_poly is not divisible by vH_poly"
            print(f"P> check p0_poly passed")

        # Define p_k(X) polynomials for k=1..logn
        for k in range(1, log_n+1):
            lambda_k = Field.nth_root_of_unity(2**k)
            c_poly_shifted = c_poly.shift(lambda_k)

            if self.debug > 1:
                print(f"P> check c_poly_shifted")
                assert c_poly_shifted.evaluate(omega) == c_poly.evaluate(omega * lambda_k)
                print(f"P> check c_poly_shifted passed")

            g_poly = c_poly * CnstPoly(us[log_n-k]) - (c_poly.shift(lambda_k) * CnstPoly(Field(1) - us[log_n - k]))
            p_poly = s_poly_vec[k-1] * g_poly * CnstPoly(alpha**k)

            if self.debug > 1:
                print(f"P> check divisibility of p_{k}")
                _, r_x = divmod(p_poly, vH_poly)
                assert r_x.is_zero(), f"p_{k} is not divisible by vH"
                print(f"P> check divisibility of p_{k} passed")
            h_poly += p_poly
        
        # Construct z(X), which encodes the sum-accumulators of f[i] * c[i]
        z_vec = []
        z_acc = Field.zero()
        for i in range(domain_size): 
            z_acc += f_vec[i] * c_vec[i]
            z_vec.append(z_acc)

        if self.debug > 1:
            assert z_acc == v, f"z_acc={z_acc}, v={v}"
            print(f"P> check z_acc passed")

        z_poly = UniPolynomialWithFft.interpolate(z_vec, len(z_vec))

        # Construct l0(X) and ln_1(X) lagrange polynomials
        l0_poly = UniPolynomialWithFft.lagrange_polynomial(0, domain_size)
        ln_1_poly = UniPolynomialWithFft.lagrange_polynomial(domain_size-1, domain_size)

        # Construct h0(X), h1(X), h2(X) constraint polynomials
        h0_poly = l0_poly * (z_poly - CnstPoly(c_vec[0])*f_poly)
        h1_poly = UniPolynomial([-Field.one(), Field.one()]) * (z_poly - UniPolynomial.shift(z_poly, omega.inv()) - f_poly * c_poly)
        h2_poly = ln_1_poly * (z_poly - CnstPoly(v))
        
        # Finalize h(X)
        h_poly += CnstPoly(alpha**(log_n + 1)) * h0_poly 
        h_poly += CnstPoly(alpha**(log_n + 2)) * h1_poly 
        h_poly += CnstPoly(alpha**(log_n + 3)) * h2_poly

        # Compute t(X), the quotient polynomial of h(X) / vH(X)
        t_poly, r_poly = divmod(h_poly, vH_poly)
        if self.debug > 1:
            print(f"P> check divisibility of h_poly")
            assert r_poly.is_zero()
            print(f"P> check divisibility of h_poly passed")
        
        # Commit to the accumulator polynomial z(X)
        z_cm = self.kzg_pcs.commit(z_poly)

        # Commit to the quotient polynomial t(X)
        t_cm = self.kzg_pcs.commit(t_poly)

        # Send `[z(X)]` and `[t(X)]` to the verifier
        tr.absorb(b"z_commitment", z_cm.cm)
        tr.absorb(b"t_commitment", t_cm.cm)

        # > Round 3.

        # Get evaluation challenge
        zeta = Field.from_bytes(tr.challenge_bytes(b"zeta", 1))
        if self.debug > 0:
            print(f"P> zeta = {zeta}")

        # Evaluate selector polynomials at zeta
        s_evals = [s.evaluate(zeta) for s in s_poly_vec]

        if self.debug > 1:
            print(f"P> check s_evals")
            vH_poly_at_zeta = zeta**domain_size - Field.one()
            x = zeta
            for k in range(log_n):
                vH = x - Field.one()
                s_poly_at_zeta = vH_poly_at_zeta / vH
                x = x**2
                assert s_evals[k] == s_poly_at_zeta, \
                    f"s_evals[{k}]={s_evals[k]},s_poly_at_zeta={s_poly_at_zeta}"
            print(f"P> check s_evals passed")

        # Construct c*(X) polynomial evaluations
        #
        # c_evals = [c(zeta), c(zeta*omega^{2^{n-1}}), ..., c(zeta*omega^2), c(zeta*omega)]
        #
        #  TODO: optimize this, c(x) -> c(x^2)
        c_star_evals = []
        for k in range(log_n+1):
            omega_k = Field.nth_root_of_unity(2**k)
            eval_point = omega_k * zeta
            eval_val = c_poly.evaluate(eval_point)
            c_star_evals.append(eval_val)

        if self.debug > 1:
            print(f"P> check c_star_evals")
            h = s_poly_vec[0].evaluate(zeta) * (c_star_evals[0] - c_vec[0])
            for k in range(1, log_n + 1):
                g = c_star_evals[0] * us[log_n - k] - c_star_evals[k] * (Field(1) - us[log_n - k])
                p = s_poly_vec[k - 1].evaluate(zeta) * g * (alpha ** k)
                h += p
            h += (alpha ** (log_n + 1)) * h0_poly.evaluate(zeta) 
            h += (alpha ** (log_n + 2)) * h1_poly.evaluate(zeta) 
            h += (alpha ** (log_n + 3)) * h2_poly.evaluate(zeta)
            assert h == t_poly.evaluate(zeta) * vH_poly.evaluate(zeta)
            print(f"P> check c_star_evals passed")

        if self.debug > 1:
            print(f"P> debug={self.debug}")
            self.kzg_pcs.debug_check_commitment(f_cm, f_poly.coeffs)
            self.kzg_pcs.debug_check_commitment(t_cm, t_poly.coeffs)
            self.kzg_pcs.debug_check_commitment(c_cm, c_poly.coeffs)

        # Compute z(zeta/omega)
        z_shifted_eval = z_poly.evaluate(zeta * omega.inv())

        # Compute vH(zeta), l0(zeta), ln_1(zeta)
        vH_poly_at_zeta = vH_poly.evaluate(zeta)
        l0_poly_at_zeta = l0_poly.evaluate(zeta)
        ln_1_poly_at_zeta = ln_1_poly.evaluate(zeta)

        # Compute r(X) as the linearized polynomial
        r_const = s_evals[0] * (c_star_evals[0] - c_vec[0])
        for i in range(1, log_n+1):
            r_const += alpha**(i) * s_evals[i-1] * (us[log_n-i] * c_star_evals[0] - c_star_evals[i] * (Field(1) - us[log_n-i]))
        r_poly = UniPolynomial([r_const])
        r_poly += CnstPoly(alpha**(log_n + 1) * l0_poly_at_zeta) * (z_poly - CnstPoly(c_vec[0]) * f_poly)
        r_poly += CnstPoly(alpha**(log_n + 2) * (zeta - Field.one())) * (z_poly - CnstPoly(z_shifted_eval) - CnstPoly(c_star_evals[0]) * f_poly)
        r_poly += CnstPoly(alpha**(log_n + 3) * ln_1_poly_at_zeta) * (z_poly - CnstPoly(v))
        r_poly -= CnstPoly(vH_poly_at_zeta) * t_poly

        if self.debug > 1:
            print(f"P> check r_poly")
            assert r_poly.evaluate(zeta) == Field.zero()
            print(f"P> check r_poly passed")

        q_poly, rem = r_poly.div_by_linear_divisor(zeta)
        if self.debug > 1:
            print(f"P> check divisibility of r_poly")
            assert rem == Field.zero()
            print(f"P> check divisibility of r_poly passed")


        # D = [zeta, zeta*omega^{2^{n-1}}, ..., zeta*omega^2, zeta*omega]
        # TODO: optimize off Fr.nth_root_of_unity * n
        domain_D = []
        for k in range(0, log_n+1):
            lambda_k = Field.nth_root_of_unity(2**k)
            domain_D.append(zeta * lambda_k)
        
        # Construct c*(X) polynomial
        c_star_poly = UniPolynomial.interpolate(c_star_evals, domain_D)

        # Construct zD(X) polynomial
        zD_poly = UniPolynomial.vanishing_polynomial(domain_D)

        # Construct qc(X) polynomial, which is the quotient of (c(X) - c*(X)) / zD(X)
        qc_poly, rem_c_poly = divmod(c_poly - c_star_poly, zD_poly)

        if self.debug > 0:
            print(f"P> check divisibility of qc_poly")
            assert rem_c_poly.is_zero()
            print(f"P> check divisibility of qc_poly passed")

        # Construct q_omega(X), which is the quotient of (z(X) - z(zeta/omega)) / (X - zeta/omega)
        q_omega_poly, rem_q_omega = (z_poly - CnstPoly(z_shifted_eval)).div_by_linear_divisor(zeta * omega.inv())

        if self.debug > 0:
            print(f"P> check divisibility of q_omega_poly")
            assert rem_q_omega == Field.zero()
            print(f"P> check divisibility of q_omega_poly passed")

        # Commit to q(X)
        q_cm = self.kzg_pcs.commit(q_poly)
        tr.absorb(b"q_commitment", q_cm.cm)

        # Commit to qc(X)
        qc_cm = self.kzg_pcs.commit(qc_poly)
        tr.absorb(b"qc_commitment", qc_cm.cm)

        # Commit to q_omega(X)
        q_omega_cm = self.kzg_pcs.commit(q_omega_poly)
        tr.absorb(b"q_omega_commitment", q_omega_cm.cm)

        for i in range(len(c_star_evals)):
            tr.absorb(b"c_star_evals", c_star_evals[i])
        tr.absorb(b"z_shifted_eval", z_shifted_eval)

        ## Round 4.

        # Get evaluation challenge
        xi = tr.squeeze(Field, b"xi", 1)
        if self.debug > 0:
            print(f"P> xi = {xi}")

        c_final_poly = c_poly
        c_final_poly -= CnstPoly(c_star_poly.evaluate(xi)) 
        c_final_poly -= qc_poly * CnstPoly(zD_poly.evaluate(xi))

        # Construct q_xi(X), which is the quotient of (c(X) - c*(xi) -  zD(xi) * qc(X)) / (X - xi)
        q_xi_poly, rem_q_xi = c_final_poly.div_by_linear_divisor(xi)

        q_xi_cm = self.kzg_pcs.commit(q_xi_poly)
        tr.absorb(b"q_xi_commitment", q_xi_cm.cm)

        if self.debug > 0:
            print(f"P> check divisibility of c_final_poly")
            assert rem_q_xi == Field.zero()
            print(f"P> check divisibility of c_final_poly passed")

            bc_weights = UniPolynomial.barycentric_weights(domain_D)
            numerator = Field.zero()
            denominator = Field.zero()
            for i in range(len(domain_D)):
                factor = bc_weights[i] * (xi - domain_D[i]).inv()
                denominator += factor
                numerator += c_star_evals[i] * factor
            c_star_poly_at_xi = numerator * denominator.inv()
            assert c_star_poly_at_xi == c_star_poly.evaluate(xi)
            print(f"P> check c_star_poly_at_xi passed")

            H_weights = UniPolynomialWithFft.compute_barycentric_weights(domain_size)
            vH_poly_at_zeta = zeta**domain_size - Field.one()
            assert vH_poly_at_zeta == UniPolynomialWithFft.vanishing_polynomial(domain_size).evaluate(zeta)
            print(f"P> check vH_poly_at_zeta passed")

            l0_poly_at_zeta = H_weights[0] * vH_poly_at_zeta * (zeta - Field.one()).inv()
            assert l0_poly_at_zeta == UniPolynomialWithFft.lagrange_polynomial(0, domain_size).evaluate(zeta)
            assert l0_poly_at_zeta == l0_poly.evaluate(zeta)
            print(f"P> check l0_poly_at_zeta passed")

            ln_1_poly_at_zeta = H_weights[-1] * vH_poly_at_zeta * (zeta - omega.inv()).inv()
            assert ln_1_poly_at_zeta == UniPolynomialWithFft.lagrange_polynomial(domain_size-1, domain_size).evaluate(zeta)
            print(f"P> check ln_1_poly_at_zeta passed")
        
        if self.debug > 1:
            print(f"P> check s_poly_vec")
            vH_poly_at_zeta = zeta**domain_size - Field.one()
            x = zeta
            for k in range(log_n):
                vH = x - Field.one()
                s_poly_at_zeta = vH_poly_at_zeta / vH
                x = x**2
                print(f"P> prover> s_poly_at_zeta={s_poly_at_zeta}")
                assert s_poly_vec[k].evaluate(zeta) == s_poly_at_zeta, \
                    f"s_poly_vec[{k}]={s_poly_vec[k].evaluate(zeta)},s_poly_at_zeta={s_poly_at_zeta}"
            print(f"P> check s_poly_vec passed")    

        g = self.kzg_pcs.params['g']
        tau_h = self.kzg_pcs.params['tau_h']
        h = self.kzg_pcs.params['h']
        if self.debug > 1:
            print(f"P> check C_r")
            C_r = self.kzg_pcs.params['g'].ec_mul(r_const)
            C_r += (z_cm.cm - f_cm.cm.ec_mul(c_vec[0])).ec_mul(alpha**(log_n+1)*l0_poly_at_zeta)
            C_r += (z_cm.cm - g.ec_mul(z_shifted_eval) - f_cm.cm.ec_mul(c_star_evals[0])).ec_mul(alpha**(log_n+2)*(zeta - Field.one()))
            C_r += (z_cm.cm - g.ec_mul(v)).ec_mul(alpha**(log_n+3)*ln_1_poly_at_zeta)
            C_r -= t_cm.cm.ec_mul(vH_poly_at_zeta)
            lhs = (C_r + q_cm.cm.ec_mul(zeta), h)
            rhs = (q_cm.cm, tau_h)
            checked = ec_pairing_check([lhs[0], rhs[0]], [-lhs[1], rhs[1]])
            assert checked, "C_r is not valid"
            print(f"P> check C_r passed")

        if self.debug > 1:
            zD_poly_at_xi = zD_poly.evaluate(xi)
            print(f"P> check q_xi_cm")
            C = c_cm.cm - g.ec_mul(c_star_poly_at_xi) - qc_cm.cm.ec_mul(zD_poly_at_xi) + q_xi_cm.cm.ec_mul(xi)
            lhs = (C, h)
            rhs = (q_xi_cm.cm, tau_h)
            checked = ec_pairing_check([lhs[0], rhs[0]], [-lhs[1], rhs[1]])
            assert checked, "q_xi_cm is not valid"
            print(f"P> check q_xi_cm passed")

        if self.debug > 1:
            print(f"P> check q_omega_cm")
            C = z_cm.cm - g.ec_mul(z_shifted_eval) + q_omega_cm.cm.ec_mul(zeta * omega.inv())
            lhs = (C, h)
            rhs = (q_omega_cm.cm, tau_h)
            checked = ec_pairing_check([lhs[0], rhs[0]], [-lhs[1], rhs[1]])
            assert checked, "q_omega_cm is not valid"
            print(f"P> check q_omega_cm passed")
            
        return v, {
            'c_commitment': c_cm,  # Round 1
            'z_commitment': z_cm,  # Round 2 
            't_commitment': t_cm,  # Round 2
            'q_zeta_commitment': q_cm,  # Round 3
            'q_c_commitment': qc_cm,    # Round 3
            'q_omega_zeta_commitment': q_omega_cm,  # Round 3
            'c_star_evals': c_star_evals,                     # Round 3
            'z_shifted_eval': z_shifted_eval,       # Round 3
            'q_xi_commitment': q_xi_cm  # Round 4
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
        log_n = len(us)
        domain_size = 2**log_n
        omega = Field.nth_root_of_unity(domain_size)
        
        g = self.kzg_pcs.params['g']
        tau_h = self.kzg_pcs.params['tau_h']
        h = self.kzg_pcs.params['h']
        c0 = reduce(lambda x, y: x*y, [(Field.one() - us[i]) for i in range(len(us))])

        # Load the argument
        c_cm = arg['c_commitment']
        z_cm = arg['z_commitment']
        t_cm = arg['t_commitment']
        q_zeta_cm = arg['q_zeta_commitment']
        q_c_cm = arg['q_c_commitment']
        q_zeta_omega_cm = arg['q_omega_zeta_commitment']
        c_star_evals = arg['c_star_evals']
        z_shifted_eval = arg['z_shifted_eval']
        q_xi_cm = arg['q_xi_commitment']  

        # > Round 0
        # tr.append_message(b"magic_number", b"ph23_pcs")
        tr.absorb(b"commitment", f_cm.cm)
        tr.absorb(b"point", us)
        tr.absorb(b"value", v)

        # > Round 1
        
        tr.absorb(b"c_commitment", c_cm.cm)

        # > Round 2
        alpha = tr.squeeze(Field, b"alpha", 1)
        if self.debug > 0:
            print(f"V> alpha = {alpha}")

        tr.absorb(b"z_commitment", z_cm.cm)
        tr.absorb(b"t_commitment", t_cm.cm)

        # > Round 3
        zeta = tr.squeeze(Field, b"zeta", 1)
        if self.debug > 0:
            print(f"V> zeta = {zeta}")

        tr.absorb(b"q_commitment", q_zeta_cm.cm)
        tr.absorb(b"qc_commitment", q_c_cm.cm)
        tr.absorb(b"q_omega_commitment", q_zeta_omega_cm.cm)

        for i in range(len(c_star_evals)):
            tr.absorb(b"c_star_evals", c_star_evals[i])
        tr.absorb(b"z_shifted_eval", z_shifted_eval)

        # > Round 4.

        xi = tr.squeeze(Field, b"xi", 1)
        if self.debug > 0:
            print(f"V> xi = {xi}")

        tr.absorb(b"q_xi_commitment", q_xi_cm.cm)

        # > Round of verification

        gamma = tr.squeeze(Field, b"gamma", 1)
        if self.debug > 0:
            print(f"V> gamma = {gamma}")

        # TODO: Optimize 
        domain_D = []
        for k in range(0, log_n + 1):
            lambda_k = Field.nth_root_of_unity(2**k)
            domain_D.append(zeta * lambda_k)

        # Construct c(xi) polynomial
        bc_weights = UniPolynomial.barycentric_weights(domain_D) # TODO: to be precomputed
        numerator = Field.zero()
        denominator = Field.zero()
        for i in range(len(domain_D)):
            factor = bc_weights[i] * (xi - domain_D[i]).inv()
            denominator += factor
            numerator += c_star_evals[i] * factor
        c_star_poly_at_xi = numerator * denominator.inv()

        # Construct vH(zeta), l_0(zeta), l_{n-1}(zeta)
        vH_poly_at_zeta = zeta**domain_size - Field.one()

        H_weights = UniPolynomialWithFft.compute_barycentric_weights(domain_size) # TODO: to be precomputed
        l0_poly_at_zeta = H_weights[0] * vH_poly_at_zeta * (zeta - Field.one()).inv()
        ln_1_poly_at_zeta = H_weights[-1] * vH_poly_at_zeta * (zeta - omega.inv()).inv()

        # evaluate selector polynomials at zeta
        # Method 1
        # x = zeta
        # s_evals = []
        
        # for k in range(log_n):
        #     vH = x - Field.one()
        #     s_poly_at_zeta = vH_poly_at_zeta / vH
        #     x = x**2
        #     s_evals.append(s_poly_at_zeta)

        # evaluate selector polynomials at zeta
        # Method 2
        s_evals = []
        # s_{n-1}(zeta) = zeta^{2^{n-1}} + 1
        s_evals.append(zeta**(2**(log_n - 1)) + Field.one()) 
        # compute s_{n-2}(zeta), ..., s_{0}(zeta)
        # s_{i}(zeta) = s_{i+1}(zeta) * (zeta^{2^i} + 1)
        for i in range(log_n - 2, -1, -1):
            temp = zeta**(2**i) + Field.one()
            s_evals.append(s_evals[-1] * temp)
        # reserve s_evals
        s_evals.reverse()

        P = G1Point.zero()
        Q = G1Point.zero()

        # Construct commitment of r(X) -- linearized polynomial

        r_const = s_evals[0] * (c_star_evals[0] - c0)
        for i in range(1, log_n + 1):
            r_const += alpha**(i) * s_evals[i-1] * (us[log_n-i] * c_star_evals[0] - c_star_evals[i] * (Field(1) - us[log_n-i]))
        
        C_r = self.kzg_pcs.params['g'].ec_mul(r_const)
        C_r += (z_cm.cm - f_cm.cm.ec_mul(c0)).ec_mul(alpha**(log_n+1)*l0_poly_at_zeta)
        C_r += (z_cm.cm - g.ec_mul(z_shifted_eval) - f_cm.cm.ec_mul(c_star_evals[0])).ec_mul(alpha**(log_n+2)*(zeta - Field.one()))
        C_r += (z_cm.cm - g.ec_mul(v)).ec_mul(alpha**(log_n+3)*ln_1_poly_at_zeta)
        C_r -= t_cm.cm.ec_mul(vH_poly_at_zeta)

        # check q_zeta_commitment
        C_0 = C_r + q_zeta_cm.cm.ec_mul(zeta)
        P += C_0
        Q += q_zeta_cm.cm

        if self.debug > 1:
            print(f"V> check C_0")
            checked = ec_pairing_check([C_0, q_zeta_cm.cm], [-h, tau_h])
            assert checked, "C_0 is not valid"
            print(f"V> check C_0 passed")

        # compute zD(xi)
        zD_poly_at_xi = reduce(lambda x, y: x*y, [xi - domain_D[i] for i in range(len(domain_D))])
        # check q_xi_commmitment
        C_1 = c_cm.cm - g.ec_mul(c_star_poly_at_xi) - q_c_cm.cm.ec_mul(zD_poly_at_xi) + q_xi_cm.cm.ec_mul(xi)
        P += C_1.ec_mul(gamma)
        Q += q_xi_cm.cm.ec_mul(gamma)

        if self.debug > 1:
            print(f"V> check C_1")
            checked = ec_pairing_check([C_1, q_xi_cm.cm], [-h, tau_h])
            assert checked, "C_1 is not valid"
            print(f"V> check C_1 passed")

        # check q_zeta_omega_cm
        C_2 = z_cm.cm - g.ec_mul(z_shifted_eval) + q_zeta_omega_cm.cm.ec_mul(zeta * omega.inv())
        P += C_2.ec_mul(gamma*gamma)
        Q += q_zeta_omega_cm.cm.ec_mul(gamma*gamma)

        if self.debug > 1:
            print(f"V> check C_2")
            checked = ec_pairing_check([C_2, q_zeta_omega_cm.cm], [-h, tau_h])
            assert checked, "C_2 is not valid"
            print(f"V> check C_2 passed")

        checked = ec_pairing_check([P, Q], [-h, tau_h])
        if self.debug > 1:
            print(f"V> check P, Q")
            assert checked, "P or Q is not valid"
            print(f"V> check P, Q passed")

        return checked

def test_ph23_uni_pcs():

    # # initialize the PedersenCommitment and the IPA_PCS
    kzg = KZG10_PCS(G1Point, G2Point, Field, 20)
    kzg.debug = True

    ph23 = PH23_PCS(kzg, debug = 2)

    tr = MerlinTranscript(b"ph23-pcs")

    # A simple instance f(x) = y
    coeffs = [Field(2), Field(3), Field(4), Field(5), Field(6), Field(7), Field(8), Field(9), \
             Field(10), Field(11), Field(12), Field(13), Field(14), Field(15), Field(16), Field(17)]
    us = [Field(4), Field(2), Field(3), Field(0)]
    eqs = MLEPolynomial.eqs_over_hypercube(us)

    y = sum([a * b for a, b in zip(coeffs, eqs)])
    f = MLEPolynomial(coeffs, 4)
    assert f.evaluate(us) == y

    f_cm = ph23.commit(f)

    v, arg = ph23.prove_eval(f_cm, f, us, tr.fork(b"ph23_pcs"))
    assert v == y
    ph23.verify_eval(f_cm, us, v, arg, tr.fork(b"ph23_pcs"))

if __name__ == "__main__":
    test_ph23_uni_pcs()

