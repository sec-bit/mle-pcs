from group import DummyGroup
from unipolynomial import UniPolynomial

class Commitment:
    """Represents a commitment."""
    def __init__(self, group, value):
        self.group = group
        self.value = value
    
    @classmethod
    def set_scalar(cls, scalar):
        cls.scalar = scalar

    @staticmethod
    def zero(self, group):
        return Commitment(group, self.group.zero())

    def __add__(self, other):
        """Add two commitments using + operator."""
        if not isinstance(other, Commitment) or self.group != other.group:
            raise TypeError("Can only add commitments from the same group")
        return Commitment(self.group, self.group.exp(self.value, 1) + self.group.exp(other.value, 1))
    
    def __sub__(self, other):
        """Subtract two commitments using - operator."""
        if not isinstance(other, Commitment) or self.group != other.group:
            raise TypeError("Can only subtract commitments from the same group")
        return Commitment(self.group, self.group.scalar_mul(self.value, 1) + self.group.scalar_mul(other.value, -1))
    
    def __mul__(self, other):
        """
        Overload the * operator for UniPolynomial instances.

        Args:
            other (UniPolynomial or scalar): The polynomial or scalar to multiply with this one.

        Returns:
            UniPolynomial: Product of the two polynomials or scalar multiplication result.
        """
        if not isinstance(other, (int, float, type(UniPolynomial.scalar))):  # Scalar multiplication
            raise TypeError("Unsupported operand type for *: '{}' and '{}'".format(type(self).__name__, type(other).__name__))
        return Commitment(self.group, self.group.scalar_mul(self.value, other))

    def __rmul__(self, other):
        """Multiply a commitment using * operator."""
        if not isinstance(other, (int, float, type(UniPolynomial.scalar))):
            raise TypeError("Can only multiply commitments from the same group")
        return Commitment(self.group, self.group.scalar_mul(self.value, other))

    def __repr__(self):
        return f"Commitment({self.value})"

class KZG10Commitment:
    """KZG10 commitment scheme."""

    def __init__(self, G1, G2, max_degree):
        self.G1 = G1
        self.G2 = G2
        self.max_degree = max_degree
        self.setup()
    
    def setup(self, secret_symbol = None, g1_generator = None, g2_generator = None) -> None:
        """Generate the structured reference string (SRS)."""
        if g1_generator is None:
            g = self.G1.field.primitive_element()
            h = self.G2.field.primitive_element()
        else:
            g = self.G1.field(g1_generator)
            h = self.G2.field(g2_generator)

        if secret_symbol is None:
            s = self.G1.field.random_element()
        else:
            s = secret_symbol
        self.srs = [self.G1.scalar_mul(g, s**i) for i in range(self.max_degree + 1)]
        self.srs2 = [self.G2.scalar_mul(h, s**i) for i in range(self.max_degree + 1)]
        self.h = h
        self.h_s = self.G2.scalar_mul(h, s)
    
    def commit(self, polynomial) -> Commitment:
        """
        Commit to a polynomial.
        
        """

        if isinstance(polynomial, list):
            polynomial = UniPolynomial(polynomial)
        elif isinstance(polynomial, UniPolynomial):
            pass
        else:
            raise TypeError("Invalid polynomial type")
        
        if polynomial.degree > self.max_degree:
            raise ValueError("Polynomial degree exceeds maximum supported degree")
        
        commitment = self.G1.field.zero()  # Identity element
        # commitment = self.group.exp(1, 0)  # Identity element
        for i, coeff in enumerate(polynomial.coeffs):
            commitment += coeff * self.srs[i]
        
        return Commitment(self.G1, commitment)
    

    @staticmethod
    def division_by_linear_divisor(coeffs, d):
        assert len(coeffs) > 1, "Polynomial degree must be at least 1"

        quotient = [0] * (len(coeffs) - 1)
        remainder = 0

        for i, coeff in enumerate(reversed(coeffs)):
            if i == 0:
                remainder = coeff
            else:
                quotient[-i] = remainder
                remainder = remainder * d + coeff

        return quotient, remainder
    
    def prove_eval(self, f: list, point, v):
        """
        C: commitment to f
        f: polynomial
        point: evaluation point
        v: evaluation value
        Rng: randomness
        """
        assert len(f) < self.max_degree, "Polynomial degree exceeds maximum supported degree"

        coeffs = f[:]
        coeffs[0] -= v
        # Compute the witness polynomial: (f(X) - f(z)) / (X - z)
        witness_poly, rem = self.division_by_linear_divisor(coeffs, point)
        # assert rem == Fp(0)
        # print("witness_poly=", witness_poly)

        # Compute the proof: commitment to the witness polynomial
        commitment = self.commit(witness_poly)

        return commitment
    
    def verify_eval(self, C: Commitment, proof: Commitment, point, v):
        """
        Verify an evaluation proof.

        Args:
            C (G1Point): Commitment to the polynomial.
            proof (G1Point): The evaluation proof.
            point (Scalar): The point at which the polynomial was evaluated.
            v (Scalar): The claimed evaluation result.

        Returns:
            bool: True if the proof is valid, False otherwise.
        """
        # Compute [v]G
        v_G = self.G1.scalar_mul(self.srs[0], v)

        # Compute [s]H - [z]H
        s_minus_z_H = self.G2.sub(self.h_s, self.G2.scalar_mul(self.h, point))

        # print("v_G=", v_G)
        # print("s_minus_z_H=", s_minus_z_H)
        # Check the pairing equation:
        # e(C - [y]G, H) = e(π, [s]H - [z]H)
        lhs = DummyGroup.pairing(self.G1.sub(C.value, v_G), self.h)
        rhs = DummyGroup.pairing(proof.value, s_minus_z_H)
        # print("lhs=", lhs)
        # print("rhs=", rhs)
        return lhs == rhs
    
    def prove_degree_bound(self, cm, f, degree_bound):
        """
        Prove the degree bound of a polynomial.

        Args:
            cm: commitment to the polynomial
            f: polynomial
            degree_bound: degree bound
        """
        assert degree_bound <= self.max_degree, \
                "Degree bound exceeds maximum supported degree"
        coeffs = f.copy()

        while len(coeffs) > 1 and coeffs[-1] == 0:
            coeffs.pop()

        assert len(coeffs) <= degree_bound, \
                "Polynomial degree exceeds maximum supported degree"
        
        degree_gap = self.max_degree - degree_bound + 1
        lift_coeffs = [0] * degree_gap + coeffs
        f_cm = self.commit(lift_coeffs)

        return (f_cm, degree_gap)

    def verify_degree_bound(self, C, proof, degree_bound):
        """
        Verify the degree bound of a polynomial.

        Args:
            C: commitment to the polynomial
            proof: proof of the degree bound
            degree_bound: degree bound
        """
        xf_cm, degree_gap = proof
        assert degree_gap >= self.max_degree - degree_bound + 1, \
                "Degree bound is less than the degree of the proof"
        h_gap = self.srs2[degree_gap]
        lhs = DummyGroup.pairing(C.value, h_gap)
        rhs = DummyGroup.pairing(xf_cm.value, self.h)
        return lhs == rhs


    def prove_eval_and_degree(self, f_cm, f, point, v, degree_bound):
        """
        Prove the degree bound of a polynomial.

        Args:
            cm: commitment to the polynomial
            f: polynomial
            degree_bound: degree bound
        """
        assert degree_bound <= self.max_degree, \
                "Degree bound exceeds maximum supported degree"
        coeffs = f.copy()

        while len(coeffs) > 1 and coeffs[-1] == 0:
            coeffs.pop()

        assert len(coeffs) <= degree_bound, \
                "Polynomial degree exceeds maximum supported degree"
        
        coeffs = f[:]
        coeffs[0] -= v
        # Compute the witness polynomial: (f(X) - f(z)) / (X - z)
        witness_poly, rem = self.division_by_linear_divisor(coeffs, point)

        degree_gap = self.max_degree - degree_bound + 2
        lift_coeffs = [0] * degree_gap + witness_poly
        xq_cm = self.commit(lift_coeffs)

        return (xq_cm, degree_gap)

    def verify_eval_and_degree(self, f_cm, arg, point, v, degree_bound):
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
        h_gap = self.srs2[degree_gap]
        
        # Compute [v]G
        v_G = self.G1.scalar_mul(self.srs[0], v)

        # Compute [s]H - [z]H
        s_minus_z_H = self.G2.sub(self.h_s, self.G2.scalar_mul(self.h, point))

        # Check the pairing equation:
        # e(C - [y]G, H) = e(π, [s]H - [z]H)
        lhs = DummyGroup.pairing(self.G1.sub(f_cm.value, v_G), h_gap)
        rhs = DummyGroup.pairing(xq_cm.value, s_minus_z_H)
        
        return lhs == rhs
    
