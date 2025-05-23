#!/usr/bin/env python3

from typing import TypeVar, Generic
from utils import log_2, pow_2, is_power_of_two, prime_field_inv, log_2_ceiling, next_power_of_two, bit_reverse
from utils import Scalar
from curve import Fp, Fr

# TODO: 
#  1. Rewrite fft_coset_core() with RBO output
#  2. Iterative construct_subproduct_tree() 
#  3. Karatsuba polynomial multiplication
#  4. precompute_fft_twiddles()

Field = TypeVar('Field', bound=Fr)


class Domain_FFT_2Radix(Generic[Field]):
    size: int
    points: list[Field]
    field_type: type[Field]

    def __init__(self, size: int, omega: Field, field_type: type[Field]):
        self.size = size
        assert is_power_of_two(size)
        
        self.points = []
        omega = field_type.nth_root_of_unity(size)
        a = field_type.one()
        for i in range(size):
            self.points.append(a)
            a = a * omega
        return

class UniPolynomial(Generic[Field]):
    """
    Univariate polynomial with coefficients in a prime field F.

        F[X]
    """

    F = Fr

    @classmethod
    def set_field_type(cls, field_type: type):
        cls.F = field_type
        one = field_type.one()
        zero = field_type.zero()
        return

    @classmethod
    def remove_leading_zeros(cls, coeffs: list[Field]):
        """
        Remove leading zeros from a polynomial.
        """
        # coeffs2 = coeffs.copy()
        while len(coeffs) > 1 and coeffs[-1] == cls.F.zero():
            coeffs.pop()
        return
    
    def __init__(self, coeffs: list[Field]):
        """
        Initialize a UniPolynomial instance.

        Args:
            coeffs (list): Coefficients of the polynomial.
        """

        assert len(coeffs) > 0, "Coefficients cannot be empty"

        field_type = type(coeffs[0])
        coeffs2 = coeffs.copy()
        self.remove_leading_zeros(coeffs2)

        if len(coeffs2) == 1 and coeffs2[0] == self.F.zero():
            self.degree = None
            self.coeffs = coeffs2
            self.__class__.F = field_type
            return
        
        self.coeffs = coeffs2
        self.degree = len(coeffs2) - 1
        self.__class__.F = field_type
        return

    def is_zero(self):
        if len(self.coeffs) == 0 and self.degree == None:
            return True
        if self.degree == None and len(self.coeffs) == 1 and self.coeffs[0] == self.F.zero():
            return True
        return False


    def add(self, other: 'UniPolynomial[Field]') -> 'UniPolynomial[Field]':
        """
        Add two UniPolynomial instances.

        Args:
            poly1 (UniPolynomial): First polynomial.
            poly2 (UniPolynomial): Second polynomial.

        Returns:
            UniPolynomial: Sum of the two polynomials.
        """
        result_coeffs = self.polynomial_addition(self.coeffs, other.coeffs)
        return UniPolynomial(result_coeffs)

    @classmethod
    def polynomial_subtraction(cls, a: list[Field], b: list[Field]) -> list[Field]:
        """
        Subtract two UniPolynomial instances.

        Args:
            poly1 (UniPolynomial): First polynomial.
            poly2 (UniPolynomial): Second polynomial to subtract from the first.

        Returns:
            UniPolynomial: Difference of the two polynomials.
        """
        max_degree = max(len(a), len(b))
        result_coeffs = [cls.F.zero()] * (max_degree + 1)

        for i in range(max_degree + 1):
            coeff1 = a[i] if i < len(a) else cls.F.zero()
            coeff2 = b[i] if i < len(b) else cls.F.zero()
            result_coeffs[i] = coeff1 - coeff2

        # Remove leading zeros
        cls.remove_leading_zeros(result_coeffs)

        return result_coeffs
    
    def subtract(self, other: 'UniPolynomial[Field]') -> 'UniPolynomial[Field]':
        """
        Subtract two UniPolynomial instances.

        Args:
            poly1 (UniPolynomial): First polynomial.
            poly2 (UniPolynomial): Second polynomial to subtract from the first.

        Returns:
            UniPolynomial: Difference of the two polynomials.
        """
        coeffs = self.polynomial_subtraction(self.coeffs, other.coeffs)
        return UniPolynomial(coeffs)

    def mul(self, other: 'UniPolynomial[Field]') -> 'UniPolynomial[Field]':
        """
        Multiply two UniPolynomial instances.

        Args:
            poly1 (UniPolynomial): First polynomial.
            poly2 (UniPolynomial): Second polynomial.

        Returns:
            UniPolynomial: Product of the two polynomials.
        """
        coeffs = self.polynomial_multiplication(self.coeffs, other.coeffs)
        return UniPolynomial(coeffs)
    
    def mul_scalar(self, s: Scalar):
        if self.is_zero():
            return self
        coeffs = [coeff * s.value for coeff in self.coeffs]
        return UniPolynomial(coeffs)

    @classmethod
    def divmod(cls, dividend, divisor):
        """
        Divide two UniPolynomial instances and return quotient and remainder.

        Args:
            dividend (UniPolynomial): Dividend polynomial.
            divisor (UniPolynomial): Divisor polynomial.

        Returns:
            tuple: (quotient, remainder), where quotient and remainder are UniPolynomial instances.
        """
        # q, r = cls.polynomial_division_with_remainder(dividend.coeffs, divisor.coeffs)
        q, r = cls.polynomial_division_with_remainder_fast(dividend.coeffs, divisor.coeffs)
        return cls(q), cls(r)

    def __neg__(self):
        """
        Negate the polynomial.

        Returns:
            UniPolynomial: A new polynomial with all coefficients negated.
        """
        return UniPolynomial([-coeff for coeff in self.coeffs])
    

    def __add__(self, other: 'UniPolynomial[Field]'):
        if isinstance(other, Scalar):
            # If adding with a number, treat it as a constant polynomial
            return UniPolynomial([self.coeffs[0] + other.value] + self.coeffs[1:])
        elif isinstance(other, UniPolynomial):
            return self.add(other)
        else:
            raise TypeError(f"Unsupported operand type for +: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __sub__(self, other):
        """
        Overload the - operator for UniPolynomial instances.

        Args:
            other (UniPolynomial): The polynomial to subtract from this one.

        Returns:
            UniPolynomial: Difference of the two polynomials.
        """
        if isinstance(other, Scalar):
            return UniPolynomial([self.coeffs[0] - other.value] + self.coeffs[1:])
        elif isinstance(other, UniPolynomial):
            return self.subtract(other)
        else:
            raise TypeError("Unsupported operand type for -: '{}' and '{}'".format(type(self).__name__, type(other).__name__))
   
    def __mul__(self, other):
        """
        Overload the * operator for UniPolynomial instances.

        Args:
            other (UniPolynomial or scalar): The polynomial or scalar to multiply with this one.

        Returns:
            UniPolynomial: Product of the two polynomials or scalar multiplication result.
        """
        if isinstance(other, UniPolynomial):
            return self.mul(other)
        elif isinstance(other, Scalar):  # Scalar multiplication
            return self.mul_scalar(other)
        else:
            raise TypeError("Unsupported operand type for *: '{}' and '{}'".format(type(self).__name__, type(other).__name__))

    def __rmul__(self, other):
        """
        Overload the * operator for right multiplication (scalar * polynomial).

        Args:
            other (scalar): The scalar to multiply with this polynomial.

        Returns:
            UniPolynomial: Scalar multiplication result.
        """
        if isinstance(other, Scalar):
            return self.mul_scalar(other)
        else:
            raise TypeError("Unsupported operand type for *: '{}' and '{}'".format(type(other).__name__, type(self).__name__))

    def __divmod__(self, other):
        """
        Implement the divmod operation for UniPolynomial instances.

        Args:
            other (UniPolynomial): The divisor polynomial.

        Returns:
            tuple: (quotient, remainder), where quotient and remainder are UniPolynomial instances.
        """
        if isinstance(other, UniPolynomial):
            return self.divmod(self, other)
        else:
            raise TypeError("Unsupported operand type for divmod: '{}' and '{}'".format(type(self).__name__, type(other).__name__))

    def __floordiv__(self, other):
        """
        Implement floor division (quotient) for UniPolynomial instances.

        Args:
            other (UniPolynomial): The divisor polynomial.

        Returns:
            UniPolynomial: The quotient polynomial.
        """
        if isinstance(other, UniPolynomial):
            return self.divmod(self, other)[0]
        else:
            raise TypeError("Unsupported operand type for //: '{}' and '{}'".format(type(self).__name__, type(other).__name__))

    def __mod__(self, other):
        """
        Implement modulo operation (remainder) for UniPolynomial instances.

        Args:
            other (UniPolynomial): The divisor polynomial.

        Returns:
            UniPolynomial: The remainder polynomial.
        """
        if isinstance(other, UniPolynomial):
            return self.divmod(self, other)[1]
        else:
            raise TypeError("Unsupported operand type for %: '{}' and '{}'".format(type(self).__name__, type(other).__name__))

    def __eq__(self, other):
        if isinstance(other, UniPolynomial):
            return self.coeffs == other.coeffs
        else:
            raise TypeError("Unsupported operand type for ==: '{}' and '{}'".format(type(self).__name__, type(other).__name__))
    
    def __repr__(self):
        """
        Return a string representation of the polynomial.
        """
        terms = []
        for i, coeff in enumerate(self.coeffs):
            if coeff != 0 and coeff != 1:
                if i == 0:
                    terms.append(str(coeff))
                elif i == 1:
                    terms.append(f"{coeff}x")
                else:
                    terms.append(f"{coeff}x^{i}")
            elif coeff == 1:
                if i == 0:
                    terms.append(str(coeff))
                elif i == 1:
                    terms.append(f"x")
                else:
                    terms.append(f"x^{i}")
        return " + ".join(terms) if terms else "0"
    
    @classmethod
    def polynomial_addition(cls, a: list[Field], b: list[Field]) -> list[Field]:
        """
        Add two polynomials represented as lists of coefficients.

        Args:
            a (list): Coefficients of the first polynomial.
            b (list): Coefficients of the second polynomial.

        Returns:
            list: Coefficients of the sum polynomial.
        """
        # Determine the length of the resulting polynomial
        max_len = max(len(a), len(b))
        
        # Pad the shorter polynomial with zeros
        a_padded = a + [cls.F.zero()] * (max_len - len(a))
        b_padded = b + [cls.F.zero()] * (max_len - len(b))
        
        # Add the coefficients
        result = [a_padded[i] + b_padded[i] for i in range(max_len)]
        
        cls.remove_leading_zeros(result)
        
        return result

    @classmethod
    def polynomial_scalar_multiplication(cls, a: list[Field], s: Field) -> list[Field]:
        """
        Multiply a polynomial by a scalar.

        Args:
            a (list): Coefficients of the polynomial.
            s (F): The scalar to multiply the polynomial by.

        Returns:
            list: Coefficients of the resulting polynomial.
        """
        assert len(a) > 0, "Polynomial degree must be at least 0"
        return [coeff * s for coeff in a]

    # @staticmethod
    # def bit_reverse(k, k_log_size):
    #     """
    #     Reverse the bits of k, assuming k is represented with k_log_size bits.

    #     Args:
    #         k (int): The number to bit-reverse.
    #         k_log_size (int): The number of bits used to represent k.

    #     Returns:
    #         int: The bit-reversed value of k.
    #     """
    #     return int(format(k, f'0{k_log_size}b')[::-1], 2)
    
    @classmethod
    def polynomial_multiplication(cls, a: list[Field], b: list[Field]) -> list[Field]:
        """
        Multiply two polynomials represented as lists of coefficients.
            NOTE: It's slow.
            TODO: Rewrite using Karatsuba algorithm
        Args:
            a (list): Coefficients of the first polynomial.
            b (list): Coefficients of the second polynomial.

        Returns:
            list: Coefficients of the product polynomial.
        """
        result = [cls.F.zero()] * (len(a) + len(b) - 1)
        for i in range(len(a)):
            for j in range(len(b)):
                result[i + j] += a[i] * b[j]
        return result
    
    @classmethod
    def polynomial_division_with_remainder(cls, dividend: list[Field], divisor: list[Field]) -> tuple[list[Field], list[Field]]:
        """
        Perform a polynomial long division.

        Args:
            dividend (list): Coefficients of the dividend polynomial.
            divisor (list): Coefficients of the divisor polynomial.

        Returns:
            tuple: (quotient, remainder), where quotient and remainder are lists of coefficients.

        Raises:
            ValueError: If the divisor is zero.
        """
        dividend = dividend.copy()
        divisor = divisor.copy()
        cls.remove_leading_zeros(dividend)
        cls.remove_leading_zeros(divisor)

        if not divisor or (len(divisor) == 1 and divisor[0] == cls.F.zero()):
            raise ValueError("Division by zero polynomial")

        if len(dividend) < len(divisor):
            return [cls.F.zero()], dividend

        quotient = [cls.F.zero()] * (len(dividend) - len(divisor) + 1)
        remainder = [dividend[i] for i in range(len(dividend))]

        for i in range(len(quotient) - 1, -1, -1):  # Equivalent to (0..quotient.len()).rev()
            quotient[i] = remainder[i + len(divisor) - 1] / divisor[-1]
            for j in range(len(divisor)):  # Equivalent to 0..divisor.len()
                remainder[i + j] -= quotient[i] * divisor[j]

        cls.remove_leading_zeros(remainder)

        return quotient, remainder

    @classmethod
    def polynomial_inverse(cls, coeffs: list[Field], d: int) -> list[Field]:
        """
        Compute the inverse of a polynomial modulo x^d.
        """
        k = log_2_ceiling(d)
        h = [coeffs[0].inv()]
        for i in range(1, k):
            h_sq = cls.polynomial_multiplication(h[:2**(i-1)], h[:2**(i-1)])
            f_h_sq = cls.polynomial_multiplication(h_sq, coeffs[:2**i])
            f_h_sq_mod_x_2_power_i = f_h_sq[:2**i]
            h = cls.polynomial_subtraction(cls.polynomial_scalar_multiplication(h, cls.F(2)), f_h_sq_mod_x_2_power_i)
        
        h_sq = cls.polynomial_multiplication(h, h)
        f_h_sq = cls.polynomial_multiplication(h_sq[:d+1], coeffs[:d+1])
        f_h_sq_mod_x_k = f_h_sq[:d+1]
        h = cls.polynomial_subtraction(cls.polynomial_scalar_multiplication(h[:d+1], cls.F(2)), f_h_sq_mod_x_k)
        return h

    @classmethod
    def polynomial_division_with_remainder_fast(cls, dividend: list[Field], divisor: list[Field]) -> tuple[list[Field], list[Field]]:
        
        f = dividend.copy()
        g = divisor.copy()

        cls.remove_leading_zeros(f)
        cls.remove_leading_zeros(g)

        f_deg = len(f) - 1
        g_deg = len(g) - 1

        if f_deg < g_deg:
            return [cls.F.zero()], f
        # degree of quotient
        d = f_deg - g_deg
        
        # reverse polynomial of the divisor
        # rev_g = g[::-1]
        g.reverse()
        rev_g_inv_prec_d_plus_1 = cls.polynomial_inverse(g, d+1)

        # reverse polynomial of the dividend
        f.reverse()
        
        # reverse polynomial of the quotient
        q = cls.polynomial_multiplication(f[:d+1], rev_g_inv_prec_d_plus_1)
        # truncate the quotient
        q = q[:d+1]
        # reverse the quotient
        q.reverse()

        r = cls.polynomial_subtraction(dividend, cls.polynomial_multiplication(q, divisor))
        cls.remove_leading_zeros(r)
        return q, r
    
    def div_by_linear_divisor(self, d: Field) -> tuple['UniPolynomial[Field]', Field]:
        """
        Divide a polynomial by a linear divisor (X - d) using Ruffini's rule.

        Args:
            d (Scalar): The constant term of the linear divisor.

        Returns:
            tuple: (quotient coefficients, remainder)
        """
        coeffs = self.coeffs
        assert len(coeffs) > 0, "Polynomial degree must be at least 0"

        n = len(coeffs)
        quotient = [self.F.zero()] * (n - 1)
        
        # Start with the highest degree coefficient
        current = coeffs[-1]
        
        # Iterate through coefficients from second-highest to lowest degree
        for i in range(n - 2, -1, -1):
            # Store the current value in the quotient
            quotient[i] = current
            
            # Compute the next value
            current = current * d + coeffs[i]
        
        # The final current value is the remainder
        remainder = current

        return type(self)(quotient), remainder

    def div_by_binomial(self, alpha: Field, d: int) -> tuple['UniPolynomial[Field]', 'UniPolynomial[Field]']:
        """
        Divide a polynomial by a binomial (X^d - alpha) in O(n) time.
        """
        coeffs = self.coeffs
        n = len(coeffs)
        coeffs += [self.F.zero()] * (n % d)
        num_col = d
        num_row = len(coeffs) // num_col

        q_coeffs = [self.F.zero()] * (num_col * (num_row-1))
        r_coeffs = [self.F.zero()] * num_col
        for j in range(num_col):
            fi = coeffs[j::num_row]
            qi, ri = UniPolynomial(fi).div_by_linear_divisor(alpha)
            for i in range(num_row-1):
                q_coeffs[j+i*num_row] = qi.coeffs[i]
            r_coeffs[j] = ri
        return UniPolynomial(q_coeffs), UniPolynomial(r_coeffs)
    
    @classmethod
    def construct_subproduct_tree_fix(cls, domain: list[Field]) -> dict:
        """
        Construct a subproduct tree for the given domain.

        Args:
            domain (list): A list of field elements representing the domain.

        Returns:
            dict: A dictionary representing the subproduct tree.
        """
        n = len(domain)
        if n == 1:
            return {"poly": [-domain[0], cls.F.one()], "children": None}

        mid = n // 2
        left = cls.construct_subproduct_tree_fix(domain[:mid])
        right = cls.construct_subproduct_tree_fix(domain[mid:])
        poly = cls.polynomial_multiplication(left["poly"], right["poly"])

        return {"poly": poly, "children": (left, right)}
    
    @classmethod
    def compute_eval_fix(cls, tree: dict, f: list[Field], domain: list[Field]) -> list[Field]:
        """
        Compute the evaluation of polynomial f at points in domain using the subproduct tree.

        Args:
            tree (dict): The subproduct tree.
            f (list): Coefficients of the polynomial to evaluate.
            domain (list): Points at which to evaluate the polynomial.

        Returns:
            list: Evaluations of f at points in domain.
        """
        n = len(domain)
        if n == 1:
            return [cls.evaluate_at_point(f, domain[0])]

        left_tree, right_tree = tree["children"]

        _, r0 = cls.polynomial_division_with_remainder_fast(f, left_tree["poly"])
        _, r1 = cls.polynomial_division_with_remainder_fast(f, right_tree["poly"])

        mid = n // 2

        left_evals = cls.compute_eval_fix(left_tree, r0, domain[:mid])
        right_evals = cls.compute_eval_fix(right_tree, r1, domain[mid:])

        return left_evals + right_evals

    @classmethod
    def compute_linear_combination_linear_moduli_fix(cls, tree: dict, ws: list[F], domain: list[F]) -> list[F]:
        """
        Compute the linear combination of linear moduli using the subproduct tree.

        Args:
            tree (dict): The subproduct tree.
            ws (list): Weights for the linear combination.
            domain (list): The domain points.

        Returns:
            list: Coefficients of the resulting polynomial.
        """
        n = len(domain)
        if n == 1:
            return [ws[0]]

        left_tree, right_tree = tree["children"]

        mid = n // 2
        left_ws = ws[:mid]
        right_ws = ws[mid:]

        left_poly = cls.compute_linear_combination_linear_moduli_fix(left_tree, left_ws, domain[:mid])
        right_poly = cls.compute_linear_combination_linear_moduli_fix(right_tree, right_ws, domain[mid:])

        left_result = cls.polynomial_multiplication(left_poly, right_tree["poly"])
        right_result = cls.polynomial_multiplication(right_poly, left_tree["poly"])

        result = cls.polynomial_addition(left_result, right_result)

        return result
    
    @classmethod
    def evaluate_at_point(cls, poly: list[Field], point: Field) -> Field:
        """Evaluate a polynomial at a single point using Horner's method."""
        result = cls.F.zero()
        for coeff in reversed(poly):
            result = result * point + coeff
        return result

    def evaluate(self, point: Field) -> Field:
        return self.evaluate_at_point(self.coeffs, point)
    
    @classmethod
    def vanishing_polynomial(cls, domain):
        """
        Compute the vanishing polynomial for the given domain.

        Args:
            domain (list): A list of field elements.

        Returns:
            UniPolynomial: The vanishing polynomial.
        """
        tree = cls.construct_subproduct_tree_fix(domain)
        return cls(tree["poly"])

    @classmethod
    def compute_coeffs_from_evals_fast(cls, evals, domain):
        """
        Compute polynomial coefficients from evaluations over irregular domain.

        Args:
            evals (list): Evaluations of the polynomial.
            domain (list): Domain points where the polynomial was evaluated.

        Returns:
            list: Coefficients of the interpolated polynomial.
        """
        n = len(domain)
        assert len(evals) == n, "Number of evaluations must match domain size"

        # evals = [e for e in evals]
        # domain = [d for d in domain]

        # 1. Build up the subproduct tree
        tree = cls.construct_subproduct_tree_fix(domain)
        
        # 2. Compute z'(X) in O(n) time
        z_derivative = cls.compute_z_derivative(tree["poly"])

        # 3. Compute barycentric weights
        z_derivative_at_u = cls.compute_eval_fix(tree, z_derivative, domain)
        ws = [1 / zd for zd in z_derivative_at_u]
        ws = [w * e for w, e in zip(ws, evals)]
        
        # 4. Compute barycentric interpolation
        f = cls.compute_linear_combination_linear_moduli_fix(tree, ws, domain)

        return f

    @classmethod
    def compute_evals_from_coeffs_fast(cls, coeffs, domain):
        """
        Compute evaluations from coefficients in O(n log^2 n) time over irregular domain.

        Args:
            coeffs (list): Coefficients of the polynomial.
            domain (list): Domain points where to evaluate the polynomial.

        Returns:
            list: Evaluations of the polynomial over the domain.
        """
        n = len(domain)

        assert n == len(coeffs), "Domain size must match the number of coefficients"
        assert (n & (n - 1) == 0), "Domain size must be a power of 2"

        # coeffs = [Fp(c) for c in coeffs]
        # domain = [Fp(d) for d in domain]

        # 1. Building up subproduct tree
        tree = cls.construct_subproduct_tree_fix(domain)

        # 2. Compute evaluations from subproduct tree
        evals = cls.compute_eval_fix(tree, coeffs, domain)

        return evals

    @staticmethod
    def compute_z_derivative(z):
        """Compute the derivative of the polynomial z."""
        return [i * z[i] for i in range(1, len(z))]
    
    @classmethod
    def interpolate(cls, evals, domain):
        """
        Interpolate a polynomial from its evaluations.

        Args:
            evals (list): Evaluations of the polynomial.
            domain (list): Domain points where the polynomial was evaluated.

        Returns:
        """
        coeffs = cls.compute_coeffs_from_evals_fast(evals, domain)
        return cls(coeffs)
    
    @classmethod
    def interpolate_and_compute_vanishing_polynomial(cls, evals, domain):
        """
        Interpolate a polynomial from its evaluations.

        Args:
            evals (list): Evaluations of the polynomial.
            domain (list): Domain points where the polynomial was evaluated.

        Returns:
        """
        n = len(domain)
        assert len(evals) == n, "Number of evaluations must match domain size"

        # evals = [e for e in evals]
        # domain = [d for d in domain]

        # 1. Building up subproduct tree
        tree = cls.construct_subproduct_tree_fix(domain)
        z_poly = tree["poly"]

        # 2. Construct z'(X) in O(n) time
        z_derivative = cls.compute_z_derivative(z_poly)

        # 3. Compute barycentric weights
        z_derivative_at_u = cls.compute_eval_fix(tree, z_derivative, domain)
        ws = [1 / zd for zd in z_derivative_at_u]
        ws = [w * e for w, e in zip(ws, evals)]

        # 4. Compute barycentric interpolation
        coeffs = cls.compute_linear_combination_linear_moduli_fix(tree, ws, domain)

        return cls(coeffs), cls(z_poly)

    @classmethod
    def from_evals(cls, evals, domain):
        """
        Construct a polynomial from its evaluations.
        """
        return cls.interpolate(evals, domain)

    # Compute Barycentric interpolation with O(n^2) time complexity
    @classmethod
    def barycentric_weights(cls, D: list[Field]) -> list[Field]:
        """
        Compute the barycentric weights for the given domain.
        """
        n = len(D)
        weights = [cls.F.one()] * n
        for i in range(n):
            # weights[i] = product([(D[i] - D[j]) if i !=j else Fp(1) for j in range(n)])
            for j in range(n):
                if i==j:
                    # weights[i] *= 1
                    continue
                weights[i] *= (D[i] - D[j])
            weights[i] = 1/weights[i]
        return weights
    
    @classmethod
    def barycentric_weights_fast(cls, D: list[Field]) -> list[Field]:
        """
        Compute the barycentric weights for the given domain using the subproduct tree.

        Args:
            evals (list): Evaluations of the polynomial.
            domain (list): Domain points where the polynomial was evaluated.

        Returns:
        """
        tree = cls.construct_subproduct_tree_fix(D)
        z_poly = tree["poly"]
        z_derivative = cls.compute_z_derivative(z_poly)
        z_derivative_at_u = cls.compute_eval_fix(tree, z_derivative, D)
        ws = [1 / zd for zd in z_derivative_at_u]
        return ws


    @classmethod
    def lagrange_polynomial(cls, i: int, domain: list[Field]) -> 'UniPolynomial':
        barycentric_weights = cls.barycentric_weights(domain)
        zH_poly = cls.vanishing_polynomial(domain)
        l_poly = cls.const(barycentric_weights[i]) * zH_poly // cls([-domain[i], cls.F.one()])
        return l_poly

    @classmethod
    # def uni_eval_from_evals(cls, evals, z, D):
    def evaluate_from_evals(cls, evals, z, D):
        n = len(evals)
        if n != len(D):
            raise ValueError("Domain size should be equal to the length of evaluations")
        if z in D:
            return evals[D.index(z)]
        weights = cls.barycentric_weights(D)
        # print("weights={}".format(weights))
        e_vec = [weights[i] / (z - D[i]) for i in range(n)]
        numerator = sum([e_vec[i] * evals[i] for i in range(n)])
        denominator = sum([e_vec[i] for i in range(n)])
        return (numerator / denominator)
    
    def shift(self, shift_value):
        coeffs = []
        shift_value_power = self.F.one()
        for i in range(len(self.coeffs)):
            coeffs.append(self.coeffs[i] * shift_value_power)
            shift_value_power *= shift_value
        return UniPolynomial(coeffs)
    
    @classmethod
    def const(cls, constant: Field) -> 'UniPolynomial':
        if isinstance(constant, cls.F):
            return UniPolynomial([constant])
        else:
            raise ValueError("Constant must be a field element")


class UniPolynomialWithFft(UniPolynomial):
    """
    Univariate polynomial with coefficients in a prime field F, where a large 
    domain (multiplicative subgroup) size is required for FFT, and the order of 
    the subgroup is a power of 2.
    """

    @classmethod
    def set_field_type(cls, field_type: type):
        UniPolynomial.set_field_type(field_type)
        cls.F = field_type
        one = field_type.one()
        zero = field_type.zero()
        cls.TWO_ADICITY = field_type.TWO_ADICITY
        cls.MULTIPLICATIVE_GENERATOR = field_type.MULTIPLICATIVE_GENERATOR
        cls.ROOT_OF_UNITY = field_type.ROOT_OF_UNITY
        return
    
    def __init__(self, coeffs: list[Field]):
        super().__init__(coeffs)
        # self.TWO_ADICITY = TWO_ADICITY
        # self.MULTIPLICATIVE_GENERATOR = MULTIPLICATIVE_GENERATOR
        # self.ROOT_OF_UNITY = ROOT_OF_UNITY
        return 
    
    @classmethod
    def fft_core(cls, coeffs: list[Field], omega: Field, k_log_size: int) -> list[Field]:
        """
        Perform Algebraic FFT on the given coefficients using a 2^k-th root of unity.

        Args:
            coeffs (list): Coefficients of the polynomial, which must be padded to 
                a power of 2 before calling this function.
            omega (Field): A valid 2^k-th root of unity.
            k_log_size (int): logarithm of the size of the domain.

        Returns:
            list: Coefficients after Algebraic FFT.
        """
        domain_size = 2 ** k_log_size
        assert len(coeffs) == domain_size, "Coefficients length must be a power of 2"

        # Bit-reversing
        for k in range(domain_size):
            k_rev = bit_reverse(k, k_log_size)
            if k < k_rev:
                coeffs[k], coeffs[k_rev] = coeffs[k_rev], coeffs[k]

        sep = 1
        for _ in range(k_log_size):
            w = cls.F.one()
            for j in range(sep):
                for i in range(0, domain_size, 2*sep):
                    l, r = i + j, i + j + sep
                    tmp = coeffs[r] * w
                    coeffs[r] = coeffs[l] - tmp
                    coeffs[l] = coeffs[l] + tmp
                w = w * (omega**(domain_size // (2*sep)))
            sep *= 2

        return coeffs
    
    @classmethod
    def fft_core_with_coset(cls, coeffs, coset_factor, k_log_size, omega=None):
        """
        Perform Algebraic FFT on the given coefficients over a coset
            using a 2^k-th root of unity.

        Args:
            coeffs (list): Coefficients of the polynomial.
            coset_factor (Field): The coset factor.
            k_log_size (int): The logarithm of the size of the domain.
            omega (Field): The root of unity.

        Returns:
            list: Coefficients after Algebraic FFT.
        """
        domain_size = 2 ** k_log_size
        assert len(coeffs) == domain_size, "Coefficients length must be a power of 2"

        if omega is None:
            omega = cls.F.nth_root_of_unity(domain_size)
        else:
            assert (omega ** domain_size) == cls.F.one(), "omega must be a 2^k-th root of unity"
            assert (omega ** (domain_size // 2)) == cls.F.neg_one(), "omega must be a 2^k-th root of unity"
        
        # Bit-reversing
        for k in range(domain_size):
            k_rev = bit_reverse(k, k_log_size)
            if k < k_rev:
                coeffs[k], coeffs[k_rev] = coeffs[k_rev], coeffs[k]

        sep = 1
        
        for i in range(k_log_size):
            g = coset_factor**(2**(k_log_size - 1 - i))
            w = cls.F.one()
            for j in range(sep):
                for i in range(0, domain_size, 2*sep):
                    l, r = i + j, i + j + sep
                    tmp = coeffs[r] * w * g
                    coeffs[r] = coeffs[l] - tmp
                    coeffs[l] = coeffs[l] + tmp
                w = w * (omega**(domain_size // (2*sep)))
            sep *= 2
        return coeffs   

    @classmethod
    def fft_coset_rbo(cls, coeffs: list[Field], coset_factor: Field, k_log_size: int, omega=None):
        """
        Compute evaluations of the polynomial over a coset.

        Args:
            coeffs (list): Coefficients of the polynomial.
            coset_factor (Field): The coset factor.
            k_log_size (int): The logarithm of the size of the domain.
            omega (Field): The root of unity.

        Returns:
            list: (Reversed Bit-Order) Evaluations of the polynomial over the coset.
        """
        domain_size = 2**k_log_size
        assert len(coeffs) <= domain_size, "Coefficients length must be less than or equal to the domain size"
        
        if omega is None:
            omega = cls.F.nth_root_of_unity(domain_size)
        else:
            assert (omega ** domain_size) == cls.F.one(), "omega must be a 2^k-th root of unity"
            assert (omega ** (domain_size // 2)) == cls.F.neg_one(), "omega must be a 2^k-th root of unity"

        coeffs_copy = coeffs + [cls.F.zero()] * (domain_size - len(coeffs))
        evals = cls.fft_core_with_coset(coeffs_copy, coset_factor, k_log_size, omega)
        return bit_reverse_permutation(evals)
    
    @classmethod
    def fft_coset(cls, coeffs: list[Field], coset_factor: Field, k_log_size: int, omega=None):
        """
        Compute evaluations of the polynomial over a coset.

        Args:
            coeffs (list): Coefficients of the polynomial.
            coset_factor (Field): The coset factor.
            k_log_size (int): The logarithm of the size of the domain.
            omega (Field): The root of unity.

        Returns:
            list: (Reversed Bit-Order) Evaluations of the polynomial over the coset.
        """
        domain_size = 2**k_log_size
        assert len(coeffs) <= domain_size, "Coefficients length must be less than or equal to the domain size"
        
        if omega is None:
            omega = cls.F.nth_root_of_unity(domain_size)
        else:
            assert (omega ** domain_size) == cls.F.one(), "omega must be a 2^k-th root of unity"
            assert (omega ** (domain_size // 2)) == cls.F.neg_one(), "omega must be a 2^k-th root of unity"

        coeffs_copy = coeffs + [cls.F.zero()] * (domain_size - len(coeffs))
        evals = cls.fft_core_with_coset(coeffs_copy, coset_factor, k_log_size, omega)
        return evals
    
    @classmethod
    def ifft_coset(cls, evals: list[Field], coset_factor: Field, k_log_size: int, omega=None):
        """
        Perform Algebraic Inverse FFT on the given coefficients over a coset
            using a 2^k-th root of unity.

        Args:
            evals (list): Evaluations of the polynomial over the coset `gH`.
            coset_factor (Field): A coset factor, `g` not in `H`.
            k_log_size (int): The logarithm of the size of the domain.
            omega (Field): The root of unity.

        Returns:
            list: Coefficients after Algebraic Inverse FFT.
        """
        domain_size = 2**k_log_size
        if omega is None:
            omega = cls.F.nth_root_of_unity(domain_size)
        else:
            assert (omega ** domain_size) == cls.F.one(), "omega must be a 2^k-th root of unity"
            assert (omega ** (domain_size // 2)) == cls.F.neg_one(), "omega must be a 2^k-th root of unity"
        
        n = cls.F(domain_size)
        n_inv = n.inv()

        omega_inv = omega.inv()
        coeffs = cls.fft_coset(evals, cls.F.one(), k_log_size, omega=omega_inv)
        coset_factor_inv = coset_factor.inv()

        factors = [coset_factor_inv**i for i in range(domain_size)]
        return [c * f * n_inv for c, f in zip(coeffs, factors)]

    # @classmethod    
    # def fft_with_twiddles(cls, coeffs, k_log_size, twiddles):

    #     n = len(coeffs)
    #     assert (n & (n - 1) == 0), "Domain size must be a power of 2"

    #     coeffs = [c for c in coeffs]
    #     omega = cls.get_root_of_unity(k_log_size)
    #     return cls.ntt_core(coeffs.copy(), omega, k_log_size)

    @classmethod
    def ifft(cls, evals: list[Field], k_log_size: int, omega: Field) -> list[Field]:
        n = len(evals)
        assert is_power_of_two(n), "Domain size must be a power of 2"
        assert k_log_size == log_2(n), "Domain size must match the logarithm of the number of evaluations"

        omega_inv = omega.inv()
        domain_size = type(omega)(2 ** k_log_size)
        domain_size_inv = domain_size.inv()
        
        coeffs = cls.fft_core(evals.copy(), omega_inv, k_log_size)
        return [c * domain_size_inv for c in coeffs]
    
    @classmethod
    def fft(cls, coeffs, k_log_size, omega):
        n = len(coeffs)
        field_type = type(omega)
        coeffs_copy = coeffs + [field_type.zero()] * (2 ** k_log_size - n)
        evals = cls.fft_core(coeffs_copy, omega, k_log_size)
        return evals

    @classmethod
    def polynomial_multiplication(cls, a: list[Field], b: list[Field]) -> list[Field]:
        
        # assume no leading zeros
        print("DEBUG: polynomial_multiplication via FFT")
        # compute the domain size
        domain_size = next_power_of_two(len(a) + len(b))
        # if debug: print(f"domain_size={domain_size}")
        # compute the log size of the domain
        domain_log_size = log_2(domain_size)
        # if debug: print(f"domain_log_size={domain_log_size}")
        # compute the nth root of unity
        omega = cls.F.nth_root_of_unity(domain_size)
        # if debug: print(f"omega={omega}"

        # extend the polynomials to the domain size
        a = a + [cls.F.zero()] * (domain_size - len(a))
        b = b + [cls.F.zero()] * (domain_size - len(b))

        # compute the evaluations of the polynomials over the domain
        a_evals_H = cls.fft(a, domain_log_size, omega)
        b_evals_H = cls.fft(b, domain_log_size, omega)

        # compute the evaluations of the product polynomial over the domain
        ab_evals_H = [a_evals_H[i] * b_evals_H[i] for i in range(domain_size)]

        # compute the coefficients of the product polynomial
        ab_coeffs = cls.ifft(ab_evals_H, domain_log_size, omega)
        cls.remove_leading_zeros(ab_coeffs)
        return ab_coeffs

    # Overrided method in UniPolynomial using FFT
    @classmethod
    def vanishing_polynomial(cls, domain_size: int):
        """
        Compute the vanishing polynomial for a given domain size.
        """
        assert is_power_of_two(domain_size), "Domain size must be a power of 2"

        coeffs = [cls.F.zero()] * (domain_size + 1)
        coeffs[0] = -cls.F.one()
        coeffs[-1] = cls.F.one()
        return cls(coeffs)
    
    # Overrided method in UniPolynomial using FFT
    @classmethod
    def lagrange_polynomial(cls, i, domain_size) -> 'UniPolynomial':
        n = domain_size
        domain = [cls.F.nth_root_of_unity(n)**i for i in range(n)]
        barycentric_weights = cls.compute_barycentric_weights(domain_size)
        zH_poly = cls.vanishing_polynomial(domain_size)
        l_poly = cls.const(barycentric_weights[i]) * zH_poly // UniPolynomial([-domain[i], Fr.one()])
        return l_poly

    @classmethod
    def compute_barycentric_weights(cls, domain_size: int):
        """
        Compute barycentric weights for an FFT domain.

            domain: 
                H = (1, omega, omega^2, ..., omega^(n-1))

            vanishing_polynomial: 
                zH(X) = X^n - 1

            derivative of vanishing_polynomial: 
                zH'(X) = nX^(n-1)

            barycentric weights: w[n]
                w_i = 1 / zH'(omega_i) 
                    = 1 / n*omega_i^{n-1} 
                    = (omega_i)/n

        Args:
            domain_size (int): The size of the domain.

        Returns:
            list: Barycentric weights.
        """
        n = domain_size
        omega = cls.F.nth_root_of_unity(domain_size)
        n_inv = cls.F(n).inv()
        
        x = n_inv
        weights = []
        for i in range(n):
            weights.append(x)
            x *= omega
        return weights
    
    def compute_evaluations(self, domain_size:int):
        assert is_power_of_two(domain_size), "Domain size must be a power of 2"
        k = log_2(domain_size)
        omega = self.F.nth_root_of_unity(domain_size)
        return self.fft(self.coeffs, k, omega)

    @classmethod
    def interpolate(cls, evals: list[Field], domain_size:int):
        """
        Interpolate a polynomial from its evaluations using FFT.

        Args:
            evals (list): Evaluations of the polynomial.
            omega: The omega root of unity.

        Returns:
        """
        assert is_power_of_two(domain_size), "Domain size must be a power of 2"
        domain_size = len(evals)
        assert len(evals) == domain_size, "Length of evaluations must match the domain size"
        
        if domain_size == 1:
            return cls([evals[0]])

        omega = cls.F.nth_root_of_unity(domain_size)

        domain_log_size = log_2(domain_size)

        coeffs = cls.ifft(evals, domain_log_size, omega)

        return cls(coeffs)
    
    @classmethod
    def precompute_twiddles_for_fft(cls, domain_size: int, is_inversed: bool = False, is_bit_reversed: bool = False):
        assert is_power_of_two(domain_size), "Domain size must be a power of 2"

        twiddles = []
        omega = cls.F.nth_root_of_unity(domain_size)
        omega_power = cls.F.one()
        for i in range(domain_size//2):
            if is_inversed:
                twiddles.insert(1, omega_power)
            else:
                twiddles.append(omega_power)
            omega_power *= omega

        if is_bit_reversed:
            twiddles = bit_reverse_permutation(twiddles)
        return twiddles

def reverse_bits(n: int, bit_length: int) -> int:
    """
    Reverse the bits of an integer.

    Args:
        n (int): The input integer.
        bit_length (int): The number of bits to consider.

    Returns:
        int: The integer with its bits reversed.
    """
    result = 0
    for i in range(bit_length):
        result = (result << 1) | (n & 1)
        n >>= 1
    return result

def bit_reverse_permutation_inplace(elements: list[Field]):
    assert is_power_of_two(len(elements)), "Length of elements must be a power of 2"

    bit_length = log_2(len(elements))
    n = len(elements)
    for i in range(n):
        j = reverse_bits(i, bit_length)
        if i < j:
            elements[i], elements[j] = elements[j], elements[i]
    return

def bit_reverse_permutation(elements: list[Field]):
    assert is_power_of_two(len(elements)), "Length of elements must be a power of 2"
    
    bit_length = log_2(len(elements))
    n = len(elements)
    vec = elements.copy()
    for i in range(n):
        j = reverse_bits(i, bit_length)
        if i < j:
            vec[i], vec[j] = vec[j], vec[i]
    return vec

def test_fft_coset():
    coeffs = [Fr(2), Fr(3), Fr(4), Fr(2)]
    evals1 = UniPolynomialWithFft.fft_coset(coeffs, Fr.one(), 2)
    evals2 = UniPolynomialWithFft.fft(coeffs, 2, Fr.nth_root_of_unity(4))
    evals3 = UniPolynomialWithFft.fft_coset_rbo(coeffs, Fr.one(), 2)

    print(f"evals1: {evals1}")
    print(f"evals2: {evals2}")
    print(f"evals3: {evals3}")
    assert evals1 == evals2
    assert bit_reverse_permutation(evals1) == evals3

    evals = UniPolynomialWithFft.fft_coset(coeffs, Fr.multiplicative_generator(), 2)
    coeffs2 = UniPolynomialWithFft.ifft_coset(evals, Fr.multiplicative_generator(), 2)
    print(f"coeffs2: {coeffs2}")
    assert coeffs == coeffs2  

# Example usage
if __name__ == "__main__":

    a = UniPolynomial([Fr(2), Fr(3), Fr(4), Fr(2)])
    b = UniPolynomial([Fr(3), Fr(1), Fr(2), Fr(9)])
    omega = Fr.nth_root_of_unity(4)
    c = a * b 
    print(f"c: {c}")
    z = UniPolynomial([Fr(1), Fr(0), Fr(0), Fr(0), Fr(1)])
    q, r = divmod(c, z)
    print(f"q: {q}")
    print(f"r: {r}")
    assert q * z + r == c

    a = UniPolynomial([Fr(0)])
    assert a.is_zero()
    # f(X) = X^3 + 3X^2 + 2X + 5
    # f = UniPolynomial([Fr(5), Fr(2), Fr(3), Fr(1)])
    # print(f"type of f is {type(f)}")
    # x = UniPolynomial([Fr(0), Fr(1)])  # Represents X
    # d = Fr(1)  # Dividing by (X - 1)

    # q, r = f.division_by_linear_divisor(d)
    # print(f"f(X) = {f}")
    # print(f"Dividing by (X - {d})")
    # print(f"Quotient: {q}")
    # print(f"Remainder: {r}")

    # # Verify the result
    # # f(X) should equal q(X) * (X - d) + r
    # linear_divisor = x - UniPolynomial([d])
    # result = q * linear_divisor + UniPolynomial([r])
    # print(f"Verification: {result}")
    # print(f"Original polynomial: {f}")
    # print(f"Equal: {result.coeffs == f.coeffs}")

    # assert f.field_type == Fr, f"field_type: {f.field_type}, type(Fr): {type(Fr)}"

    test_fft_coset()