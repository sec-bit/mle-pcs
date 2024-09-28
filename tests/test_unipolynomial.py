from functools import reduce
from unittest import TestCase, main
from random import randint
import sys

sys.path.append('../src')
sys.path.append('src')

from unipolynomial import UniPolynomial

class UniPolynomialTest(TestCase):
    def setUp(self):
        # Set up a scalar field for testing (e.g., integers modulo a prime)
        prime = 193  # A small prime for testing
        UniPolynomial.set_scalar(int, lambda x: x % prime)

    def test_initialization(self):
        p = UniPolynomial([1, 2, 3])
        self.assertEqual(p.coeffs, [1, 2, 3])
        self.assertEqual(p.degree, 2)

        # Test removing leading zeros
        p = UniPolynomial([1, 2, 3, 0, 0])
        self.assertEqual(p.coeffs, [1, 2, 3])
        self.assertEqual(p.degree, 2)

    def test_addition(self):
        p1 = UniPolynomial([1, 2, 3])
        p2 = UniPolynomial([4, 5, 6, 7])
        result = p1 + p2
        self.assertEqual(result.coeffs, [5, 7, 9, 7])

    def test_subtraction(self):
        p1 = UniPolynomial([4, 5, 6, 7])
        p2 = UniPolynomial([1, 2, 3])
        result = p1 - p2
        self.assertEqual(result.coeffs, [3, 3, 3, 7])

    def test_multiplication(self):
        p1 = UniPolynomial([1, 2])
        p2 = UniPolynomial([3, 4, 5])
        result = p1 * p2
        self.assertEqual(result.coeffs, [3, 10, 13, 10])

    def test_division(self):
        p1 = UniPolynomial([5, 2, 3, 1])  # x^3 + 3x^2 + 2x + 5
        p2 = UniPolynomial([1, 1])  # x + 1
        q, r = divmod(p1, p2)
        self.assertEqual(q.coeffs, [0, 2, 1])  # x^2 + 2x
        self.assertEqual(r.coeffs, [5])  # 5

    def test_evaluation(self):
        p = UniPolynomial([1, 2, 1])  # x^2 + 2x + 1
        self.assertEqual(p.evaluate(2), 9)  # (2^2 + 2*2 + 1) % 193 = 9

    def test_interpolation(self):
        from sage.all import GF
        from field import magic

        Fp = magic(GF(193))
        domain = [Fp(1), Fp(2), Fp(3), Fp(4)]
        evals = [Fp(3), Fp(7), Fp(13), Fp(21)]  # Corresponds to x^2 + x + 1
        p = UniPolynomial.interpolate(evals, domain)
        self.assertEqual(p.coeffs, [1, 1, 1])

    def test_vanishing_polynomial(self):
        domain = [0, 1, 2]
        v = UniPolynomial.vanishing_polynomial(domain)
        for x in domain:
            self.assertEqual(v.evaluate(x), 0)

    def test_negation(self):
        p = UniPolynomial([1, 2, 3])
        neg_p = -p
        self.assertEqual(neg_p.coeffs, [-1, -2, -3])

    def test_scalar_addition(self):
        p = UniPolynomial([1, 2, 3])
        result = p + UniPolynomial([2, 3, 1])
        self.assertEqual(result.coeffs, [3, 5, 4])

    def test_scalar_multiplication(self):
        p = UniPolynomial([1, 2, 3])
        result = p * 2
        self.assertEqual(result.coeffs, [2, 4, 6])

    def test_right_scalar_multiplication(self):
        p = UniPolynomial([1, 2, 3])
        result = 2 * p
        self.assertEqual(result.coeffs, [2, 4, 6])

    def test_floor_division(self):
        p1 = UniPolynomial([5, 2, 3, 1])  # x^3 + 3x^2 + 2x + 5
        p2 = UniPolynomial([1, 1])  # x + 1
        q = p1 // p2
        self.assertEqual(q.coeffs, [0, 2, 1])  # x^2 + 2x

    def test_modulo(self):
        p1 = UniPolynomial([5, 2, 3, 1])  # x^3 + 3x^2 + 2x + 5
        p2 = UniPolynomial([1, 1])  # x + 1
        r = p1 % p2
        self.assertEqual(r.coeffs, [5])  # 5

    def test_repr(self):
        p = UniPolynomial([1, 0, 2, 3])
        self.assertEqual(repr(p), "1 + 2x^2 + 3x^3")

    def test_bit_reverse(self):
        self.assertEqual(UniPolynomial.bit_reverse(1, 3), 4)
        self.assertEqual(UniPolynomial.bit_reverse(3, 3), 6)

    def test_ntt_core(self):
        from sage.all import GF
        from field import magic

        Fp = GF(193)
        Fp = magic(Fp)

        # This test might need to be adjusted based on your specific implementation
        coeffs = [Fp(1), Fp(2), Fp(3), Fp(4)]
        coeffs_copy = coeffs[::-1]
        omega = Fp.primitive_element() ** 48  # This should be a proper root of unity in your field
        res1 = UniPolynomial.ntt_core(coeffs, omega, 2)
        res2 = [reduce(lambda t, s: t * (omega ** x) + s, coeffs_copy, 0) for x in range(0, 4)]
        self.assertEqual(res1, res2)

    def test_ntt_evals_from_coeffs(self):
        from sage.all import GF
        from field import magic

        Fp = GF(193)
        Fp = magic(Fp)

        coeffs = [Fp(1), Fp(2), Fp(3), Fp(4)]
        omega = Fp.primitive_element() ** 48  # This should be a proper root of unity in your field
        
        result = UniPolynomial.ntt_evals_from_coeffs(coeffs, 2, omega)
        
        # Calculate expected result using the definition of NTT
        expected = [reduce(lambda t, s: t * (omega ** x) + s, coeffs[::-1], Fp(0)) for x in range(0, 4)]
        
        self.assertEqual(result, expected)

    def test_ntt_coeffs_from_evals(self):
        from sage.all import GF
        from field import magic
        
        Fp = GF(193)
        Fp = magic(Fp)
        evals = [Fp(1), Fp(2), Fp(3), Fp(4)]
        omega = Fp.primitive_element() ** 48  # This should be a proper root of unity in your field
        
        result = UniPolynomial.ntt_coeffs_from_evals(evals, 2, omega, one=Fp(1))
        
        # Calculate expected result using the inverse NTT formula
        expected = UniPolynomial.ntt_evals_from_coeffs(result, 2, omega)
        
        self.assertEqual(evals, expected)

    def test_division_by_linear_divisor(self):
        p = UniPolynomial([5, 2, 3, 1])  # x^3 + 3x^2 + 2x + 5
        q, r = p.division_by_linear_divisor(1)
        self.assertEqual(q.coeffs, [6, 4, 1])  # x^2 + 2x
        self.assertEqual(r, 11)

    def test_construct_subproduct_tree(self):
        from sage.all import GF
        from field import magic

        Fp = magic(GF(193))
        domain = [Fp(1), Fp(2), Fp(3), Fp(4)]
        tree = UniPolynomial.construct_subproduct_tree_fix(domain)
        self.assertEqual(tree, {
            'poly': [Fp(24), Fp(143), Fp(35), Fp(183), 1],
            'children': ({
                'poly': [Fp(2), Fp(190), 1],
                'children': ({
                    'poly': [Fp(192), 1],
                    'children': None
                },
                {
                    'poly': [Fp(191), 1],
                    'children': None
                })
            },
            {
                'poly': [Fp(12), Fp(186), 1],
                'children': ({
                    'poly': [Fp(190), 1],
                    'children': None
                },
                {
                    'poly': [Fp(189), 1],
                    'children': None
                })
            })
        })

    def test_compute_eval(self):
        from sage.all import GF
        from field import magic

        Fp = magic(GF(193))
        domain = [Fp(1), Fp(2), Fp(3), Fp(4)]
        tree = UniPolynomial.construct_subproduct_tree_fix(domain)
        f = UniPolynomial([4, 3, 2, 1])  # x^3 + 2x^2 + 3x + 4
        evals = UniPolynomial.compute_eval_fix(tree, f.coeffs, domain)
        
        # Calculate expected evaluations manually
        expected = [f.evaluate(x) for x in domain]
        
        self.assertEqual(evals, expected)

    def test_compute_z_derivative(self):
        z = [1, 2, 3, 4]
        result = UniPolynomial.compute_z_derivative(z)
        self.assertEqual(result, [2, 6, 12])

    def test_uni_eval_from_evals(self):
        evals = [1, 8, 27, 64]
        domain = [1, 2, 3, 4]
        z = 5
        result = UniPolynomial.uni_eval_from_evals(evals, z, domain)
        self.assertEqual(result, 125)

if __name__ == '__main__':
    main()
