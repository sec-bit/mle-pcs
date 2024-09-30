import unittest
from sage.all import GF
import sys

sys.path.append('../src')
sys.path.append('src')

from mle2 import MLEPolynomial
from utils import bits_le_with_width

Fp = GF(2**64 - 2**32 + 1)

class TestMLEPolynomial(unittest.TestCase):

    def test_init(self):
        evals = [Fp(1), Fp(2), Fp(3), Fp(4)]
        mle = MLEPolynomial(evals, 2)
        self.assertEqual(mle.evals, evals)
        self.assertEqual(mle.num_var, 2)

    def test_from_coeffs(self):
        coeffs = [Fp(1), Fp(2), Fp(3), Fp(4)]
        mle = MLEPolynomial.from_coeffs(coeffs, 2)
        self.assertEqual(mle.evals, MLEPolynomial.compute_evals_from_coeffs(coeffs))

    def test_ntt_core(self):
        vs = [Fp(1), Fp(2), Fp(3), Fp(4)]
        result = MLEPolynomial.ntt_core(vs, Fp(1))
        self.assertEqual(result, [MLEPolynomial(vs, 2).evaluate(bits_le_with_width(x, 2)) for x in range(4)])
        self.assertEqual(vs, MLEPolynomial.ntt_core(result, -1))

    def test_compute_evals_from_coeffs(self):
        coeffs = [Fp(1), Fp(2), Fp(3), Fp(4)]
        evals = MLEPolynomial.compute_evals_from_coeffs(coeffs)
        self.assertEqual(evals, [MLEPolynomial(coeffs, 2).evaluate(bits_le_with_width(x, 2)) for x in range(4)])

    def test_compute_coeffs_from_evals(self):
        evals = [Fp(1), Fp(2), Fp(3), Fp(4)]
        coeffs = MLEPolynomial.compute_coeffs_from_evals(evals)
        self.assertEqual(evals, [MLEPolynomial(coeffs, 2).evaluate(bits_le_with_width(x, 2)) for x in range(4)])

    def test_evaluate(self):
        evals = [Fp(1), Fp(2), Fp(3), Fp(4)]
        mle = MLEPolynomial(evals, 2)
        result = mle.evaluate([Fp(1), Fp(2)])
        self.assertEqual(result, MLEPolynomial.evaluate_from_evals(evals, [Fp(1), Fp(2)]))

    def test_evaluate_from_coeffs(self):
        coeffs = [Fp(1), Fp(2), Fp(3), Fp(4)]
        result = MLEPolynomial.evaluate_from_coeffs(coeffs, [Fp(1), Fp(2)])
        self.assertEqual(result, MLEPolynomial.evaluate_from_evals(MLEPolynomial.compute_evals_from_coeffs(coeffs), [Fp(1), Fp(2)]))

    def test_decompose_by_div(self):
        evals = [i for i in range(8)]
        mle = MLEPolynomial(evals, 3)
        point = [1, 2, 3]
        k = len(point)
        quotients, remainder = mle.decompose_by_div(point)
        remainder = MLEPolynomial([remainder], 0)
        for i in range(k):
            remainder = MLEPolynomial.mul_quotients(quotients[i], remainder, point[i])
        self.assertEqual(remainder.evals, mle.evals)

    def test_decompose_by_div_from_coeffs(self):
        coeffs = [Fp(i) for i in range(8)]
        point = [Fp(1), Fp(2), Fp(3)]
        evals = MLEPolynomial.compute_evals_from_coeffs(coeffs[:])
        self.assertEqual(evals, [0, 1, 2, 6, 4, 10, 12, 28])
        quotients, remainder = MLEPolynomial(evals, 3).decompose_by_div(point)
        quotients = [MLEPolynomial.compute_coeffs_from_evals(q.evals) for q in quotients]
        self.assertEqual((quotients, remainder), MLEPolynomial.decompose_by_div_from_coeffs(coeffs, point))

    def test_eq_poly_vec(self):
        point = [Fp(i) for i in range(4)]
        res1 = MLEPolynomial.eqs_over_hypercube(point)
        res2 = MLEPolynomial.eqs_over_hypercube_slow(4, point)
        self.assertEqual(res1, res2)

    def evaluate_from_evals(self):
        point = [Fp(i) for i in range(4)]
        evals = [Fp(i) for i in range(16)]
        res1 = MLEPolynomial.evaluate_from_evals(evals, point)
        res2 = MLEPolynomial.evaluate_from_evals_2(evals, point)
        self.assertEqual(res1, res2)

if __name__ == '__main__':
    unittest.main()