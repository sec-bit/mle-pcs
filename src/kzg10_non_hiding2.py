#!/usr/bin/env python3

# WARNING: This implementation may contain bugs and has not been audited. 
# It is only for educational purposes. DO NOT use it in production.

# Implementation of KZG10 
# The code is adapted from the arkworks-polycommit project
#
#   https://github.com/arkworks-rs/poly-commit
#
# Specifically, from the file poly-commit/src/kzg10/mod.rs
# Commit version: 12f5529c9ca609d07dd4683fcd1e196bc375eb0d

from typing import Optional
from curve import Fp, Fr as Field, ec_mul, ec_mul_group2, G1Point as G1, G2Point as G2, ec_pairing_check
from unipoly2 import UniPolynomial, Domain_FFT_2Radix, UniPolynomialWithFft
# from field import Field
from random import randint
from utils import is_power_of_two, bit_reverse, log_2
import copy


class Commitment:
    """Represents a commitment in the KZG scheme."""
    def __init__(self, cm, oob=None):
        self.cm = cm
        self.group = type(cm)
        if oob is not None:
            self.oob = oob

    @staticmethod
    def zero():
        """Create a zero commitment."""
        return Commitment(G1.zero())

    def __add__(self, other):
        """Add two commitments using + operator."""
        if not isinstance(other, Commitment):
            raise TypeError("Can only add commitments from the same group")
        return Commitment(self.cm + other.cm)
    
    def __sub__(self, other):
        """Subtract two commitments using - operator."""
        if not isinstance(other, Commitment) or self.group != other.group:
            raise TypeError("Can only subtract commitments from the same group")
        return Commitment(self.cm - other.cm)
    
    def __mul__(self, other):
        """
        Multiply a commitment using * operator.

        Args:
            other (UniPolynomial or scalar): The polynomial or scalar to multiply with this one.

        Returns:
            Commitment: 
        """
        if not isinstance(other, (int, type(self.scalar))):  # Scalar multiplication
            raise TypeError("Unsupported operand type for *: '{}' and '{}'".format(type(self).__name__, type(other).__name__))
        return Commitment(self.cm.ec_mul(other))

    def __rmul__(self, other):
        """Multiply a commitment using * operator."""

        if not isinstance(other, (int, type(self.scalar))):
            raise TypeError("Unsupported operand type for *: '{}' and '{}'".format(type(self).__name__, type(other).__name__))
        return Commitment(self.cm.ec_mul(other))

    def __repr__(self):
        return f"Commitment({self.cm})"
    
    def scalar_mul(self, scalar: Field):
        """Multiply a commitment using * operator."""
        # if not isinstance(scalar, (int, type(self.scalar))):
            # raise TypeError("Unsupported operand type for *: '{}' and '{}'".format(type(self).__name__, type(scalar).__name__))
        return Commitment(self.cm.ec_mul(scalar))

class KZG10_PCS:
    """KZG10 commitment scheme implementation."""
    params: dict

    def __init__(self, G1, G2, Scalar, max_degree, debug=False):
        """
        Initialize the KZG10 commitment scheme.
        
        Args:
            G1, G2: Elliptic curve groups
            max_degree: Maximum polynomial degree supported
            debug: Enable debug assertions
        """
        self.G1 = G1
        self.G2 = G2
        self.Scalar = Scalar
        self.max_degree = max_degree
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

        powers_of_tau = [tau ** i for i in range(self.max_degree + 2)]
        powers_of_g: list[self.G1] = [g.ec_mul(powers_of_tau[i]) for i in range(self.max_degree + 1)]
        powers_of_h: list[self.G1] = [h.ec_mul(powers_of_tau[i]) for i in range(self.max_degree + 1)]

        self.params = {}
        self.params['powers_of_g'] = powers_of_g
        self.params['powers_of_h'] = powers_of_h
        self.params['h'] = h
        self.params['tau_h'] = h.ec_mul(tau)
        self.params['g'] = g
        self.params['tau_g'] = g.ec_mul(tau)

        return self.params
    
    def setup_lagrange_basis(self, n: int):
        """
        Setup the Lagrange basis polynomials.
        """
        assert is_power_of_two(n), "n must be a power of two"
        assert n <= self.max_degree, f"n: {n} is larger than max_degree: {self.max_degree}"

        k_log_size = log_2(n)
        omega = self.Scalar.nth_root_of_unity(n)
        omega_inv = omega.inv()

        n_inv = self.Scalar(n).inv()

        lagrange_bases = self.params['powers_of_g'].copy()

        # bit reverse
        for i in range(n):
            i_rev = bit_reverse(i, k_log_size)
            if i < i_rev:
                lagrange_bases[i_rev], lagrange_bases[i] = lagrange_bases[i], lagrange_bases[i_rev]
        
        # butterfly network
        sep = 1
        for _ in range(k_log_size):
            w = self.Scalar.one()
            w_exp = omega_inv.exp(n // (sep * 2))
            for j in range(sep):
                for i in range(0, n, sep * 2):
                    l = i + j
                    r = i + j + sep
                    a = lagrange_bases[r].ec_mul(w)
                    lagrange_bases[r] = lagrange_bases[l] - a
                    lagrange_bases[l] = lagrange_bases[l] + a
                w = w * w_exp
            sep *= 2
        
        self.params['lagrange_of_g'] = [lagrange_bases[i].ec_mul(n_inv) for i in range(n)]

        return

    def commit_with_lagrange_basis(self, evaluations: list[Field]):
        """
        Commit to a polynomial with Lagrange basis.
        
        Args:
            evaluations: The evaluations of the polynomial at the Lagrange basis points
        
        Returns:
            tuple: (Commitment, random_ints used for hiding)
        """
        # Check if polynomial degree is too large
        n = len(evaluations)
        num_lagrange_basis = len(self.params['lagrange_of_g'])
        assert n == num_lagrange_basis, f"Number of evaluation points must be equal to the number of Lagrange basis points, n: {n}, num_lagrange_basis: {num_lagrange_basis}"

        # Commitment calculation
        commitment = msm_basic(self.params['lagrange_of_g'], evaluations)

        if self.debug:
            return Commitment(commitment, oob=(evaluations))

        return Commitment(commitment)
    
    def compute_quotient_polynomial(self, f: UniPolynomial, point: Field):
        """
        Compute the quotient polynomial for a given polynomial and point.
        
        Args:
            polynomial: The polynomial to compute the witness polynomial for
            point: The point at which to evaluate the polynomial
                
        Returns:
            tuple: (witness polynomial, evaluation)
        """
        quotient, evaluation = f.div_by_linear_divisor(point)
        return quotient, evaluation
    
    def commit(self, polynomial: UniPolynomial) -> Commitment:
        """
        Commit to a polynomial.
        
        Args:
            polynomial: The polynomial to commit to
                * its coefficients have no leading zeros (pre-condition)
        
        Returns:
            tuple: w_commitment
        """
        # Check if polynomial degree is too large
        n = polynomial.degree + 1
        max_degree_bound = len(self.params['powers_of_g'])
        assert n <= max_degree_bound, f"Too many coefficients, n: {n}, max_degree_bound: {max_degree_bound}"

        commitment = msm_basic(self.params['powers_of_g'], polynomial.coeffs)

        # Final debug assertion
        if self.debug:
            assert isinstance(commitment, self.G1)

        if self.debug:
            return Commitment(commitment, oob=(polynomial.coeffs))

        return Commitment(commitment)
    
    def prove_evaluation(self, polynomial: UniPolynomial, point) -> tuple[Field, dict]:
        """
        Open the polynomial at a given point.
        
        Args:
            polynomial: The polynomial to open
            point: The point at which the polynomial was opened
        
        Returns:
            tuple: (evaluation, proof)
                - evaluation: The value of the polynomial at the given point
                - proof: {'w': witness polynomial, 'hiding_v': hiding witness polynomial}
        """
        assert polynomial.degree + 1 < len(self.params['powers_of_g']), f"Too many coefficients, polynomial.degree: {polynomial.degree}"
        
        q_poly, v = self.compute_quotient_polynomial(polynomial, point)
        if self.debug:
            assert isinstance(q_poly, UniPolynomial)

        w_cm = msm_basic(self.params['powers_of_g'], q_poly.coeffs)

        return v, {'w_cm': Commitment(w_cm)}
    
    def verify_evaluation(self, cm: Commitment, point: Field, value: Field, proof: dict):
        """
        Check the validity of the proof.
        
        Args:
            comm: The commitment to check
            point: The point at which the polynomial was evaluated
            value: The value of the polynomial at the given point
            proof: The proof values
        
        Returns:
            bool: True if the proof is valid, False otherwise
        """
        f_cm = cm.cm
        f_cm -= self.params['powers_of_g'][0].ec_mul(value)
        w_cm = proof['w_cm'].cm

        f_cm += w_cm.ec_mul(point)

        lhs = (f_cm, self.params['h'])
        # rhs = (w_cm, self.params['tau_h'] - self.params['h'].ec_mul(point))
        rhs = (w_cm, self.params['tau_h'])

        checked = ec_pairing_check([lhs[0], rhs[0]], [-lhs[1], rhs[1]])

        return checked
    
    def batch_verify(self, commitments, points, values, proofs):
        """
        

        Theorem: 
            f(X) - f(z) = q(X) * (X - z)

        Verification equation:
            e(C - v*[1], [1]) = e([w], [s] - z*[1])

        To support batch verification, the above equation is changed to:
            f(X) - f(z) + q(X) * z = q(X) * X    
        
            e(C - v*[1] + z*[w], [1]) = e([w], [s])

        If we have 

            e(C1 - v1*[1] + z1*[w1], [1]) = e([w1], [s])
            e(C2 - v2*[1] + z2*[w2], [1]) = e([w2], [s])
            ...
            e(Cn - vn*[1] + zn*[wn], [1]) = e([wn], [s])

        Then we can sum up all the equations with a random linear combination:
            e(∑ rho^i * (Ci - vi*[1] + zi*[wi]), [1]) = e(∑ rho^i * ([wi]), [s])

        """
        batched_C = self.G1.zero()
        batched_W = self.G1.zero()

        # random linear combination
        rho = self.Scalar.one()
        g_multiplier = 0
        gamma_g_multiplier = 0

        for Ci, zi, vi, proofi in zip(commitments, points, values, proofs):
            Wi = proofi['w_cm']
            C = Wi.cm.ec_mul(zi) + Ci.cm
            g_multiplier += rho * vi
            batched_C += C.ec_mul(rho)
            batched_W += Wi.cm.ec_mul(rho)
            rho = self.Scalar.rand()

        batched_C -= self.params['powers_of_g'][0].ec_mul(g_multiplier)
        
        lhs = (batched_C, self.params['h'])
        rhs = (batched_W, self.params['tau_h'])
        checked = ec_pairing_check([lhs[0], rhs[0]], [-lhs[1], rhs[1]])

        return checked

    def prove_degree_bound(self, polynomial: UniPolynomial, deg_bound: int) -> Commitment:
        """
        Prove that polynomial f has degree **strictly less than** deg_bound.
            
            deg(f) < deg_bound

        suppose  f_cm = [f(X)] + [γr(X)]

            fx_cm = [f(X)X^{D - d - 1}]

            e(f_cm, [x^{D - d - 1}]) = e(fx_cm, [h])

        Args:
            polynomial: The polynomial to prove degree bound for
            deg_bound: The upper bound on the degree

        Returns:
            Commitment to the polynomial f * x^{max_degree - deg_bound - 1}
            
        Raises:
            AssertionError: If polynomial degree is not less than deg_bound
        """
        f = polynomial
        assert f.is_zero() == False, "Polynomial is zero"
        assert f.degree < deg_bound, f"Polynomial degree {f.degree} not less than bound {deg_bound}"
        
        # Multiply f by x_poly
        fx_coeffs = [Field(0)] * (self.max_degree - deg_bound - 1) + f.coeffs
        
        fx_cm = msm_basic(self.params['powers_of_g'], fx_coeffs)

        return Commitment(fx_cm)
    
    def verify_degree_bound(self, 
                          f_cm: Commitment, 
                          deg_bound: int, 
                          fx_cm: Commitment) -> bool:
        """
        Verify that polynomial committed in f_cm has degree less than deg_bound.
        
        Args:
            f_cm: Commitment to the polynomial
            deg_bound: The claimed degree bound
            fx_cm: The degree bound argument
            
        Returns:
            bool: True if the degree bound proof verifies
            
        Raises:
            AssertionError: If max_degree doesn't match
        """

        # Get x^(max_degree - deg_bound - 1) in G2
        x_in_g2 = self.params['powers_of_h'][self.max_degree - deg_bound - 1]
        
        # Get commitment to f * x
        fx_cm = fx_cm.cm
        f_cm = f_cm.cm
        
        # Check pairing equation
        # e(f_cm, x_in_g2) = e(fx_cm, h)
        lhs = (f_cm, x_in_g2)
        rhs = (fx_cm, self.params['h'])
        
        return ec_pairing_check([lhs[0], rhs[0]], [-lhs[1], rhs[1]])

    def debug_check_commitment(self, cm: Commitment, vs: tuple[Field]):
        assert self.debug, "Debug mode is not enabled"
        assert cm.oob is not None, "Commitment is not opened"
        assert len(cm.oob) == len(vs), f"Number of values mismatch, len(cm.oob): {len(cm.oob)}, len(vs): {len(vs)}"

    def prove_eval_and_degree(self, cm: Commitment, f: UniPolynomial, point: Field, degree_bound: int):
        """
        Prove the degree bound of a polynomial.

            f(X) - f(z) = q(X) * (X - z)
            
            arg: [x^{D-(d-1)} * q(x)]

            e([f(x)] - f(z)[1], [x^{D-(d-1)}]) = e([x^{D-(d-1)} * q(x)], [x]- z[1])
            
        Args:
            cm: commitment to the polynomial
            f: polynomial
            point: evaluation point
            degree_bound: degree bound
        """
        assert degree_bound <= self.max_degree, \
                "Degree bound exceeds maximum supported degree"
        coeffs = f.coeffs.copy()

        while len(coeffs) > 1 and coeffs[-1] == 0:
            coeffs.pop()

        assert len(coeffs) <= degree_bound, \
                "Polynomial degree exceeds maximum supported degree"
        
        # Compute the witness polynomial: (f(X) - f(z)) / (X - z)
        witness_poly, v = self.compute_quotient_polynomial(f, point)

        degree_gap = self.max_degree - degree_bound + 2
        lift_coeffs = [0] * degree_gap + witness_poly.coeffs
        xq_cm = self.commit(UniPolynomial(lift_coeffs))

        return v, (xq_cm, degree_gap)

    def verify_eval_and_degree(self, f_cm: Commitment, point: Field, v: Field, degree_bound: int, arg: tuple[Commitment, int]):
        """
        Verify the evaluation and degree bound of a polynomial.

        Args:
            f_cm: commitment to the polynomial
            arg: proof of the evaluation and degree bound
            point: evaluation point
            v: evaluation value
            degree_bound: degree bound
        """
        xq_cm, degree_gap = arg
        assert degree_gap >= self.max_degree - degree_bound + 2, \
                "Degree bound is less than the degree of the proof"
        h_gap = self.params['powers_of_h'][degree_gap]
        g = self.params['powers_of_g'][0]
        h_tau = self.params['tau_h']
        h = self.params['h']

        # Compute [v]
        # v_cm = g.ec_mul(v)

        # Compute [tau] - z[1]
        # h_tau_minus_h_point = h_tau - h_gap.ec_mul(point)

        # Check the pairing equation:
        # e([f(x)] - f(z)[1], [x^{D-(d-1)}]) = e([x^{D-(d-1)} * q(x)], [x]- z[1])
        # e(C - z[1], [tau^{D-d+1}]) = e(π, [s]H - [z]H)
        lhs = (f_cm.cm - g.ec_mul(v), h_gap)
        rhs = (xq_cm.cm, h_tau - h.ec_mul(point))

        return ec_pairing_check([lhs[0], rhs[0]], [-lhs[1], rhs[1]])


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

# def msm_bigint_wnaf(bases, bigints):
#     """
#     Implementation of multi-scalar multiplication using big integers and the Window NAF method.
    
#     Args:
#         bases: List of group elements
#         bigints: List of big integers
    
#     Returns:
#         Group element representing the result of the multi-scalar multiplication
#     """
#     WINDOW_SIZE = 5
#     result = 0
    
#     # Precompute window
#     precomp = [[base * i for i in range(1 << (WINDOW_SIZE - 1))] for base in bases]
    
#     for i in range(max(next_power_of_two(bigint) for bigint in bigints)):
#         result = result + result
#         for j, (base, scalar) in enumerate(zip(bases, bigints)):
#             if next_power_of_two(scalar) > i:
#                 window = (scalar >> i) & ((1 << WINDOW_SIZE) - 1)
#                 if window:
#                     if window >= (1 << (WINDOW_SIZE - 1)):
#                         result -= precomp[j][window - (1 << (WINDOW_SIZE - 1))]
#                     else:
#                         result += precomp[j][window - 1]
#     return result

def test_lagrange_basis(kzg):

    f = UniPolynomialWithFft([Field.rand() for _ in range(randint(5, 10))])

    kzg.setup_lagrange_basis(16)

    omega = Field.nth_root_of_unity(16)

    evals = f.compute_evaluations(16)
    f2 = UniPolynomialWithFft.interpolate(evals, 16)
    assert f.coeffs == f2.coeffs, "Interpolation should be the same polynomial"

    C1 = kzg.commit(f)
    C2 = kzg.commit_with_lagrange_basis(evals)

    assert C1.cm == C2.cm, "Commitment mismatch"
    print("test_lagrange_basis passed!")

def test_prove_verify_eval_and_degree(kzg):
    kzg = KZG10_PCS(G1, G2, Field, 16, debug=True)
    f = UniPolynomial([Field.rand() for _ in range(randint(5, 10))])
    point = Field.rand()
    degree_bound = len(f.coeffs)

    C = kzg.commit(f)   
    v, arg = kzg.prove_eval_and_degree(C, f, point, degree_bound)

    verified = kzg.verify_eval_and_degree(C, point, v, degree_bound, arg)
    assert verified, "Verification failed"
    print("test_prove_verify_eval_and_degree passed!")


if __name__ == '__main__':
    # Test regular check
    print("Testing regular check...")

    # Create KZG10 commitment scheme instance
    kzg = KZG10_PCS(G1, G2, Field, 20,debug=True)

    test_lagrange_basis(kzg)

    test_prove_verify_eval_and_degree(kzg)
    # # Create a polynomial and a point
    # test_poly = UniPolynomial([Field.rand() for _ in range(randint(5, 10))])
    # test_point = Field.rand()
    # print(f"test_poly: {test_poly}")



    # ######## TEST commit with lagrange basis

    # omega = Field.nth_root_of_unity(16)
    # domain = Domain_FFT_2Radix(16, Field.root_of_unity(), Field)
    # print(f"domain.points: {domain.points}")

    # evals = test_poly.compute_evaluations_fft(16, omega)
    # print(f"evals: {evals}")

    # coeffs = UniPolynomial.interpolate_fft(evals, omega)
    # print(f"coeffs: {coeffs}")
    
    # C1 = kzg.commit(test_poly)
    # kzg.setup_lagrange_basis(16)
    # C2 = kzg.commit_with_lagrange_basis(evals)
    # assert C1 == C2, "Commitment mismatch"



    # # Commit to the polynomial
    # cm, random_ints = kzg.commit(test_poly, hiding_bound=3)
    # print(f"random_ints: {random_ints}")

    # # Evaluate the polynomial
    # value = test_poly.evaluate(test_point)
    # print(f"value: {value}")

    # # Generate proof
    # v, proof = kzg.open(test_poly, test_point, random_ints)

    # assert v == value, f"Evaluation mismatch, v: {v}, value: {value}"
    
    # # Verification
    # verified = kzg.verify(cm, test_point, value, proof)
    # print(f"verified: {verified}")
    # assert verified, "Verification failed"
    
    # # Batched Verification
    # verified = kzg.batch_verify([cm], [test_point], [value], [proof])
    # print(f"batch-verified: {verified}")
    # assert verified, "Batch verification failed"

    # # 2 polynomials

    # test_poly2 = UniPolynomial([Field.rand() for _ in range(randint(12, 16))])
    # test_point2 = Field.rand()

    # cm2, random_ints2 = kzg.commit(test_poly2, hiding_bound=5)
    # print(f"random_ints2: {random_ints2}")

    # value2 = test_poly2.evaluate(test_point2)
    # print(f"value2: {value2}")

    # v2, proof2 = kzg.open(test_poly2, test_point2, random_ints2)

    # verified = kzg.batch_verify([cm, cm2], [test_point, test_point2], [value, value2], [proof, proof2])
    # print(f"batch-verified: {verified}")
    # assert verified, "Batch verification failed"

