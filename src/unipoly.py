#!/usr/bin/env python3

from typing import TypeVar, Generic
from utils import log_2, is_power_of_two
from curve import Fp, Fr

F = TypeVar('F', bound=Fr)

class Domain_FFT_2Radix(Generic[F]):
    size: int
    points: list[F]
    field_type: type[F]

    def __init__(self, size: int, omega: F, field_type: type[F]):
        self.size = size
        assert is_power_of_two(size)
        
        self.points = []
        omega = field_type.nth_root_of_unity(size)
        a = field_type.one()
        for i in range(size):
            self.points.append(a)
            a = a * omega
        return

class UniPolynomial(Generic[F]):
    """
    A univariate polynomial with coefficients in a field F.
    """
    # coeffs: list[F]
    # degree: int
    # field_type: type[F]

    def __init__(self, coeffs: list[F]):
        """
        Initialize a UniPolynomial instance.

        Args:
            coeffs (list): Coefficients of the polynomial.
        """

        c_list = coeffs.copy()
        field_type = type(c_list[0])

        # Remove leading zeros
        while len(c_list) > 1 and c_list[-1] == field_type(0):
            c_list.pop()

        if len(c_list) == 0:
            self.coeffs = [field_type.zero()]
            self.degree = None
            self.field_type = field_type
            return
        
        self.coeffs = c_list
        self.degree = len(c_list) - 1
        self.field_type = field_type
        return

    def is_zero(self):
        if len(self.coeffs) == 0 and self.degree == 0:
            return True
        if self.degree == 0 and len(self.coeffs) == 1 and self.coeffs[0] == 0:
            return True
        return False

    def __neg__(self):
        """
        Negate the polynomial.

        Returns:
            UniPolynomial: A new polynomial with all coefficients negated.
        """
        return UniPolynomial([-coeff for coeff in self.coeffs])
    
    @classmethod
    def add(cls, poly1: 'UniPolynomial[F]', poly2: 'UniPolynomial[F]') -> 'UniPolynomial[F]':
        """
        Add two UniPolynomial instances.

        Args:
            poly1 (UniPolynomial): First polynomial.
            poly2 (UniPolynomial): Second polynomial.

        Returns:
            UniPolynomial: Sum of the two polynomials.
        """
        result_coeffs = cls.polynomial_addition(poly1.coeffs, poly2.coeffs)
        return cls(result_coeffs)
    
    def __add__(self, other: 'UniPolynomial[F]'):
        if isinstance(other, (int, float)):
            # If adding with a number, treat it as a constant polynomial
            return UniPolynomial([self.coeffs[0] + other] + self.coeffs[1:])
        elif isinstance(other, UniPolynomial):
            # Existing code for adding two polynomials
            max_degree = max(len(self.coeffs), len(other.coeffs))
            new_coeffs = [0] * max_degree
            for i in range(max_degree):
                if i < len(self.coeffs):
                    new_coeffs[i] += self.coeffs[i]
                if i < len(other.coeffs):
                    new_coeffs[i] += other.coeffs[i]
            return UniPolynomial(new_coeffs)
        else:
            raise TypeError(f"Unsupported operand type for +: '{type(self).__name__}' and '{type(other).__name__}'")
    
    @classmethod
    def subtract(cls, poly1: 'UniPolynomial[F]', poly2: 'UniPolynomial[F]') -> 'UniPolynomial[F]':
        """
        Subtract two UniPolynomial instances.

        Args:
            poly1 (UniPolynomial): First polynomial.
            poly2 (UniPolynomial): Second polynomial to subtract from the first.

        Returns:
            UniPolynomial: Difference of the two polynomials.
        """
        max_degree = max(poly1.degree, poly2.degree)
        result_coeffs = [0] * (max_degree + 1)

        for i in range(max_degree + 1):
            coeff1 = poly1.coeffs[i] if i <= poly1.degree else 0
            coeff2 = poly2.coeffs[i] if i <= poly2.degree else 0
            result_coeffs[i] = coeff1 - coeff2

        # Remove leading zeros
        while len(result_coeffs) > 1 and result_coeffs[-1] == 0:
            result_coeffs.pop()

        return cls(result_coeffs)

    def __sub__(self, other):
        """
        Overload the - operator for UniPolynomial instances.

        Args:
            other (UniPolynomial): The polynomial to subtract from this one.

        Returns:
            UniPolynomial: Difference of the two polynomials.
        """
        if isinstance(other, UniPolynomial):
            return self.subtract(self, other)
        else:
            raise TypeError("Unsupported operand type for -: '{}' and '{}'".format(type(self).__name__, type(other).__name__))
   
    
    @classmethod
    def mul(cls, poly1, poly2):
        """
        Multiply two UniPolynomial instances.

        Args:
            poly1 (UniPolynomial): First polynomial.
            poly2 (UniPolynomial): Second polynomial.

        Returns:
            UniPolynomial: Product of the two polynomials.
        """
        result_coeffs = cls.polynomial_multiplication(poly1.coeffs, poly2.coeffs)
        return cls(result_coeffs)

    def __mul__(self, other):
        """
        Overload the * operator for UniPolynomial instances.

        Args:
            other (UniPolynomial or scalar): The polynomial or scalar to multiply with this one.

        Returns:
            UniPolynomial: Product of the two polynomials or scalar multiplication result.
        """
        if isinstance(other, UniPolynomial):
            return self.mul(self, other)
        elif isinstance(other, (int, float)):  # Scalar multiplication
            return UniPolynomial([coeff * other for coeff in self.coeffs])
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
        if isinstance(other, (int, float)):
            return UniPolynomial([coeff * other for coeff in self.coeffs])
        else:
            raise TypeError("Unsupported operand type for *: '{}' and '{}'".format(type(other).__name__, type(self).__name__))


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
        q, r = cls.polynomial_division_with_remainder(dividend.coeffs, divisor.coeffs)
        return cls(q), cls(r)

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
        return self.coeffs == other.coeffs
    
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
    
    @staticmethod
    def polynomial_addition(a, b):
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
        a_padded = a + [0] * (max_len - len(a))
        b_padded = b + [0] * (max_len - len(b))
        
        # Add the coefficients
        result = [a_padded[i] + b_padded[i] for i in range(max_len)]
        
        # Remove leading zeros
        while len(result) > 1 and result[-1] == 0:
            result.pop()
        
        return result

    @staticmethod
    def bit_reverse(k, k_log_size):
        """
        Reverse the bits of k, assuming k is represented with k_log_size bits.

        Args:
            k (int): The number to bit-reverse.
            k_log_size (int): The number of bits used to represent k.

        Returns:
            int: The bit-reversed value of k.
        """
        return int(format(k, f'0{k_log_size}b')[::-1], 2)
    
    @classmethod
    def ntt_core(cls, coeffs, omega, k_log_size):
        """
        Perform NTT on the given coefficients using the specified root of unity.

        Args:
            coeffs (list): Coefficients of the polynomial.
            omega (Field): The root of unity.
            k_log_size (int): The logarithm of the size of the domain.

        Returns:
            list: Coefficients after NTT.
        """
        domain_size = 2 ** k_log_size
        assert len(coeffs) == domain_size, "Coefficients length must be a power of 2"

        # Bit-reversing
        for k in range(domain_size):
            k_rev = cls.bit_reverse(k, k_log_size)
            if k < k_rev:
                coeffs[k], coeffs[k_rev] = coeffs[k_rev], coeffs[k]

        sep = 1
        for _ in range(k_log_size):
            w = Fr.one()
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
    def ntt_core_coset(cls, coeffs, omega, coset_factor, k_log_size):
        """
        Perform NTT on the given coefficients using the specified root of unity.

        Args:
            coeffs (list): Coefficients of the polynomial.
            omega (Field): The root of unity.
            k_log_size (int): The logarithm of the size of the domain.

        Returns:
            list: Coefficients after NTT.
        """
        domain_size = 2 ** k_log_size
        assert len(coeffs) == domain_size, "Coefficients length must be a power of 2"

        # Bit-reversing
        for k in range(domain_size):
            k_rev = cls.bit_reverse(k, k_log_size)
            if k < k_rev:
                coeffs[k], coeffs[k_rev] = coeffs[k_rev], coeffs[k]

        sep = 1
        g = coset_factor
        for _ in range(k_log_size):
            w = 1
            for j in range(sep):
                for i in range(0, domain_size, 2*sep):
                    l, r = i + j, i + j + sep
                    tmp = g * coeffs[r] * w
                    coeffs[r] = coeffs[l] - tmp
                    coeffs[l] = coeffs[l] + tmp
                w = w * (omega**(domain_size // (2*sep)))
            sep *= 2
            g = g * g
        return coeffs   
    
    @classmethod    
    def fft_with_twiddles(cls, coeffs, k_log_size, twiddles):

        n = len(coeffs)
        assert (n & (n - 1) == 0), "Domain size must be a power of 2"

        coeffs = [c for c in coeffs]
        omega = cls.get_root_of_unity(k_log_size)
        return cls.ntt_core(coeffs.copy(), omega, k_log_size)

    @classmethod
    def ntt_coeffs_from_evals(cls, evals, k_log_size, omega):
        n = len(evals)
        assert (n & (n - 1) == 0), "Domain size must be a power of 2"
        assert k_log_size == log_2(n), "Domain size must match the logarithm of the number of evaluations"

        omega_inv = omega.inv()
        domain_size = type(omega)(2 ** k_log_size)
        domain_size_inv = type(omega).one() / domain_size
        
        coeffs = cls.ntt_core(evals.copy(), omega_inv, k_log_size)
        return [c * domain_size_inv for c in coeffs]
    
    @classmethod
    def ntt_evals_from_coeffs(cls, coeffs, k_log_size, omega):
        n = len(coeffs)
        field_type = type(omega)
        coeffs_copy = coeffs + [field_type.zero()] * (2 ** k_log_size - n)
        evals = cls.ntt_core(coeffs_copy, omega, k_log_size)
        return evals
    
    @staticmethod
    def polynomial_multiplication(a, b):
        """
        Multiply two polynomials represented as lists of coefficients.
        (It's slow)
            - TODO: use FFT to speed up

        Args:
            a (list): Coefficients of the first polynomial.
            b (list): Coefficients of the second polynomial.

        Returns:
            list: Coefficients of the product polynomial.
        """
        result = [0] * (len(a) + len(b) - 1)
        for i in range(len(a)):
            for j in range(len(b)):
                result[i + j] += a[i] * b[j]
        return result
    
    @staticmethod
    def polynomial_division_with_remainder(dividend, divisor):
        """
        Perform polynomial long division.

        Args:
            dividend (list): Coefficients of the dividend polynomial.
            divisor (list): Coefficients of the divisor polynomial.

        Returns:
            tuple: (quotient, remainder), where quotient and remainder are lists of coefficients.

        Raises:
            ValueError: If the divisor is zero.
        """
        dividend = [c for c in dividend]
        divisor = [c for c in divisor]
        if not divisor or (len(divisor) == 1 and divisor[0] == Fr.zero()):
            raise ValueError("Division by zero polynomial")

        # Remove leading zeros
        while dividend and dividend[-1] == 0:
            dividend.pop()
        while divisor and divisor[-1] == 0:
            divisor.pop()

        if len(dividend) < len(divisor):
            return [], dividend

        quotient = [0] * (len(dividend) - len(divisor) + 1)
        remainder = [dividend[i] for i in range(len(dividend))]

        for i in range(len(quotient) - 1, -1, -1):  # Equivalent to (0..quotient.len()).rev()
            quotient[i] = remainder[i + len(divisor) - 1] / divisor[-1]
            for j in range(len(divisor)):  # Equivalent to 0..divisor.len()
                remainder[i + j] -= quotient[i] * divisor[j]

        # Remove leading zeros
        while remainder and remainder[-1] == 0:
            remainder.pop()

        return quotient, remainder


    def division_by_linear_divisor(self, d):
        """
        Divide a polynomial by a linear divisor (X - d) using Ruffini's rule.

        Args:
            coeffs (list): Coefficients of the polynomial, from lowest to highest degree.
            d (Scalar): The constant term of the linear divisor.

        Returns:
            tuple: (quotient coefficients, remainder)
        """
        assert len(self.coeffs) > 0, "Polynomial degree must be at least 1"

        n = len(self.coeffs)
        quotient = [0] * (n - 1)
        
        # Start with the highest degree coefficient
        current = self.coeffs[-1]
        
        # Iterate through coefficients from second-highest to lowest degree
        for i in range(n - 2, -1, -1):
            # Store the current value in the quotient
            quotient[i] = current
            
            # Compute the next value
            current = current * d + self.coeffs[i]
        
        # The final current value is the remainder
        remainder = current

        return UniPolynomial(quotient), remainder

    @classmethod    
    def vanishing_polynomial_fft(cls, domain_size):
        assert is_power_of_two(domain_size), "Domain size must be a power of 2"

        coeffs = [Fr(0)] * (domain_size + 1)
        coeffs[0] = -Fr.one()
        coeffs[-1] = Fr.one()
        return UniPolynomial(coeffs)
    
    def compute_evaluations_fft(self, n:int, omega: F):
        assert (n & (n - 1) == 0), "Domain size must be a power of 2"
        k = log_2(n)
        return UniPolynomial.ntt_evals_from_coeffs(self.coeffs, k, omega)

    @classmethod
    def interpolate_fft(cls, evals, omega):
        """
        Interpolate a polynomial from its evaluations using FFT.

        Args:
            evals (list): Evaluations of the polynomial.
            omega: The omega root of unity.

        Returns:
        """

        n = len(evals)
        assert is_power_of_two(n), "Domain size must be a power of 2"
        k_log_size = log_2(n)

        coeffs = cls.ntt_coeffs_from_evals(evals, k_log_size, omega)
        return cls(coeffs)
    
    @classmethod
    def barycentric_weights_fft(cls, domain_size):
        """
        Compute barycentric weights for a given domain size using FFT.

            H = (1, omega, omega^2, ..., omega^(n-1))

            zH(X) = X^n - 1

            zH'(X) = nX^(n-1)

            w_i = 1/zH'(omega_i) = 1 / n*omega_i^{n-1} = (omega_i)/n

        Args:
            domain_size (int): The size of the domain.

        Returns:
            list: Barycentric weights.
        """
        n = domain_size
        omega = Fr.nth_root_of_unity(n)
        n_inv = Fr(n).inv()
        
        x = n_inv
        weights = []
        for i in range(n):
            weights.append(x)
            x *= omega
        return weights
    ############################################################
    # Non-fft interpolation
    ############################################################

    @staticmethod
    def construct_subproduct_tree_fix(domain):
        """
        Construct a subproduct tree for the given domain.

        Args:
            domain (list): A list of field elements representing the domain.

        Returns:
            dict: A dictionary representing the subproduct tree.
        """
        n = len(domain)
        if n == 1:
            return {"poly": [-domain[0], Fr.one()], "children": None}

        mid = n // 2
        left = UniPolynomial.construct_subproduct_tree_fix(domain[:mid])
        right = UniPolynomial.construct_subproduct_tree_fix(domain[mid:])

        poly = UniPolynomial.polynomial_multiplication(left["poly"], right["poly"])

        return {"poly": poly, "children": (left, right)}
    
    @staticmethod
    def compute_eval_fix(tree, f, domain):
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
            return [UniPolynomial.evaluate_at_point(f, domain[0])]

        left_tree, right_tree = tree["children"]

        _, r0 = UniPolynomial.polynomial_division_with_remainder(f, left_tree["poly"])
        _, r1 = UniPolynomial.polynomial_division_with_remainder(f, right_tree["poly"])

        mid = n // 2

        left_evals = UniPolynomial.compute_eval_fix(left_tree, r0, domain[:mid])
        right_evals = UniPolynomial.compute_eval_fix(right_tree, r1, domain[mid:])

        return left_evals + right_evals

    @staticmethod
    def compute_linear_combination_linear_moduli_fix(tree, ws, domain):
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

        left_poly = UniPolynomial.compute_linear_combination_linear_moduli_fix(left_tree, left_ws, domain[:mid])
        right_poly = UniPolynomial.compute_linear_combination_linear_moduli_fix(right_tree, right_ws, domain[mid:])

        left_result = UniPolynomial.polynomial_multiplication(left_poly, right_tree["poly"])
        right_result = UniPolynomial.polynomial_multiplication(right_poly, left_tree["poly"])

        result = UniPolynomial.polynomial_addition(left_result, right_result)

        return result
    
    @staticmethod
    def evaluate_at_point(poly: list[F], point: F) -> F:
        """Evaluate a polynomial at a single point using Horner's method."""
        result = 0
        for coeff in reversed(poly):
            result = result * point + coeff
        return result

    def evaluate(self, point):
        return self.evaluate_at_point(self.coeffs, point)


    # @staticmethod
    # def polynomial_division(dividend, divisor):
    #     """
    #     Perform polynomial long division.

    #     Args:
    #         dividend (list): Coefficients of the dividend polynomial.
    #         divisor (list): Coefficients of the divisor polynomial.

    #     Returns:
    #         tuple: (quotient, remainder)
    #     """
    #     dividend = [x for x in dividend]  # Make a copy
    #     divisor = [x for x in divisor if x != 0]  # Remove leading zeros
    #     if len(dividend) < len(divisor):
    #         return [], dividend
        
    #     quotient = [Fr.zero()] * (len(dividend) - len(divisor) + 1)
    #     for i in range(len(quotient)-1, -1, -1):
    #         quotient[i] = dividend[-1] // divisor[-1]
    #         for j in range(len(divisor)):
    #             dividend[i+j] -= quotient[i] * divisor[j]
    #         dividend.pop()
        
    #     remainder = [x for x in dividend if x != 0]  # Remove leading zeros
    #     return quotient, remainder
    
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

        # 1. Building up subproduct tree
        tree = cls.construct_subproduct_tree_fix(domain)

        # 2. Construct z'(X) in O(n) time
        z_derivative = cls.compute_z_derivative(tree["poly"])

        # 3. Compute barycentric weights
        z_derivative_at_u = cls.compute_eval_fix(tree, z_derivative, domain)
        ws = [1 / zd for zd in z_derivative_at_u]

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
    def from_evals(cls, evals):
        """
        Interpolate a polynomial from its evaluations.
        """
        n = len(evals)
        assert is_power_of_two(n), "Domain size must be a power of 2"
        omega = Fr.nth_root_of_unity(n)

        return cls.interpolate_fft(evals, omega)

    # barycentric interpolation with O(n^2) time complexity
    @classmethod
    def barycentric_weights(cls, D):
        n = len(D)
        weights = [1] * n
        for i in range(n):
            # weights[i] = product([(D[i] - D[j]) if i !=j else Fp(1) for j in range(n)])
            for j in range(n):
                if i==j:
                    weights[i] *= 1
                    continue
                weights[i] *= (D[i] - D[j])
            weights[i] = 1/weights[i]
        return weights
    
    @classmethod
    def lagrange_polynomial(cls, i, domain) -> 'UniPolynomial':
        n = len(domain)
        barycentric_weights = cls.barycentric_weights(domain)
        zH_poly = UniPolynomial.vanishing_polynomial(domain)
        l_poly = UniPolynomial.const(barycentric_weights[i]) * zH_poly // UniPolynomial([-domain[i], Fr.one()])
        return l_poly
    
    @classmethod
    def lagrange_polynomial_fft(cls, i, domain_size) -> 'UniPolynomial':
        n = domain_size
        domain = [Fr.nth_root_of_unity(n)**i for i in range(n)]
        barycentric_weights = cls.barycentric_weights(domain)
        zH_poly = UniPolynomial.vanishing_polynomial(domain)
        l_poly = UniPolynomial.const(barycentric_weights[i]) * zH_poly // UniPolynomial([-domain[i], Fr.one()])
        return l_poly

    @classmethod
    def uni_eval_from_evals(cls, evals, z, D):
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
        shift_value_power = Fr(1)
        for i in range(len(self.coeffs)):
            coeffs.append(self.coeffs[i] * shift_value_power)
            shift_value_power *= shift_value
        return UniPolynomial(coeffs)
    
    @classmethod
    def const(cls, constant):
        if isinstance(constant, Fr):
            return UniPolynomial([constant])
        else:
            raise ValueError("Constant must be a field element")
    
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

def bit_reverse_permutation(elements: list, bit_length: int):
    n = len(elements)
    for i in range(n):
        j = reverse_bits(i, bit_length)
        if i < j:
            elements[i], elements[j] = elements[j], elements[i]
    return elements

def precompute_twiddles_for_fft(omega: F, domain_size: int, is_inversed: bool = False, is_reversed: bool = False):
    twiddles = []
    omega_power = F(1)
    for i in range(domain_size):
        if is_inversed:
            twiddles.insert(1, omega_power)
        else:
            twiddles.append(omega_power)
        print(f"twiddles: {twiddles}")
        omega_power *= omega

    if is_reversed:
        twiddles = bit_reverse_permutation(twiddles, log_2(domain_size))
    return twiddles


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

