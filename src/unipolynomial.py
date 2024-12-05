# from sage.all import *

class UniPolynomial:

    def __init__(self, coeffs):
        """
        Initialize a UniPolynomial instance.

        Args:
            coeffs (list): Coefficients of the polynomial.
        """
        coeffs = [c for c in coeffs]
        # Remove leading zeros
        while len(coeffs) > 1 and coeffs[-1] == 0:
            coeffs.pop()
        self.coeffs = coeffs
        self.degree = len(coeffs) - 1 if coeffs else 0

    @classmethod
    def set_scalar(cls, scalar, scalar_constructor):
        cls.scalar = scalar
        cls.scalar_constructor = scalar_constructor

    def __neg__(self):
        """
        Negate the polynomial.

        Returns:
            UniPolynomial: A new polynomial with all coefficients negated.
        """
        return UniPolynomial([-coeff for coeff in self.coeffs])
    
    @classmethod
    def add(cls, poly1, poly2):
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
    
    def __add__(self, other):
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
    def subtract(cls, poly1, poly2):
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
        domain_size = 2 ** k_log_size
        assert len(coeffs) == domain_size, f"len(coeffs) != domain_size, coeffs: {coeffs}, domain_size: {domain_size}"

        # Bit-reversing
        for k in range(domain_size):
            k_rev = cls.bit_reverse(k, k_log_size)
            if k < k_rev:
                coeffs[k], coeffs[k_rev] = coeffs[k_rev], coeffs[k]

        sep = 1
        for _ in range(k_log_size):
            w = 1
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
    def ntt_evals_from_coeffs(cls, coeffs, k_log_size, omega):
        n = len(coeffs)
        assert (n & (n - 1) == 0), "Domain size must be a power of 2"

        coeffs = [c for c in coeffs]
        # omega = cls.get_root_of_unity(k_log_size)
        return cls.ntt_core(coeffs.copy(), omega, k_log_size)

    @classmethod
    def ntt_coeffs_from_evals(cls, evals, k_log_size, omega, one=1):
        n = len(evals)
        assert (n & (n - 1) == 0), "Domain size must be a power of 2"

        # omega = cls.get_root_of_unity(k_log_size)
        # evals = [Fp(e) for e in evals]

        omega_inv = omega.inverse()
        domain_size = UniPolynomial.scalar_constructor(2 ** k_log_size)
        domain_size_inv = one / domain_size
        
        coeffs = cls.ntt_core(evals.copy(), omega_inv, k_log_size)
        return [c * domain_size_inv for c in coeffs]
    
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
        dividend = [UniPolynomial.scalar_constructor(c) for c in dividend]
        divisor = [UniPolynomial.scalar_constructor(c) for c in divisor]
        if not divisor or (len(divisor) == 1 and divisor[0] == 0):
            raise ValueError("Division by zero polynomial")

        # Remove leading zeros
        while dividend and dividend[-1] == 0:
            dividend.pop()
        while divisor and divisor[-1] == 0:
            divisor.pop()

        if len(dividend) < len(divisor):
            return [], dividend

        quotient = [0] * (len(dividend) - len(divisor) + 1)
        remainder = dividend.copy()

        for i in range(len(quotient)-1, -1, -1):
            if len(remainder) < len(divisor):
                break
            quot = remainder[-1] / divisor[-1]
            quotient[i] = quot

            for j in range(len(divisor)):
                remainder[i+j] -= quot * divisor[j]

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
        assert len(self.coeffs) > 1, "Polynomial degree must be at least 1"

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
            return {"poly": [-domain[0], 1], "children": None}

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

        _, r0 = UniPolynomial.polynomial_division(f, left_tree["poly"])
        _, r1 = UniPolynomial.polynomial_division(f, right_tree["poly"])

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
    def evaluate_at_point(poly, point):
        """Evaluate a polynomial at a single point using Horner's method."""
        result = 0
        for coeff in reversed(poly):
            result = result * point + coeff
        return result

    def evaluate(self, point):
        return self.evaluate_at_point(self.coeffs, point)

    @staticmethod
    def polynomial_division(dividend, divisor):
        """
        Perform polynomial long division.

        Args:
            dividend (list): Coefficients of the dividend polynomial.
            divisor (list): Coefficients of the divisor polynomial.

        Returns:
            tuple: (quotient, remainder)
        """
        dividend = [UniPolynomial.scalar_constructor(x) for x in dividend]  # Make a copy
        divisor = [UniPolynomial.scalar_constructor(x) for x in divisor if x != 0]  # Remove leading zeros
        if len(dividend) < len(divisor):
            return [], dividend
        
        quotient = [0] * (len(dividend) - len(divisor) + 1)
        for i in range(len(quotient)-1, -1, -1):
            quotient[i] = dividend[-1] // divisor[-1]
            for j in range(len(divisor)):
                dividend[i+j] -= quotient[i] * divisor[j]
            dividend.pop()
        
        remainder = [x for x in dividend if x != 0]  # Remove leading zeros
        return quotient, remainder
    
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
        Compute polynomial coefficients from evaluations using fast interpolation.

        Args:
            evals (list): Evaluations of the polynomial.
            domain (list): Domain points where the polynomial was evaluated.

        Returns:
            list: Coefficients of the interpolated polynomial.
        """
        n = len(domain)
        assert len(evals) == n, f"Number of evaluations must match domain size, evals: {evals}, domain: {domain}"

        # evals = [e for e in evals]
        # domain = [d for d in domain]

        # 1. Building up subproduct tree
        tree = cls.construct_subproduct_tree_fix(domain)

        # 2. Construct z'(X) in O(n) time
        z_derivative = cls.compute_z_derivative(tree["poly"])

        # 3. Compute barycentric weights
        z_derivative_at_u = cls.compute_eval_fix(tree, z_derivative, domain)
        ws = [1 / zd for zd in z_derivative_at_u]
        ws = [w * e for w, e in zip(ws, evals)]

        # 4. Compute barycentric interpolation
        f = cls.compute_linear_combination_linear_moduli_fix(tree, ws, domain)

        return f

    @classmethod
    def compute_evals_from_coeffs_fast(cls, coeffs, domain, debug=0):
        """
        Compute evaluations from coefficients in O(n log^2 n) time.

        Args:
            coeffs (list): Coefficients of the polynomial.
            domain (list): Domain points where to evaluate the polynomial.

        Returns:
            list: Evaluations of the polynomial over the domain.
        """
        n = len(domain)

        if debug > 0: print(f"compute_evals_from_coeffs_fast: coeffs: {coeffs}, domain: {domain}")

        assert n == len(coeffs), f"Domain size must match the number of coefficients, coeffs: {coeffs}, domain: {domain}"
        assert (n & (n - 1) == 0), f"Domain size must be a power of 2, domain: {domain}"

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

    # barycentric interpolation
    @classmethod
    def barycentric_weights(cls, D, one=1):
        n = len(D)
        weights = [1] * n
        for i in range(n):
            # weights[i] = product([(D[i] - D[j]) if i !=j else Fp(1) for j in range(n)])
            for j in range(n):
                if i==j:
                    weights[i] *= one
                    continue
                weights[i] *= (D[i] - D[j])
            weights[i] = one / weights[i]
        return weights

    @classmethod
    def uni_eval_from_evals(cls, evals, z, D, one=1):
        n = len(evals)
        if n != len(D):
            raise ValueError("Domain size should be equal to the length of evaluations")
        if z in D:
            return evals[D.index(z)]
        weights = cls.barycentric_weights(D, one)
        # print("weights={}".format(weights))
        e_vec = [weights[i] / (z - D[i]) for i in range(n)]
        numerator = sum([e_vec[i] * evals[i] for i in range(n)])
        denominator = sum([e_vec[i] for i in range(n)])
        return (numerator / denominator)

# Example usage
if __name__ == "__main__":
    # f(X) = X^3 + 3X^2 + 2X + 5
    f = UniPolynomial([5, 2, 3, 1])
    x = UniPolynomial([0, 1])  # Represents X
    d = 1  # Dividing by (X - 1)

    q, r = f.division_by_linear_divisor(d)
    print(f"f(X) = {f}")
    print(f"Dividing by (X - {d})")
    print(f"Quotient: {q}")
    print(f"Remainder: {r}")

    # Verify the result
    # f(X) should equal q(X) * (X - d) + r
    linear_divisor = x - UniPolynomial([d])
    result = q * linear_divisor + UniPolynomial([r])
    print(f"Verification: {result}")
    print(f"Original polynomial: {f}")
    print(f"Equal: {result.coeffs == f.coeffs}")