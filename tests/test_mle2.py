import unittest
from sage.all import GF
import sys

sys.path.append('../src')
sys.path.append('src')

from mle2 import MLEPolynomial, pow_2

# Assuming Fp is defined in your original file, if not, you may need to import or define it here
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
        self.assertEqual(len(mle.evals), 4)

    def test_ntt_core(self):
        vs = [Fp(1), Fp(2), Fp(3), Fp(4)]
        result = MLEPolynomial.ntt_core(vs, Fp(1))
        self.assertEqual(len(result), 4)

    def test_compute_evals_from_coeffs(self):
        coeffs = [Fp(1), Fp(2), Fp(3), Fp(4)]
        evals = MLEPolynomial.compute_evals_from_coeffs(coeffs)
        self.assertEqual(len(evals), 4)

    def test_compute_coeffs_from_evals(self):
        evals = [Fp(1), Fp(2), Fp(3), Fp(4)]
        coeffs = MLEPolynomial.compute_coeffs_from_evals(evals)
        self.assertEqual(len(coeffs), 4)

    def test_evaluate(self):
        evals = [Fp(1), Fp(2), Fp(3), Fp(4)]
        mle = MLEPolynomial(evals, 2)
        result = mle.evaluate([Fp(1), Fp(2)])
        # self.assertIsInstance(result, Fp)

    def test_evaluate_from_coeffs(self):
        coeffs = [Fp(1), Fp(2), Fp(3), Fp(4)]
        result = MLEPolynomial.evaluate_from_coeffs(coeffs, [Fp(1), Fp(2)])
        # self.assertIsInstance(result, Fp)

    def test_eval_from_coeffs(self):
        coeffs = [Fp(1), Fp(2), Fp(3), Fp(4)]
        result = MLEPolynomial.eval_from_coeffs(coeffs, Fp(2))
        # self.assertIsInstance(result, Fp)

    def test_decompose_by_div(self):
        evals = [Fp(i) for i in range(8)]
        mle = MLEPolynomial(evals, 3)
        point = [Fp(1), Fp(2), Fp(3)]
        quotients, remainder = mle.decompose_by_div(point)
        self.assertEqual(len(quotients), 3)
        # self.assertIsInstance(remainder, Fp)

    def test_decompose_by_div_from_coeffs(self):
        coeffs = [Fp(i) for i in range(8)]
        point = [Fp(1), Fp(2), Fp(3)]
        quotients, remainder = MLEPolynomial.decompose_by_div_from_coeffs(coeffs, point)
        self.assertEqual(len(quotients), 3)
        # self.assertIsInstance(remainder, Fp)

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