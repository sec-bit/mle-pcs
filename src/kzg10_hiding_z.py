#!/usr/bin/env python3

# WARNING: This implementation may contain bugs and has not been audited. 
# It is only for educational purposes. DO NOT use it in production.

# Implementation of KZG10 (Zeromorph version)
#
#   - one single randomness for commitment and more randomness for evaluation arguments
#   - one additional pairing in verification

# from typing import Optional
from curve import Fp, Fr as Field, ec_mul, ec_mul_group2, G1Point as G1, G2Point as G2, ec_pairing_check
from unipoly import UniPolynomial
from random import randint
from utils import is_power_of_two, bits_le_with_width, bit_reverse, log_2

class Commitment:
    """Represents a commitment in the KZG scheme."""
    def __init__(self, cm, oob=None):
        self.cm = cm
        self.group = type(cm)
        self.scalar = Field
        if oob is not None:
            self.value = oob

    @staticmethod
    def zero(self):
        """Create a zero commitment."""
        return Commitment(self.group.zero())

    def __add__(self, other):
        """Add two commitments using + operator."""
        if not isinstance(other, Commitment) or self.group != other.group:
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

class KZG10_PCS:
    """KZG10 commitment scheme implementation."""
    params: dict

    def __init__(self, G1, G2, Scalar, max_degree, debug=False):
        """
        Initialize the KZG10 commitment scheme.
        
        Args:
            G1, G2: Elliptic curve groups
            Scalar: Scalar field
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

            G1 : [1]_1, [tau]_1, [tau^2]_1,     ..., [tau^max_degree]_1, [xi]_1
            G2 : [1]_2, [tau]_2, [xi]_2
        
        Args:
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

        # xi: randomness used for hiding
        xi = self.Scalar.rand()
        # [xi]_1
        xi_g = g.ec_mul(xi)
        # [xi]_2
        xi_h = h.ec_mul(xi)

        powers_of_tau = [tau ** i for i in range(self.max_degree + 2)]
        # [1]_1, [τ]_1, [τ^2]_1, ..., [τ^{max_degree + 1}]_1
        powers_of_tau_g: list[self.G1] = [g.ec_mul(powers_of_tau[i]) for i in range(self.max_degree + 1)]
        # [1]_2, [τ]_2, [τ^2]_2, ..., [τ^{max_degree}]_2
        powers_of_tau_h: list[self.G2] = [h.ec_mul(powers_of_tau[i]) for i in range(self.max_degree + 1)]

        self.params = {}
        self.params['powers_of_tau_g'] = powers_of_tau_g
        self.params['powers_of_tau_h'] = powers_of_tau_h
        self.params['g'] = g
        self.params['xi_g'] = xi_g
        self.params['tau_g'] = powers_of_tau_g[1]
        self.params['h'] = h
        self.params['tau_h'] = h.ec_mul(tau)
        self.params['xi_h'] = xi_h

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

    # NOTE: This function is only used internally.
    def compute_quotient_polynomial(self, polynomial: UniPolynomial, point):
        """
        Compute the quotient polynomial for a given polynomial and point.
        
        Args:
            polynomial: The polynomial to compute the witness polynomial for
            point: The point at which to evaluate the polynomial
        
        Returns:
            tuple: witness polynomial
        """
        quotient, evaluation = polynomial.division_by_linear_divisor(point)
        return quotient, evaluation
    
    def commit_with_lagrange_basis(self, evaluations: list[Field]) -> tuple[Commitment, Field]:
        """
        Commit to a polynomial with Lagrange basis.
        
        Args:
            evaluations: The evaluations of the polynomial at the Lagrange basis points
        
        Returns:
            tuple: (Commitment, randomness)
                - Commitment: The commitment to the polynomial
                - randomness: The random scalar used for hiding
        """
        # Check if polynomial degree is too large
        domain_size = len(evaluations)
        num_lagrange_basis = len(self.params['lagrange_of_g'])
        assert domain_size == num_lagrange_basis, f"Number of evaluation points must be equal to the number of Lagrange basis points, domain_size: {domain_size}, num_lagrange_basis: {num_lagrange_basis}"

        # Commitment calculation
        cm = msm_basic(self.params['lagrange_of_g'], evaluations)

        # while UniPolynomial(random_ints).degree == 0:
        r = self.Scalar.rand() 
        assert r != self.Scalar.zero(), f"Random scalar is zero, r: {r}"

        hiding_cm = self.params['xi_g'].ec_mul(r)
        cm += hiding_cm

        # Final debug assertion
        if self.debug:
            assert isinstance(cm, self.G1)

        if self.debug:
            return Commitment(cm, oob=(evaluations, r)), r

        return Commitment(cm), r
    

    def commit(self, polynomial: UniPolynomial) -> tuple[Commitment, Field]:
        """
        Commit to a polynomial.
        
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

        r = self.Scalar.rand()
        assert r != self.Scalar.zero(), f"Random scalar is zero, r: {r}"

        hiding_cm = self.params['xi_g'].ec_mul(r)
        cm += hiding_cm

        # Final debug assertion
        if self.debug:
            assert isinstance(cm, self.G1)

        if self.debug:
            return Commitment(cm, oob=(polynomial.coeffs)), r

        return Commitment(cm), r
    
    def prove_evaluation(self, polynomial: UniPolynomial, point: Field, randomness: Field) -> tuple[Field, dict]:
        """
        Open the polynomial at a given point.

            f(X) - v = q(X) * (X - z)

            <=> (f(X) + r{xi}) - v = (q(X) + s{xi}) * (X - z) + (r - s(tau - z)) * {xi}

            <=> e(F - v[1], [1])= e(W, [tau] - z*[1]) + e(R, [xi])
        
            where R = r[1] - s[tau] + sz[1]
        Args:
            polynomial: The polynomial to open
            point: The point at which the polynomial was opened
            randomness: The random scalar used for hiding commitment
        
        Returns:
            tuple: (evaluation, proof)
                - evaluation: The value of the polynomial at the given point
                - proof: {'w_cm': witness polynomial, 's_cm': hiding witness polynomial}
        """
        # assert not polynomial.is_zero(), "Polynomial is zero"
        assert polynomial.degree + 1 < len(self.params['powers_of_tau_g']), f"Too many coefficients, polynomial.degree: {polynomial.degree}"
        
        q_poly, v = self.compute_quotient_polynomial(polynomial, point)

        if self.debug:
            assert isinstance(q_poly, UniPolynomial)

        w_cm = msm_basic(self.params['powers_of_tau_g'], q_poly.coeffs)
        s = self.Scalar.rand()
        w_cm += self.params['xi_g'].ec_mul(s)

        s_cm = self.params['g'].ec_mul(randomness + s * point) - self.params['tau_g'].ec_mul(s)

        return v, {'w_cm': Commitment(w_cm), 's_cm': Commitment(s_cm)}
    
    def verify_evaluation(self, f_cm: Commitment, point: Field, value: Field, argument: dict) -> bool:
        """
        Check the validity of the proof.

                e(F - v[1] + z*W, [1])= e(W, [tau]) + e(R, [xi])

            where R = r[1] - s[tau] + sz[1]

        Args:
            f_cm: The commitment to check
            point: The point at which the polynomial was evaluated
            value: The value of the polynomial at the given point
            argument: The proof values
        
        Returns:
            bool: True if the proof is valid, False otherwise
        """
        cm = f_cm.cm - self.params['g'].ec_mul(value) + argument['w_cm'].cm.ec_mul(point)

        lhs = (cm, self.params['h'])
        # rhs0 = (argument['w_cm'].cm, self.params['tau_h'] - self.params['h'].ec_mul(point))
        rhs0 = (argument['w_cm'].cm, self.params['tau_h'])
        rhs1 = (argument['s_cm'].cm, self.params['xi_h'])

        checked = ec_pairing_check([lhs[0], rhs0[0], rhs1[0]], [-lhs[1], rhs0[1], rhs1[1]])
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

    #     batched_C -= self.params['powers_of_tau_g'][0].ec_mul(g_multiplier)
    #     batched_C -= self.params['powers_of_gamma_g'][0].ec_mul(gamma_g_multiplier)
        
    #     lhs = (batched_C, self.params['h'])
    #     rhs = (batched_W, self.params['tau_h'])

    #     checked = ec_pairing_check([lhs[0], rhs[0]], [-lhs[1], rhs[1]])

    #     return checked

    def prove_degree_bound(self, polynomial: UniPolynomial, deg_bound: int, randomness: Field) -> tuple[Commitment, Commitment]:
        """
        Prove that polynomial f has degree **strictly less than** deg_bound.
            
            deg(f) < deg_bound

        suppose  f_cm = [f(X)] + [γr(X)]

            fx_cm = [f(X)X^{D - d - 1}] + s[γ], where s is random
            rx_cm = [r(X)X^{D - d - 1}] - s[1]

            f_cm * [x^{D - d - 1}]  

            = ([f(X)] + [γr(X)]) * [x^{D - d - 1}] 
            
            = ([f(X)X^{D - d - 1}] + r[γ]) * [1] + ([r(X)X^{D - d - 1}] - s[1]) * [γ]

        Args:
            polynomial: The polynomial to prove degree bound for
            deg_bound: The upper bound on the degree
            randomness: The random scalar used for hiding

        Returns:
            tuple: (Commitment to the polynomial f * x^{max_degree - deg_bound - 1}, 
                    Commitment to the polynomial r * x^{max_degree - deg_bound - 1})

        Raises:
            AssertionError: If polynomial degree is not less than deg_bound
        """

        f = polynomial
        assert f.degree < deg_bound, f"Polynomial degree {f.degree} not less than bound {deg_bound}"
        
        # Create polynomial x^{max_degree - deg_bound - 1}
        coeffs = [f.coeffs[i] for i in range(len(f.coeffs))]
        coeffs = [Field(0)] * (self.max_degree - deg_bound) + coeffs
        fx_poly = UniPolynomial(coeffs)
        fx_cm = msm_basic(self.params['powers_of_tau_g'], fx_poly.coeffs)

        s = self.Scalar.rand()
        s_cm = self.params['xi_g'].ec_mul(s)
        fx_cm += s_cm

        rx_cm = self.params['powers_of_tau_g'][self.max_degree - deg_bound].ec_mul(randomness)
        rx_cm -= self.params['g'].ec_mul(s)

        return Commitment(fx_cm), Commitment(rx_cm)
    
    def verify_degree_bound(self, 
                          f_cm: Commitment, 
                          deg_bound: int, 
                          fx_cm: Commitment,
                          rx_cm: Commitment) -> bool:
        """
        Verify that polynomial committed in f_cm has degree less than deg_bound.
        
        Args:
            f_cm: Commitment to the polynomial
            deg_bound: The claimed degree bound
            fx_cm: The commitment to the polynomial f * x^{max_degree - deg_bound - 1}
            rx_cm: The commitment to the randomness polynomial r * x^{max_degree - deg_bound - 1}
            
        Returns:
            bool: True if the degree bound proof verifies
            
        Raises:
            AssertionError: If max_degree doesn't match
        """

        # Get x^(max_degree - deg_bound) in G2
        x_poly_in_g2 = self.params['powers_of_tau_h'][self.max_degree - deg_bound]
        
        # Get commitment to f * x
        fx_cm = fx_cm.cm
        f_cm = f_cm.cm
        rx_cm = rx_cm.cm
        
        # Check pairing equation
        # e(f_cm, x_in_g2) = e(fx_cm, h)
        lhs = (f_cm, x_poly_in_g2)
        rhs0 = (fx_cm, self.params['h'])
        rhs1 = (rx_cm, self.params['xi_h'])
        
        return ec_pairing_check([lhs[0], rhs0[0], rhs1[0]], [-lhs[1], rhs0[1], rhs1[1]])

    def prove_evaluation_with_degree_bound(self, polynomial: UniPolynomial, point: Field, deg_bound: int, randomness: Field) -> tuple[Field, dict]:
        """
        Open the polynomial at a given point and prove degree bound.
        Args:
            polynomial: The polynomial to open
            point: The point at which the polynomial was opened
            deg_bound: The upper bound on the degree
            randomness: The random scalar used for hiding commitment
        
        Returns:
            tuple: (evaluation, proof)
                - evaluation: The value of the polynomial at the given point
                - proof: {'w_cm': witness polynomial, 's_cm': hiding witness polynomial}
        """
        # assert not polynomial.is_zero(), "Polynomial is zero"
        assert polynomial.degree + 1 < len(self.params['powers_of_tau_g']), f"Too many coefficients, polynomial.degree: {polynomial.degree}"
        
        q_poly, v = self.compute_quotient_polynomial(polynomial, point)

        if self.debug:
            assert isinstance(q_poly, UniPolynomial)

        qx_coeffs = [self.Scalar(0)] * (self.max_degree - deg_bound) + q_poly.coeffs
        qx_cm = msm_basic(self.params['powers_of_tau_g'], qx_coeffs)
        s = self.Scalar.rand()
        qx_cm += self.params['xi_g'].ec_mul(s)

        rx_cm = self.params['powers_of_tau_g'][self.max_degree - deg_bound].ec_mul(randomness)
        rx_cm -= self.params['tau_g'].ec_mul(s)
        rx_cm += self.params['g'].ec_mul(s*point)

        return v, {'qx_cm': Commitment(qx_cm), 'rx_cm': Commitment(rx_cm)}
    
    def verify_evaluation_with_degree_bound(self, polynomial_cm: Commitment, point: Field, value: Field, deg_bound: int, argument: dict) -> bool:
        """
        Check the validity of the proof.

        Args:
            f_cm: The commitment to check
            point: The point at which the polynomial was evaluated
            value: The value of the polynomial at the given point
            argument: The proof values
        
        Returns:
            bool: True if the proof is valid, False otherwise
        """
        f_cm = polynomial_cm.cm

        cm = f_cm - self.params['g'].ec_mul(value)

        x_poly_in_g2 = self.params['powers_of_tau_h'][self.max_degree - deg_bound]

        lhs = (cm, x_poly_in_g2)
        rhs0 = (argument['qx_cm'].cm, self.params['tau_h'] - self.params['h'].ec_mul(point))
        rhs1 = (argument['rx_cm'].cm, self.params['xi_h'])

        checked = ec_pairing_check([lhs[0], rhs0[0], rhs1[0]], [-lhs[1], rhs0[1], rhs1[1]])
        return checked

    def debug_check_commitment(self, cm: Commitment, vs: tuple[Field]):
        assert self.debug, "Debug mode is not enabled"
        assert cm.oob is not None, "Commitment is not opened"
        assert len(cm.oob[0]) == len(vs), f"Number of values mismatch, len(cm.oob): {len(cm.oob)}, len(vs): {len(vs)}"

    # @staticmethod
    # def division_by_linear_divisor(coeffs, d):
    #     """
    #     Perform polynomial division by a linear divisor.
        
    #     Args:
    #         coeffs: List of polynomial coefficients
    #         d: The constant number in the divisor
        
    #     Returns:
    #         tuple: (quotient coefficients, remainder)
    #     """
    #     assert len(coeffs) > 1, "Polynomial degree must be at least 1"

    #     quotient = [0] * (len(coeffs) - 1)
    #     remainder = 0

    #     for i, coeff in enumerate(reversed(coeffs)):
    #         if i == 0:
    #             remainder = coeff
    #         else:
    #             quotient[-i] = remainder
    #             remainder = remainder * d + coeff

    #     return quotient, remainder

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


if __name__ == '__main__':
    # Test regular check
    print("Testing regular check...")

    # Create KZG10 commitment scheme instance
    kzg = KZG10_PCS(G1, G2, Field, 20, debug=True)



