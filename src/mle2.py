#!/usr/bin/env sage -python

from functools import reduce
from utils import log_2, pow_2, bits_le_with_width, Scalar
from curve import Fr as BN254_Fr
from typing import TypeVar, Generic

# TODO:
#  1. mle addition with different number of variables
#  2. mle multiplication

Field = TypeVar('Field')

class MLEPolynomial(Generic[Field]):

    F = BN254_Fr # default finite field 

    @classmethod
    def set_field_type(cls, field_type: type):
        cls.F = field_type
        one = cls.F.one()
        zero = cls.F.zero()
        assert one + zero == one, f"one + zero: {one + zero}"
        assert one * one == one, f"one * one: {one * one}"
        assert one * zero == zero, f"one * zero: {one * zero}"

        return

    def __init__(self, evals, num_var):
        assert len(evals) <= 2**num_var, "Evaluation length must be less than or equal to 2^num_var"

        self.evals = evals + [self.F.zero()] * (2**num_var - len(evals))
        self.num_var = num_var

    @classmethod
    def zero_polynomial(cls):
        f = cls([cls.F.zero()], 0)
        return f
    
    def is_zero(self):
        for i in range(2**self.num_var):
            if self.evals[i] != self.F.zero():
                return False
        return True
    
    def __repr__(self):
        return f"MLEPolynomial({self.evals}, {self.num_var})"
    
    def __getitem__(self, index):
        """
        Retrieve an evaluation using square bracket notation.

        Args:
            index (int): The index of the evaluation to retrieve.

        Returns:
            The evaluation at the given index.

        Raises:
            IndexError: If the index is out of range.
        """
        
        if 0 <= index < len(self.evals):
            return self.evals[index]
        else:
            raise IndexError("Evaluation index out of range")
    
    def __len__(self):
        return len(self.evals)

    def sub(self, g: 'MLEPolynomial'):
        if g.is_zero():
            return self
        neg_g = g.scalar_mul(Scalar(self.F(-1)))
        return self.add(neg_g)

    def add(self, g: 'MLEPolynomial'):
        if g.is_zero() or self.is_zero():
            return g if self.is_zero() else self
        assert self.num_var == g.num_var, "Number of variables must match"
        evals = [self.evals[i] + g.evals[i] for i in range(len(self.evals))]
        return MLEPolynomial(evals, self.num_var)
    
    def scalar_mul(self, s: Scalar):
        if self.is_zero():
            return self
        evals = [self.evals[i] * s.value for i in range(len(self.evals))]
        return MLEPolynomial(evals, self.num_var)
    
    def __add__(self, other):
        return self.add(other)
    
    def __sub__(self, other):
        return self.sub(other)
    
    def __neg__(self):
        return self.scalar_mul(Scalar(self.F(-1)))

    def __rmul__(self, other):
        """
        Overload the * operator for right multiplication (scalar * polynomial).

        Args:
            other (scalar): The scalar to multiply with this polynomial.

        Returns:
            UniPolynomial: Scalar multiplication result.
        """
        if isinstance(other, Scalar):
            return self.scalar_mul(other)
        else:
            raise TypeError("Unsupported operand type for *: '{}' and '{}'".format(type(other).__name__, type(self).__name__))

    @classmethod
    def compute_monomials(cls, rs):
        k = len(rs)
        n = 1 << k
        evals = [cls.F.one()] * n
        half = 1
        for i in range(k):
            for j in range(half):
                evals[j+half] = evals[j] * rs[i]
            half *= 2
        return evals

    @classmethod
    def eqs_over_hypercube(cls, rs):
        k = len(rs)
        n = 1 << k
        evals = [cls.F.one()] * n
        half = 1
        for i in range(k):
            for j in range(half):
                evals[j+half] = evals[j] * rs[i]
                evals[j] = evals[j] - evals[j+half]
            half *= 2
        return evals
    
    @classmethod
    def eqs_over_hypercube_slow(cls, k, indeterminates):
        if k > 5:
            raise ValueError("k>5 isn't supported")
        xs = indeterminates[:k]
        n = 1 << k
        eqs = [1] * n
        for i in range(n):
            bs = bits_le_with_width(i, k)
            eqs[i] = reduce(lambda v, j: v * ((1 - xs[j]) * (1 - bs[j]) + xs[j] * bs[j]), range(k), 1)
        return eqs

    @classmethod
    def from_coeffs(cls, coeffs: list[Field], num_var: int) -> 'MLEPolynomial':
        return cls(cls.compute_evals_from_coeffs(coeffs), num_var)
    
    def to_coeffs(self) -> list[Field]:
        return self.compute_coeffs_from_evals(self.evals)
    
    @classmethod
    def ntt_core(cls, vs, twiddle):
        n = len(vs)
        k = log_2(n)
        half = 1
        for i in range(k):
            for j in range(0, n, 2*half):
                for l in range(j, j+half):
                    vs[l+half] = vs[l+half] + twiddle * vs[l]
            half <<= 1
        return vs   

    @classmethod
    def compute_evals_from_coeffs(cls, f_coeffs: list[Field]) -> list[Field]:
        """
        Compute the evaluations of the polynomial from the coefficients.
            Time: O(n * log(n))
        """
        coeffs = [f_coeffs[i] for i in range(len(f_coeffs))]
        return cls.ntt_core(coeffs, cls.F.one())

    @classmethod
    def compute_coeffs_from_evals(cls, f_evals):
        """
        Compute the evaluations of the polynomial from the coefficients.
            Time: O(n * log(n))
        """
        evals = [f_evals[i] for i in range(len(f_evals))]
        return cls.ntt_core(evals, cls.F(-1))
    
    @classmethod
    def evaluate_from_evals(cls, evals: list[Field], zs: list[Field]) -> Field:
        f = evals

        half = len(f) >> 1
        for z in zs:
            even = f[::2]
            odd = f[1::2]
            f = [even[i] + z * (odd[i] - even[i]) for i in range(half)]
            half >>= 1
        return f[0]
    
    @classmethod
    def evaluate_from_evals_2(cls, evals: list[Field], zs: list[Field]) -> Field:
        k = len(zs)
        f = evals

        half = len(f) >> 1
        for i in range(k):
            u = zs[k-i-1]

            f = [(1-u) * f[j] + u * f[j+half] for j in range(half)]
            half >>= 1
        
        return f[0]
    
    @classmethod
    def evaluate_eq_polynomial(cls, zs: list[Field], us: list[Field]) -> Field:

        k = len(zs)
        assert k == len(us), f"len(zs) != len(us), len(zs) = {len(zs)}, len(us) = {len(us)}"
        v = cls.F.one()
        for i in range(k):
            # v *= (cls.F.one() - us[i]) * (cls.F.one() - zs[i]) + us[i] * zs[i]
            v *= cls.F.one() + 2 * (us[i] * zs[i]) - (us[i] + zs[i])
        return v

    def evaluate(self, zs: list):
        """
        Evaluate the MLE polynomial at the given points.

        Args:
            zs (list): List of points to evaluate the polynomial at.

        Returns:
            int: The evaluated value of the polynomial at the given points.
        """
        if not isinstance(zs, list):
            raise TypeError("Input zs must be a list.")
        
        return self.evaluate_from_evals(self.evals, zs)
    
    def partial_evaluate(self, zs: list):
        """
        Partial evaluate the MLE polynomial at the given points.
        """
        assert self.num_var >= len(zs), \
            f"Number of variables must be greater than or equal to the length of zs: {self.num_var} >= {len(zs)}"   
        
        k = self.num_var
        l = len(zs)
        f = self.evals
        half = len(f) >> 1
        for z in zs:
            f_even = f[::2]
            f_odd = f[1::2]
            f = [(self.F(1) - z) * f_even[i] + z * f_odd[i] for i in range(half)]
            half >>= 1
        return MLEPolynomial(f, k-l)

    @staticmethod
    def evaluate_from_coeffs(coeffs, zs):
        z = len(zs)
        f = coeffs

        half = len(f) >> 1
        for z in zs:
            even = f[::2]
            odd = f[1::2]
            f = [even[i] + z * odd[i] for i in range(half)]
            half >>= 1
        return f[0]

    def decompose_by_div(self, point):
        """
        Divide an MLE at the point: [X_0, X_1, ..., X_{n-1}] in O(N) (Linear!)

        References:
            1. Algorithm 8 in Appendix B, [XZZPS18] 
                "Libra: Succinct Zero-Knowledge Proofs with Optimal Prover Computation"
            2. Appendix A.2 in [KT23] "ZeroMorph" paper
                URL: https://eprint.iacr.org/2023/917
        Args:
            self (MLEPolynomial): the MLE polynomial to be divided
            point (list): the point to divide the polynomial

        Returns:
            list: quotients, the list of MLEs
            evaluation: the evaluation of the polynomial at the point
        """
        assert self.num_var == len(point), "Number of variables must match the point"
        e = self.evals.copy()
        k = self.num_var
        quotients = []
        half = pow_2(k - 1)
        for i in range(k):
            q = [0] * half
            for j in range(half):
                q[j] = e[j + half] - e[j]
                e[j] = e[j] * (1 - point[k-i-1]) + e[j + half] * point[k-i-1]
            quotients.insert(0, MLEPolynomial(q, k-i-1))
            half >>= 1

        return quotients, e[0]
    
    @classmethod
    def decompose_by_div_from_coeffs(cls, coeffs: list[Field], point: list[Field]) -> tuple[list[Field], Field]:
        """
        Decompose the MLE polynomial into quotients by division.

            f(X0,X1,...,X_{n-1}) = (X0-u0) * q0 
                                + (X1-u1) * q1(X0) + ... 
                                + (X_{n-1} - u_{n-1}) * q_{n-1}(X0,X1,...,X_{n-2})
                                + f(u0, u1, ..., u_{n-1})
        
        Args:
            coeffs (list[Field]): The coefficients of the MLE polynomial to be divided
            point (list[Field]): The point to divide the polynomial

        Returns:
            list[Field]: Quotients [q_0, q_1, ..., q_{n-1}] where q_i(X_0, X_1, ..., X_{i-1})
        """
        
        k = len(point)
        n = len(coeffs)
        assert n == pow_2(k), "Number of variables must match the point"
        
        coeffs = coeffs.copy()
        quotients = []
        half = pow_2(k - 1)
        for i in range(k):
            quo_coeffs = [0] * half
            for j in range(half):
                quo_coeffs[j] = coeffs[j + half]
                coeffs[j] = coeffs[j] + point[k-i-1] * coeffs[j + half]
            quotients.insert(0, quo_coeffs)
            half >>= 1

        return quotients, coeffs[0]
    
    @classmethod
    def mul_quotients(cls, quotient: 'MLEPolynomial', remainder: 'MLEPolynomial', p: Field) -> 'MLEPolynomial':
        """
        r: current remainder
        q: current quotient
        p: current point

        last_remainder
        = r + (xi - p) * q
        = r - p * q + xi * q
        = (r - p * q) * (1 - xi) + (r - (p - 1) * q) * xi
        """

        assert isinstance(quotient, MLEPolynomial), "quotient must be an MLEPolynomial"
        assert isinstance(remainder, MLEPolynomial), "remainder must be an MLEPolynomial"

        half = len(quotient.evals)
        result = [0] * 2 * half
        for i, (q, r) in enumerate(zip(quotient.evals, remainder.evals)):
            result[i] = r - p * q
            result[i + half] = r - (p - 1) * q
        return MLEPolynomial(result, quotient.num_var + 1)
