# This KZG implementation is adapted from the arkworks project
# https://github.com/arkworks-rs/poly-commit
# Specifically, from the file poly-commit/src/kzg10/mod.rs
# Any modification to arkwork's code will be marked in this file
# Commit version: 12f5529c9ca609d07dd4683fcd1e196bc375eb0d

from group import DummyGroup
from unipolynomial import UniPolynomial
from field import Field
from random import randint

# This argument is set false to not use the WNAF method for multi-scalar multiplication
# because WNAF method is not tested yet
negation_is_cheap = False

# This class is builded by ourselves.
class Commitment:
    """Represents a commitment in the KZG scheme."""
    def __init__(self, group, value):
        self.group = group
        self.value = value
    
    @classmethod
    def set_scalar(cls, scalar):
        cls.scalar = scalar

    @staticmethod
    def zero(self, group):
        """Create a zero commitment."""
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

# This class is partially adapted from 'struct KZG10' in arkworks project
class KZG10Commitment:
    """KZG10 commitment scheme implementation."""

    # There is a little modification
    # In python implementation, we use __init__ instead of generics in rust, to store information of G1, G2
    def __init__(self, G1, G2, debug=False):
        """
        Initialize the KZG10 commitment scheme.
        
        Args:
            G1, G2: Elliptic curve groups
            debug: Enable debug assertions
        """
        self.G1 = G1
        self.G2 = G2
        self.debug = debug
    
    # Implemented following the function 'setup' in arkworks project,
    # expect that this function enables input a secret_symbol rather than generate the beta using random function
    # and this function does not return prepared_h and prepared_beta_h which are not used in python implementation
    def setup(self, max_degree, produce_g2_powers=False, secret_symbol = None, g1_generator = None, g2_generator = None) -> None:
        """
        Generate the structured reference string (SRS).
        
        Args:
            max_degree: Maximum polynomial degree supported
            produce_g2_powers: Whether to produce powers in G2
            secret_symbol: Secret value for SRS (if None, randomly generated)
            g1_generator, g2_generator: Generators for G1 and G2 (if None, randomly chosen)
        
        Returns:
            Dictionary containing the SRS parameters
        """
        if g1_generator is None:
            g = self.G1.field.random_element()
            h = self.G2.field.random_element()
        else:
            g = self.G1.field(g1_generator)
            h = self.G2.field(g2_generator)

        if secret_symbol is None:
            beta = self.G1.field.random_element()
        else:
            beta = secret_symbol

        gamma_g = self.G1.field.random_element()

        powers_of_s = [beta ** i for i in range(max_degree + 2)]
        powers_of_g = [g * powers_of_s[i] for i in range(max_degree + 1)]
        powers_of_gamma_g = [gamma_g * powers_of_s[i] for i in range(max_degree + 2)]
        neg_powers_of_h = []
        if produce_g2_powers:
            neg_powers_of_beta = [1]
            cur = 1 / beta
            for _ in range(max_degree):
                neg_powers_of_beta.append(cur)
                cur /= beta

            neg_powers_of_h = [h * neg_powers_of_beta[i] for i in range(max_degree + 1)]

        result = {}
        result['powers_of_g'] = powers_of_g
        result['powers_of_gamma_g'] = powers_of_gamma_g
        result['h'] = h
        result['beta_h'] = beta * h
        result['neg_powers_of_h'] = neg_powers_of_h

        return result
    
    # Implemented following the function 'trim' in arkworks project,
    # but this function does not return prepared_h and prepared_beta_h which are not used in python implementation
    def trim(self, pp, supported_degree):
        if supported_degree == 1:
            supported_degree += 1
        powers_of_g = pp['powers_of_g'][:supported_degree + 1]
        powers_of_gamma_g = pp['powers_of_gamma_g'][:supported_degree + 1]

        powers = {
            'powers_of_g': powers_of_g,
            'powers_of_gamma_g': powers_of_gamma_g,
        }

        vk = {
            'g': pp['powers_of_g'][0],
            'gamma_g': pp['powers_of_gamma_g'][0],
            'h': pp['h'],
            'beta_h': pp['beta_h']
        }
        return powers, vk
    
    # Implemented basically following the function 'commit' in arkworks project, except some differences in grammar
    def commit(self, powers, polynomial: UniPolynomial, hiding_bound=None):
        """
        Commit to a polynomial.
        
        Args:
            polynomial: The polynomial to commit to
        
        Returns:
            tuple: (Commitment, random_ints used for hiding)
        """
        # Check if polynomial degree is too large
        num_coefficients = polynomial.degree + 1
        num_powers = len(powers['powers_of_g'])
        assert num_coefficients <= num_powers, f"Too many coefficients, num_coefficients: {num_coefficients}, num_powers: {num_powers}"
        
        # Commitment calculation
        num_leading_zeros, plain_coeffs = skip_leading_zeros_and_convert_to_bigints(polynomial)
        commitment = msm_bigint(negation_is_cheap, powers['powers_of_g'][num_leading_zeros:], plain_coeffs)

        # Debug assertion
        if self.debug:
            assert isinstance(commitment, Field), f"commitment: {commitment.coeffs}"

        # Add hiding polynomial if hiding_bound is set
        random_ints = []
        if hiding_bound is not None:
            while UniPolynomial(random_ints).degree == 0:
                random_ints = [self.G1.field.random_element() for _ in range(hiding_bound + 1)]
            
            if self.debug:
                assert UniPolynomial(random_ints).degree > 0, f"Degree of random poly is zero, random_ints: {random_ints}"
        
            # Check hiding bound
            hiding_poly_degree = len(random_ints) - 1
            num_powers = len(powers['powers_of_gamma_g'])
            assert hiding_bound != 0, "Hiding bound is zero"
            assert hiding_poly_degree < num_powers, "Hiding bound is too large"
        
            random_commitment = msm_bigint(negation_is_cheap, powers['powers_of_gamma_g'], random_ints)
            commitment += random_commitment

        # Final debug assertion
        if self.debug:
            assert isinstance(commitment, Field)

        return Commitment(self.G1, commitment), random_ints
    
    # Implemented completely following the function 'compute_witness_polynomial' in arkworks project
    def compute_witness_polynomial(self, polynomial: UniPolynomial, point, random_ints, hiding=False):
        """
        Compute the witness polynomial for a given polynomial and point.
        
        Args:
            polynomial: The polynomial to compute the witness polynomial for
            point: The point at which to evaluate the polynomial
            random_ints: Random integers used for hiding
        
        Returns:
            tuple: (witness polynomial, hiding witness polynomial)
        """
        witness_polynomial, _pz = polynomial.division_by_linear_divisor(point)
        random_witness_polynomial = None
        if hiding:
            random_poly = UniPolynomial(random_ints)
            if self.debug:
                assert random_poly.degree > 0, f"Degree of random poly is zero, random_ints: {random_ints}"
            random_witness_polynomial, _pr = UniPolynomial(random_ints).division_by_linear_divisor(point)
        return witness_polynomial, random_witness_polynomial
    
    # Implemented completely following the function 'open_with_witness_polynomial' in arkworks project
    def open_with_witness_polynomial(self, powers, point, random_ints, witness_polynomial, hiding_witness_polynomial=None):
        """
        Open the commitment with a witness polynomial.
        
        Args:
            point: The point at which the polynomial was evaluated
            random_ints: Random integers used for hiding
            witness_polynomial: The witness polynomial
            hiding_witness_polynomial: The hiding witness polynomial (optional)
        
        Returns:
            Dictionary containing the proof values
        """
        assert witness_polynomial.degree + 1 < len(powers['powers_of_g']), "Too many coefficients"
        num_leading_zeros, witness_coeffs = skip_leading_zeros_and_convert_to_bigints(witness_polynomial)

        w = msm_bigint(negation_is_cheap, powers['powers_of_g'][num_leading_zeros:], witness_coeffs)

        random_v = None
        if hiding_witness_polynomial is not None:
            blinding_p = UniPolynomial(random_ints)
            random_v = blinding_p.evaluate(point)
            w += msm_bigint(negation_is_cheap, powers['powers_of_gamma_g'], hiding_witness_polynomial.coeffs)

        return {'w': w, 'random_v': random_v}
    
    # Implemented completely following the function 'open' in arkworks project
    def open(self, powers, polynomial: UniPolynomial, point, random_ints, hiding=False):
        """
        Open the polynomial at a given point.
        
        Args:
            polynomial: The polynomial to open
            point: The point at which the polynomial was opened
            random_ints: Random integers used for hiding
        
        Returns:
            Dictionary containing the proof values
        """
        assert polynomial.degree + 1 < len(powers['powers_of_g']), f"Too many coefficients, polynomial.degree: {polynomial.degree}"
        
        witness_poly, hiding_witness_poly = self.compute_witness_polynomial(polynomial, point, random_ints, hiding)

        return self.open_with_witness_polynomial(powers, point, random_ints, witness_poly, hiding_witness_poly)

    # Implemented completely following the function 'check' in arkworks project
    def check(self, vk, comm: Commitment, point, value, proof, hiding=False):
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
        inner = comm.value - vk['g'] * value
        if hiding:
            inner -= vk['gamma_g'] * proof['random_v']
        lhs = DummyGroup.pairing(inner, vk['h'])
        rhs = DummyGroup.pairing(proof['w'], vk['beta_h'] - vk['h'] * point)
        return lhs.value[0] == rhs.value[0]
    
    # Implemented completely following the function 'batch_check' in arkworks project
    def batch_check(self, vk, commitments, points, values, proofs, hiding=False):
        total_c = 0
        total_w = 0

        # combination
        randomizer = 1
        g_multiplier = 0
        gamma_g_multiplier = 0

        for c, z, v, proof in zip(commitments, points, values, proofs):
            c = z * proof['w'] + c.value.value[0]
            g_multiplier += randomizer * v
            if hiding:
                gamma_g_multiplier += randomizer * proof['random_v']
            total_c += c.value[0] * randomizer
            total_w += proof['w'] * randomizer
            randomizer = randint(0, 1 << 128)

        total_c -= vk['g'] * g_multiplier
        if hiding:
            total_c -= vk['gamma_g'] * gamma_g_multiplier
        
        return DummyGroup.pairing(total_w, vk['beta_h']) \
            == DummyGroup.pairing(total_c, vk['h'])

    # This function is totally built by ourselves
    @staticmethod
    def division_by_linear_divisor(coeffs, d):
        """
        Perform polynomial division by a linear divisor.
        
        Args:
            coeffs: List of polynomial coefficients
            d: The constant number in the divisor
        
        Returns:
            tuple: (quotient coefficients, remainder)
        """
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
    
    
# Implemented completely following the function 'skip_leading_zeros_and_convert_to_bigints' in arkworks project
def skip_leading_zeros_and_convert_to_bigints(p):
    """
    Remove leading zeros from polynomial coefficients and convert to big integers.
    
    Args:
        p: UniPolynomial instance
    
    Returns:
        tuple: (number of leading zeros, list of non-zero coefficients as big integers)
    """
    num_leading_zeros = 0
    coeffs = p.coeffs
    
    while num_leading_zeros < len(coeffs) and coeffs[num_leading_zeros] == 0:
        num_leading_zeros += 1
    
    return num_leading_zeros, coeffs[num_leading_zeros:]


# BE CAREFUL: This function is not totally tested yet
def msm_bigint(negation_is_cheap, bases, bigints):
    """
    Perform multi-scalar multiplication using big integers.
    
    Args:
        negation_is_cheap: Whether negation is cheap in the group
        bases: List of group elements
        bigints: List of big integers
    
    Returns:
        Group element representing the result of the multi-scalar multiplication
    """
    if negation_is_cheap:
        return msm_bigint_wnaf(bases, bigints)
    else:
        return msm_bigint_basic(bases, bigints)


# This is a simple implementation of multi-scalar multiplication using big integers
# built by ourselves
def msm_bigint_basic(bases, bigints):
    """
    Basic implementation of multi-scalar multiplication using big integers.
    
    Args:
        bases: List of group elements
        bigints: List of big integers
    
    Returns:
        Group element representing the result of the multi-scalar multiplication
    """
    result = 0
    for base, scalar in zip(bases, bigints):
        result += base * scalar
    return result


# BE CAREFUL: This function is not totally tested yet
def msm_bigint_wnaf(bases, bigints):
    """
    Implementation of multi-scalar multiplication using big integers and the Window NAF method.
    
    Args:
        bases: List of group elements
        bigints: List of big integers
    
    Returns:
        Group element representing the result of the multi-scalar multiplication
    """
    WINDOW_SIZE = 5
    result = 0
    
    # Precompute window
    precomp = [[base * i for i in range(1 << (WINDOW_SIZE - 1))] for base in bases]
    
    for i in range(max(next_power_of_two(bigint) for bigint in bigints)):
        result = result + result
        for j, (base, scalar) in enumerate(zip(bases, bigints)):
            if next_power_of_two(scalar) > i:
                window = (scalar >> i) & ((1 << WINDOW_SIZE) - 1)
                if window:
                    if window >= (1 << (WINDOW_SIZE - 1)):
                        result -= precomp[j][window - (1 << (WINDOW_SIZE - 1))]
                    else:
                        result += precomp[j][window - 1]
    
    return result
    

# This function is implemented by ourselves
def next_power_of_two(n):
    """
    Find the next power of two greater than or equal to a given number.
    
    Args:
        n: The number
    
    Returns:
        The next power of two
    """
    assert n >= 0, "No negative integer"
    d = n
    k = 0
    while d > 0:
        d >>= 1
        k += 1
    return k


if __name__ == '__main__':
    # Test regular check
    print("Testing regular check...")
    
    # Create a polynomial and a point
    test_poly = UniPolynomial([randint(0, 100) for _ in range(randint(5, 10))])
    test_point = randint(0, 100)
    
    # Create KZG10 commitment scheme instance
    kzg = KZG10Commitment(DummyGroup(Field), DummyGroup(Field), debug=True)
    params = kzg.setup(100, False, None, None, None)
    powers, vk = kzg.trim(params, 100)
    
    # Commit to the polynomial
    commitment, random_ints = kzg.commit(powers, test_poly)
    
    # Evaluate the polynomial
    value = test_poly.evaluate(test_point)
    
    # Generate proof
    proof = kzg.open(powers, test_poly, test_point, random_ints)
    
    # Verify
    assert kzg.check(vk, commitment, test_point, value, proof), "Regular check failed"
    
    print("Regular check passed successfully")
    
    # Test with an invalid proof
    invalid_proof = kzg.open(powers, test_poly, test_point + 1, random_ints)  # Invalid point
    
    assert not kzg.check(vk, commitment, test_point, value, invalid_proof), "Regular check should have failed with invalid proof"
    
    print("Regular check correctly failed with invalid proof")

    # Test batch check
    print("Testing batch check...")
    
    # Test batch_check
    num_polynomials = 5
    polynomials = [UniPolynomial([randint(0, 100) for _ in range(randint(10, 100))]) for _ in range(num_polynomials)]
    points = [randint(0, 100) for _ in range(num_polynomials)]
    
    # Create KZG10 commitment scheme instance
    kzg = KZG10Commitment(DummyGroup(Field), DummyGroup(Field), 101)
    params = kzg.setup(100, False, None, None, None)
    powers, vk = kzg.trim(params, 100)
    
    commitments = []
    values = []
    proofs = []
    
    for p, point in zip(polynomials, points):
        # Commit to the polynomial
        comm, random_ints = kzg.commit(powers, p, hiding_bound=3)
        commitments.append(comm)
        
        # Evaluate the polynomial
        value = p.evaluate(point)
        values.append(value)
        
        # Generate proof
        proof = kzg.open(powers, p, point, random_ints, True)
        proofs.append(proof)
    
    # Verify batch
    assert kzg.batch_check(vk, commitments, points, values, proofs, True), "Batch check failed"
    
    print("Batch check passed successfully")
    
    # Test with an invalid proof
    invalid_proof_index = randint(0, num_polynomials - 1)
    proofs[invalid_proof_index] = kzg.open(powers, polynomials[invalid_proof_index], points[invalid_proof_index] + 1, random_ints, True)  # Invalid point
    
    assert not kzg.batch_check(vk, commitments, points, values, proofs, True), "Batch check should have failed with invalid proof"
    
    print("Batch check correctly failed with invalid proof")

    # TODO: Integrate with py_ecc library
