import unittest

import sys

sys.path.append('../src')
sys.path.append('src')

from kzg10 import KZG10Commitment, Commitment
from group import DummyGroup
from unipolynomial import UniPolynomial
from sage.all import *
from field import magic

Fp = magic(GF(193))

class TestKZG10Commitment(unittest.TestCase):
    def setUp(self):
        self.G1 = DummyGroup(Fp)
        self.G2 = DummyGroup(Fp)
        self.max_degree = 10
        self.kzg = KZG10Commitment(self.G1, self.G2, self.max_degree)

    def test_setup(self):
        self.assertEqual(len(self.kzg.srs), self.max_degree + 1)
        self.assertEqual(len(self.kzg.srs2), self.max_degree + 1)
        self.assertIsNotNone(self.kzg.h)
        self.assertIsNotNone(self.kzg.h_s)

    def test_commit(self):
        poly = UniPolynomial([1, 2, 3])  # 1 + 2x + 3x^2
        commitment = self.kzg.commit(poly)
        self.assertIsInstance(commitment, Commitment)
        self.assertEqual(commitment.group, self.G1)

    def test_commit_invalid_type(self):
        with self.assertRaises(TypeError):
            self.kzg.commit("invalid")

    def test_commit_degree_too_high(self):
        poly = UniPolynomial([1] * (self.max_degree + 2))
        with self.assertRaises(ValueError):
            self.kzg.commit(poly)

    def test_division_by_linear_divisor(self):
        coeffs = [1, 2, 1]  # x^2 + 2x + 1
        d = 1
        quotient, remainder = KZG10Commitment.division_by_linear_divisor(coeffs, d)
        self.assertEqual(quotient, [3, 1])  # x + 3
        self.assertEqual(remainder, 4)  # f(1) = 1^2 + 2*1 + 1 = 4

    def test_prove_eval(self):
        poly = [1, 2, 3]  # 1 + 2x + 3x^2
        point = 2
        value = 17  # f(2) = 1 + 2*2 + 3*2^2 = 17
        proof = self.kzg.prove_eval(poly, point, value)
        self.assertIsInstance(proof, Commitment)

    def test_verify_eval(self):
        poly = [1, 2, 3]  # 1 + 2x + 3x^2
        point = 2
        value = 17  # f(2) = 1 + 2*2 + 3*2^2 = 17
        commitment = self.kzg.commit(poly)
        proof = self.kzg.prove_eval(poly, point, value)
        result = self.kzg.verify_eval(commitment, proof, point, value)
        self.assertTrue(result)

    def test_prove_degree_bound(self):
        poly = [1, 2, 3, 0, 0]  # 1 + 2x + 3x^2
        commitment = self.kzg.commit(poly)
        degree_bound = 3
        proof = self.kzg.prove_degree_bound(commitment, poly, degree_bound)
        self.assertIsInstance(proof[0], Commitment)
        self.assertIsInstance(proof[1], int)

    def test_verify_degree_bound(self):
        poly = [1, 2, 3, 0, 0]  # 1 + 2x + 3x^2
        commitment = self.kzg.commit(poly)
        degree_bound = 3
        proof = self.kzg.prove_degree_bound(commitment, poly, degree_bound)
        result = self.kzg.verify_degree_bound(commitment, proof, degree_bound)
        self.assertTrue(result)

    def test_prove_eval_and_degree(self):
        poly = [1, 2, 3, 0, 0]  # 1 + 2x + 3x^2
        commitment = self.kzg.commit(poly)
        point = 2
        value = 17  # f(2) = 1 + 2*2 + 3*2^2 = 17
        degree_bound = 3
        proof = self.kzg.prove_eval_and_degree(commitment, poly, point, value, degree_bound)
        self.assertIsInstance(proof[0], Commitment)
        self.assertIsInstance(proof[1], int)

    def test_verify_eval_and_degree(self):
        poly = [1, 2, 3, 0, 0]  # 1 + 2x + 3x^2
        commitment = self.kzg.commit(poly)
        point = 2
        value = 17  # f(2) = 1 + 2*2 + 3*2^2 = 17
        degree_bound = 3
        proof = self.kzg.prove_eval_and_degree(commitment, poly, point, value, degree_bound)
        result = self.kzg.verify_eval_and_degree(commitment, proof, point, value, degree_bound)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
