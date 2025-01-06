#!/usr/bin/env python3

# WARNING: This implementation may contain bugs and has not been audited. 
# It is only for educational purposes. DO NOT use it in production.

# Implementation of KZG10 (Appendix C in Marlin paper, [CHMMVW19])
#
#    Marlin: Preprocessing zkSNARKs with Universal and Updatable SRS
#       - https://eprint.iacr.org/2019/1047
#
# The code is adapted from the arkworks-polycommit project
#
#   https://github.com/arkworks-rs/poly-commit
#
# Specifically, from the file poly-commit/src/kzg10/mod.rs
# Commit version: 12f5529c9ca609d07dd4683fcd1e196bc375eb0d

from typing import Optional
from curve import Fp, Fr as Field, ec_mul, ec_mul_group2, G1Point as G1, G2Point as G2, ec_pairing_check
# from group import DummyGroup
from unipoly import UniPolynomial, Domain_FFT_2Radix
# from field import Field
from random import randint
from utils import next_power_of_two, is_power_of_two, bits_le_with_width, bit_reverse, log_2
from merlin.merlin_transcript import MerlinTranscript
from kzg10_non_hiding import Commitment

class KZG10_PCS:
    """KZG10 commitment scheme implementation."""
    params: dict

    def __init__(self, G1, G2, Scalar, max_degree, hiding_bound, debug=False):
        """
        Initialize the KZG10 commitment scheme.
        
        Args:
            G1, G2: Elliptic curve groups
            Scalar: Field element type
            max_degree: Maximum polynomial degree supported
            hiding_bound: Upper bound for the hiding polynomial degree (optional)
            debug: Enable debug assertions
        """
        self.G1 = G1
        self.G2 = G2
        self.Scalar = Scalar
        self.max_degree = max_degree
        self.hiding_bound = hiding_bound
        self.params = self.setup()
        self.debug = debug
    
    # WARNING: This setup function is only used for testing. Never use it in production.
    # In practice, we should use a trusted setup, e.g., by an MPC-based setup ceremony.
    def setup(self, secret_symbol = None, g1_generator = None, g2_generator = None) -> None:
        """
        Generate the structured reference string (SRS).

            G : [1]_1, [s]_1,     [s^2]_1,     ..., [s^max_degree]_1
            G': [γ]_1, [γ*s^2]_1, [γ*s^3]_1,   ..., [γ*s^max_degree]_1
            H : [1]_2, [s]_2,     [s^2]_2,     ..., [s^max_degree]_2
        
        Args:
            produce_g2_powers: Whether to produce powers in G2
            secret_symbol: Secret value for SRS (if None, randomly generated)
            g1_generator, g2_generator: Generators for G1 and G2 (if None, randomly chosen)
        
        Returns:
            Dictionary containing the SRS parameters
        """

        # [1]_1, [1]_2
        if g1_generator is None:
            g = ec_mul(self.G1.ec_gen(), self.Scalar.rand())
            h = ec_mul_group2(self.G2.ec_gen(), self.Scalar.rand())
        else:
            g = g1_generator
            h = g2_generator

        if secret_symbol is None:
            tau = self.Scalar.rand()
        else:
            tau = secret_symbol

        # γ: randomness used for hiding
        gamma = self.Scalar.rand()
        # [γ]_1
        gamma_g = g.ec_mul(gamma)
        # [γ]_2
        gamma_h = h.ec_mul(gamma)

        powers_of_tau = [tau ** i for i in range(self.max_degree + 2)]
        # [1]_1, [τ]_1, [τ^2]_1, ..., [τ^{max_degree + 1}]_1
        powers_of_g: list[self.G1] = [g.ec_mul(powers_of_tau[i]) for i in range(self.max_degree + 1)]
        # [γ]_1, [γτ]_1, [γτ^2]_1, ..., [γτ^{max_degree + 1}]_1
        powers_of_gamma_g: list[self.G1] = [gamma_g.ec_mul(powers_of_tau[i]) for i in range(self.max_degree + 2)]
        # [1]_2, [τ]_2, [τ^2]_2, ..., [τ^{max_degree}]_2
        powers_of_h: list[self.G2] = [h.ec_mul(powers_of_tau[i]) for i in range(self.max_degree + 1)]

        self.params = {}
        self.params['powers_of_tau_g'] = powers_of_g
        self.params['powers_of_tau_gamma_g'] = powers_of_gamma_g
        self.params['powers_of_tau_h'] = powers_of_h
        self.params['g'] = g
        self.params['h'] = h
        self.params['tau_h'] = h.ec_mul(tau)
        self.params['gamma_h'] = gamma_h

        return self.params
    
    def setup_lagrange_basis(self, domain_size: int):
        """
        Setup the Lagrange basis polynomials.
        """
        assert is_power_of_two(domain_size), "domain_size must be a power of two"
        assert domain_size <= self.max_degree, f"domain_size: {domain_size} is larger than max_degree: {self.max_degree}"

        k_log_size = log_2(domain_size)
        omega = self.Scalar.nth_root_of_unity(domain_size)
        omega_inv = omega.inv()

        domain_size_inv = self.Scalar(domain_size).inv()

        lagrange_bases = self.params['powers_of_tau_g'].copy()

        # bit reverse
        for i in range(domain_size):
            i_rev = bit_reverse(i, k_log_size)
            if i < i_rev:
                lagrange_bases[i_rev], lagrange_bases[i] = lagrange_bases[i], lagrange_bases[i_rev]
        
        # butterfly network
        sep = 1
        for _ in range(k_log_size):
            w = self.Scalar.one()
            w_exp = omega_inv.exp(domain_size // (sep * 2))
            for j in range(sep):
                for i in range(0, domain_size, sep * 2):
                    l = i + j
                    r = i + j + sep
                    a = lagrange_bases[r].ec_mul(w)
                    lagrange_bases[r] = lagrange_bases[l] - a
                    lagrange_bases[l] = lagrange_bases[l] + a
                w = w * w_exp
            sep *= 2
        
        self.params['lagrange_of_g'] = [lagrange_bases[i].ec_mul(domain_size_inv) for i in range(domain_size)]

        return

    def commit_with_lagrange_basis(self, evaluations: list[Field], hiding_bound: int):
        """
        Commit to a polynomial with Lagrange basis.
        
        Args:
            evaluations: The evaluations of the polynomial at the Lagrange basis points
            hiding_bound: The upper bound for the hiding polynomial degree
        
        Returns:
            tuple: (Commitment, random_ints)
                - Commitment: The commitment to the polynomial
                - random_ints: The random integers used for hiding
        """
        # Check if polynomial degree is too large
        domain_size = len(evaluations)
        num_lagrange_basis = len(self.params['lagrange_of_g'])
        assert domain_size == num_lagrange_basis, f"Number of evaluation points must be equal to the number of Lagrange basis points, domain_size: {domain_size}, num_lagrange_basis: {num_lagrange_basis}"

        # Commitment calculation
        cm = msm_basic(self.params['lagrange_of_g'], evaluations)

        # Add hiding polynomial if hiding_bound is set
        # while UniPolynomial(random_ints).degree == 0:
        random_ints = [self.Scalar.rand() for _ in range(hiding_bound + 1)]
        assert random_ints[-1] != self.Scalar.zero(), f"Last random int is zero, random_ints: {random_ints}"

        if self.debug:
            assert UniPolynomial(random_ints).degree > 0, f"Degree of random poly is zero, random_ints: {random_ints}"
    
        # Check hiding bound
        hiding_poly_degree = len(random_ints) - 1
        num_powers = len(self.params['powers_of_tau_gamma_g'])
        assert self.hiding_bound != 0, "Hiding bound is zero"
        assert hiding_poly_degree < num_powers, "Hiding bound is too large"
    
        hiding_poly_cm = msm_basic(self.params['powers_of_tau_gamma_g'], random_ints)
        cm += hiding_poly_cm

        # Final debug assertion
        if self.debug:
            assert isinstance(cm, self.G1)

        if self.debug:
            return Commitment(cm, oob=(evaluations, random_ints)), random_ints

        return Commitment(cm), random_ints
    
    # NOTE: This function is only used internally.
    def compute_quotient_polynomial(self, polynomial: UniPolynomial, point):
        """
        Compute the quotient polynomial for a given polynomial and point.
        
        Args:
            polynomial: The polynomial to compute the witness polynomial for
            point: The point at which to evaluate the polynomial
            random_ints: Random integers used for hiding
        
        Returns:
            tuple: (witness polynomial, hiding witness polynomial)
        """
        quotient, evaluation = polynomial.division_by_linear_divisor(point)
        # quotient_hiding = None
        # evaluation_hiding = None
        # if random_ints is not None and len(random_ints) > 0:
        #     hiding_poly = UniPolynomial(random_ints)
        #     if self.debug:
        #         assert hiding_poly.degree > 0, f"Degree of random poly is zero, random_ints: {random_ints}"
        #     quotient_hiding, evaluation_hiding = hiding_poly.division_by_linear_divisor(point)
        return quotient, evaluation
    
    def commit(self, polynomial: UniPolynomial, hiding_bound: int) -> tuple[Commitment, list[Field]]:
        """
        Commit to a univariate polynomial.

            f(X)   = c_0 + c_1*X + c_2*X^2 + ... + c_n*X^n

            r(X) = r_0 + r_1*X + r_2*X^2 + ... + r_m*X^m

            [f(X)] = c_0 *[1] + c_1*[τ] + c_2*[τ^2] + ... + c_n*[τ^n] + 
            [r(X)] = r_0 *[γ] + r_1*[γτ] + r_2*[γτ^2] + ... + r_m*[γτ^m]

            where m is hiding_bound

            cm(f) = [f(X)] + [r(X)]
        
        Args:
            polynomial: The polynomial to commit to
                * its coefficients have no leading zeros
            hiding_bound: The upper bound for the hiding polynomial degree

        Returns:
            tuple: (Commitment, random_ints)
                - Commitment: The commitment to the polynomial
                - random_ints: The random integers used for hiding
        """
        # Check if polynomial degree is too large
        n = polynomial.degree + 1
        num_powers = len(self.params['powers_of_tau_g'])
        assert n <= num_powers, f"Too many coefficients, n: {n}, num_powers: {num_powers}"

        cm = msm_basic(self.params['powers_of_tau_g'], polynomial.coeffs)

        random_ints = [self.Scalar.rand() for _ in range(hiding_bound + 1)]
        assert random_ints[-1] != self.Scalar.zero(), f"Last random int is zero, random_ints: {random_ints}"

        if self.debug:
            assert UniPolynomial(random_ints).degree > 0, f"Degree of random poly is zero, random_ints: {random_ints}"
    
        # Check hiding bound
        hiding_poly_degree = len(random_ints) - 1
        num_powers = len(self.params['powers_of_tau_gamma_g'])
        assert self.hiding_bound != 0, "Hiding bound is zero"
        assert hiding_poly_degree < num_powers, "Hiding bound is too large"
    
        hiding_poly_cm = msm_basic(self.params['powers_of_tau_gamma_g'], random_ints)
        cm += hiding_poly_cm

        # Final debug assertion
        if self.debug:
            assert isinstance(cm, self.G1)

        if self.debug:
            return Commitment(cm, oob=(polynomial.coeffs, random_ints)), random_ints

        return Commitment(cm), random_ints

    def prove_evaluation(self, polynomial: UniPolynomial, point: Field, randomness: list[Field]) -> tuple[Field, dict]:
        """
        Open the polynomial at a given point.
        
        Args:
            polynomial: The polynomial to open
            point: The point at which the polynomial was opened
            randomness: Random scalars used for hiding
        
        Returns:
            tuple: (evaluation, proof)
                - evaluation: The value of the polynomial at the given point
                - proof: {'w': witness polynomial, 'hiding_v': hiding witness polynomial}
        """
        assert polynomial.degree + 1 < len(self.params['powers_of_tau_g']), \
                f"Too many coefficients, polynomial.degree: {polynomial.degree}"
        
        q_poly, v = self.compute_quotient_polynomial(polynomial, point)
        r_poly = UniPolynomial(randomness)
        r_quo_poly, r_v = self.compute_quotient_polynomial(r_poly, point)

        w_cm = msm_basic(self.params['powers_of_tau_g'], q_poly.coeffs)
        w_cm += msm_basic(self.params['powers_of_tau_gamma_g'], r_quo_poly.coeffs)

        return v, {'w_cm': Commitment(w_cm), 'v_hiding': r_v}
    
    def verify_evaluation(self, commitment: Commitment, point: Field, value: Field, proof: dict) -> bool:
        """
        Check the validity of the proof.
        
        Args:
            commitment: The commitment to the polynomial
            point: The point at which the polynomial was evaluated
            value: The value of the polynomial at the given point
            proof: The proof values
        
        Returns:
            bool: True if the proof is valid, False otherwise
        """
        f_cm = commitment.cm
        f_cm -= self.params['g'].ec_mul(value)
        f_cm -= self.params['powers_of_tau_gamma_g'][0].ec_mul(proof['v_hiding'])

        w_cm = proof['w_cm'].cm

        lhs = (f_cm, self.params['h'])
        rhs = (w_cm, self.params['tau_h'] - self.params['h'].ec_mul(point))

        checked = ec_pairing_check([lhs[0], rhs[0]], [-lhs[1], rhs[1]])
        return checked
    
    # def batch_verify(self, commitments, points, values, proofs) -> bool:
    #     """
    #     Theorem:
    #         f(X) - f(z) = q(X) * (X - z)

    #     Verification equation:
    #         e(C - v*[1], [1]) = e([w], [s] - z*[1])

    #     To support batch verification, the above equation is changed to:
    #         f(X) - f(z) + q(X) * z = q(X) * X    
        
    #         e(C - v*[1] + z*[w], [1]) = e([w], [s])

    #     If we have 

    #         e(C1 - v1*[1] + z1*[w1], [1]) = e([w1], [s])
    #         e(C2 - v2*[1] + z2*[w2], [1]) = e([w2], [s])
    #         ...
    #         e(Cn - vn*[1] + zn*[wn], [1]) = e([wn], [s])

    #     Then we can sum up all the equations with a random linear combination:
    #         e(∑ rho^i * (Ci - vi*[1] + zi*[wi]), [1]) = e(∑ rho^i * ([wi]), [s])

    #     """
    #     batched_C = self.G1.zero()
    #     batched_W = self.G1.zero()

    #     # random linear combination
    #     rho = self.Scalar.one()
    #     g_multiplier = 0
    #     gamma_g_multiplier = 0

    #     for Ci, zi, vi, proofi in zip(commitments, points, values, proofs):
    #         Wi = proofi['w']
    #         hiding_vi = proofi['hiding_v']
    #         C = Wi.ec_mul(zi) + Ci.cm
    #         g_multiplier += rho * vi
    #         gamma_g_multiplier += rho * hiding_vi

    #         batched_C += C.ec_mul(rho)
    #         batched_W += Wi.ec_mul(rho)
    #         rho = self.Scalar.rand()

    #     batched_C -= self.params['powers_of_g'][0].ec_mul(g_multiplier)
    #     batched_C -= self.params['powers_of_gamma_g'][0].ec_mul(gamma_g_multiplier)
        
    #     lhs = (batched_C, self.params['h'])
    #     rhs = (batched_W, self.params['tau_h'])
        
    #     checked = ec_pairing_check([lhs[0], rhs[0]], [-lhs[1], rhs[1]])

    #     return checked

    def commit_with_degree_bound(self, \
                    polynomial: UniPolynomial, \
                    hiding_bound: int, \
                    degree_bound: int) \
                        -> tuple[Commitment, Commitment, list[Field], list[Field]]:
        """
        Commit to a polynomial (f) with a degree bound `d`.

                deg(f) < d

        Args:
            polynomial: The polynomial to commit to
                * its coefficients have no leading zeros
            hiding_bound: The upper bound for the hiding polynomial degree
            degree_bound: The upper bound for the degree of the polynomial
        Returns:
            tuple: (commitment, lifted_commitment, randomness, lifting_randomness)
                - commitment: The commitment to the polynomial
                - lifted_commitment: The commitment to the lifted polynomial
                - randomness: The random polynomial used for hiding
                - lifting_randomness: The random polynomial used for lifting
        """
        # Check if polynomial degree is too large
        n = polynomial.degree + 1
        max_degree = len(self.params['powers_of_tau_g'])
        assert n <= max_degree, f"Too many coefficients, n: {n}, max_degree_bound: {max_degree}"

        f_cm = msm_basic(self.params['powers_of_tau_g'], polynomial.coeffs)

        # commitment to the polynomial f * x^{max_degree - deg_bound - 1}
        xf_coeffs = [self.Scalar(0)] * (self.max_degree - degree_bound) + polynomial.coeffs
        xf_cm = msm_basic(self.params['powers_of_tau_g'], xf_coeffs)

        # generate random polynomials for hiding
        r_vec = [self.Scalar.rand() for _ in range(hiding_bound + 1)]
        xr_vec = [self.Scalar.rand() for _ in range(hiding_bound + 1)]
        assert r_vec[-1] != self.Scalar.zero() and xr_vec[-1] != self.Scalar.zero(), \
                f"Last random int is zero, r_vec: {r_vec}, xr_vec: {xr_vec}"

        if self.debug:
            assert UniPolynomial(r_vec).degree > 0 and UniPolynomial(xr_vec).degree > 0, \
                f"Degree of random poly is zero, r_vec: {r_vec}, xr_vec: {xr_vec}"
    
        # Check hiding bound
        hiding_poly_degree = len(r_vec) - 1
        num_powers = len(self.params['powers_of_tau_gamma_g'])
        # assert self.hiding_bound != 0, "Hiding bound is zero"
        assert hiding_poly_degree < num_powers, "Hiding bound is too large"
    
        hiding_poly_cm = msm_basic(self.params['powers_of_tau_gamma_g'], r_vec)
        f_cm += hiding_poly_cm
        hiding_poly_cm_x = msm_basic(self.params['powers_of_tau_gamma_g'], xr_vec)
        xf_cm += hiding_poly_cm_x

        if self.debug:
            return Commitment(f_cm, oob=(polynomial.coeffs, r_vec)), \
                Commitment(xf_cm, oob=(xf_coeffs, xr_vec)), \
                r_vec, xr_vec

        return Commitment(f_cm), Commitment(xf_cm), r_vec, xr_vec
    
    # NOTE: point must be a random point chosen by the verifier
    def prove_evaluation_with_degree_bound(self, \
                    polynomial_cm: Commitment, \
                    lifted_polynomial_cm: Commitment, \
                    polynomial: UniPolynomial, \
                    point: Field, \
                    deg_bound: int, \
                    randomness: list[Field], \
                    lifted_randomness: list[Field], \
                    transcript: MerlinTranscript) -> tuple[Field, dict]:
        """
        Open the polynomial at a given point and prove degree bound.
        Args:
            polynomial_cm: The commitment to the polynomial
            lifted_polynomial_cm: The commitment to the lifted polynomial   
            polynomial: The polynomial to open
            point: The point at which the polynomial was opened
            deg_bound: The upper bound on the degree
            randomness: The random scalars used for hiding
            lifted_randomness: The random scalars used for lifting
            transcript: The transcript for the protocol
        
        Returns:
            tuple: (evaluation, proof)
                - evaluation: The value of the polynomial at the given point
                - proof: {'w_cm': witness polynomial, 't_v': evaluation of the hiding polynomial}
        """
        # assert not polynomial.is_zero(), "Polynomial is zero"
        assert polynomial.degree + 1 < len(self.params['powers_of_tau_g']), f"Too many coefficients, polynomial.degree: {polynomial.degree}"
        
        q_poly, v = self.compute_quotient_polynomial(polynomial, point)

        f_cm = polynomial_cm.cm
        r_poly = UniPolynomial(randomness)

        xf_cm = lifted_polynomial_cm.cm
        s_poly = UniPolynomial(lifted_randomness)

        transcript.append_message(b"f_cm", str(f_cm).encode())
        transcript.append_message(b"xf_cm", str(xf_cm).encode())
        transcript.append_message(b"point", str(point).encode())
        transcript.append_message(b"value", str(v).encode())
        transcript.append_message(b"deg_bound", str(deg_bound).encode())

        alpha = self.Scalar.from_bytes(transcript.challenge_bytes(b"alpha", 1))
        if self.debug:
            print(f"prover> alpha: {alpha}")

        t_poly = r_poly + UniPolynomial.const(alpha) * s_poly
        t_quo_poly, t_v = self.compute_quotient_polynomial(t_poly, point)

        # DEBUG!!!
        r_z = r_poly.evaluate(point)
        s_z = s_poly.evaluate(point)
        # print(f"prover> r_z: {r_z}, s_z: {s_z}")
        # print(f"prover> A : {(t_quo_poly * UniPolynomial([-point, self.Scalar.one()]) + UniPolynomial.const(t_v))}")
        # print(f"prover> B : {t_poly}")
        assert (t_quo_poly * UniPolynomial([-point, self.Scalar.one()]) + UniPolynomial.const(t_v)) == \
            t_poly, \
            f"Quotient mismatch, t_quo_poly: {t_quo_poly}, r_poly: {r_poly}, r_z: {r_z}, s_poly: {s_poly}, s_z: {s_z}"

        q_lift_coeffs = [self.Scalar(0)] * (self.max_degree - deg_bound) + q_poly.coeffs
        w_cm = msm_basic(self.params['powers_of_tau_g'], q_poly.coeffs)
        w_cm += msm_basic(self.params['powers_of_tau_g'], q_lift_coeffs).ec_mul(alpha)
        w_cm += msm_basic(self.params['powers_of_tau_gamma_g'], t_quo_poly.coeffs)

        assert t_v == r_poly.evaluate(point) + alpha * s_poly.evaluate(point), \
            f"Evaluation mismatch, t_v: {t_v}, r_poly: {r_poly}, s_poly: {s_poly}"

        return v, {'w_cm': Commitment(w_cm), 't_v': t_v}

    def verify_evaluation_with_degree_bound(self, \
                    polynomial_cm: Commitment, \
                    lifted_polynomial_cm: Commitment, \
                    point: Field, \
                    value: Field, \
                    deg_bound: int, \
                    argument: dict, \
                    transcript: MerlinTranscript) -> bool:
        """
        Verify the evaluation of the polynomial at a given point and degree bound.

        Args:
            polynomial_cm: The commitment to the polynomial
            lifted_polynomial_cm: The commitment to the lifted polynomial
            point: The point at which the polynomial was opened
            value: The value of the polynomial at the given point
            deg_bound: The upper bound on the degree
            argument: The proof provided by the prover
            transcript: The transcript for the protocol

        Returns:
            bool: True if the proof is valid, False otherwise
        """
        f_cm = polynomial_cm.cm
        xf_cm = lifted_polynomial_cm.cm
        w_cm = argument['w_cm'].cm
        t_v = argument['t_v']
        transcript.append_message(b"f_cm", str(f_cm).encode())
        transcript.append_message(b"xf_cm", str(xf_cm).encode())
        transcript.append_message(b"point", str(point).encode())
        transcript.append_message(b"value", str(value).encode())
        transcript.append_message(b"deg_bound", str(deg_bound).encode())
        alpha = self.Scalar.from_bytes(transcript.challenge_bytes(b"alpha", 1))
        
        if self.debug:
            print(f"verifier> alpha: {alpha}")

        t_cm = f_cm + xf_cm.ec_mul(alpha)
        t_cm -= self.params['powers_of_tau_g'][self.max_degree - deg_bound].ec_mul(value * alpha)
        t_cm -= self.params['g'].ec_mul(value) 
        t_cm -= self.params['powers_of_tau_gamma_g'][0].ec_mul(t_v)

        lhs = (t_cm, self.params['h'])    
        rhs = (w_cm, self.params['tau_h'] - self.params['h'].ec_mul(point))

        return ec_pairing_check([lhs[0], rhs[0]], [-lhs[1], rhs[1]])
    
    def debug_check_commitment(self, cm: Commitment, vs: tuple[Field]):
        """
        Check commitment against the opening values (ONLY FOR DEBUGGING)
        """
        assert self.debug, "Debug mode is not enabled"
        assert cm.oob is not None, "Commitment is not opened"
        assert len(cm.oob[0]) == len(vs), f"Number of values mismatch, len(cm.oob): {len(cm.oob)}, len(vs): {len(vs)}"

def msm_basic(bases, scalars):
    """
    Basic implementation of multi-scalar multiplication using big integers.
    
    Args:
        bases: List of group elements
        bigints: List of big integers
    
    Returns:
        Group element representing the result of the multi-scalar multiplication
    """
    result = G1.zero()
    for base, scalar in zip(bases, scalars):
        result += base.ec_mul(scalar)
    return result

def test_lagrange_basis(kzg: KZG10_PCS):

    f1 = UniPolynomial([Field.rand() for _ in range(randint(5, 10))])

    kzg.setup_lagrange_basis(16)

    omega = Field.nth_root_of_unity(16)

    evals = f1.compute_evaluations_fft(16, omega)
    f2 = UniPolynomial.interpolate_fft(evals, omega)
    assert f1.coeffs == f2.coeffs, "Interpolation should be the same polynomial"

    C1, r1 = kzg.commit(f1, 4)
    C2, r2 = kzg.commit_with_lagrange_basis(evals, 4)

    zeta = Field.rand()

    v1, arg1 = kzg.prove_evaluation(f1, zeta, r1)
    v2, arg2 = kzg.prove_evaluation(f2, zeta, r2)

    assert v1 == v2, "Evaluation mismatch"
    print("test_lagrange_basis passed!")

if __name__ == '__main__':
    # Test regular check
    # Create KZG10 commitment scheme instance
    kzg = KZG10_PCS(G1, G2, Field, 20, hiding_bound=3, debug=True)

    test_lagrange_basis(kzg)
