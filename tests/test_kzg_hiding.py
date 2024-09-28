import unittest
from random import randint
import sys
sys.path.append('../src')
sys.path.append('src')

from kzg_hiding import KZG10Commitment, UniPolynomial, DummyGroup, Field, Commitment

class TestKZG10Commitment(unittest.TestCase):
    def setUp(self):
        self.max_degree = 10
        self.hiding_bound = 3
        self.kzg = KZG10Commitment(DummyGroup(Field), DummyGroup(Field), self.max_degree, hiding_bound=self.hiding_bound, debug=True)

    def test_setup(self):
        params = self.kzg.setup()
        self.assertIn('powers_of_g', params)
        self.assertIn('powers_of_gamma_g', params)
        self.assertIn('h', params)
        self.assertIn('beta_h', params)
        self.assertIn('neg_powers_of_h', params)
        self.assertEqual(len(params['powers_of_g']), self.max_degree + 1)
        self.assertEqual(len(params['powers_of_gamma_g']), self.max_degree + 2)

    def test_commit(self):
        poly = UniPolynomial([randint(0, 100) for _ in range(5)])
        commitment, random_ints = self.kzg.commit(poly)
        self.assertIsInstance(commitment, Commitment)
        self.assertEqual(len(random_ints), self.hiding_bound + 1)

    def test_open(self):
        poly = UniPolynomial([randint(0, 100) for _ in range(5)])
        point = randint(0, 100)
        commitment, random_ints = self.kzg.commit(poly)
        proof = self.kzg.open(poly, point, random_ints)
        self.assertIn('w', proof)
        self.assertIn('random_v', proof)

    def test_check(self):
        poly = UniPolynomial([randint(0, 100) for _ in range(5)])
        point = randint(0, 100)
        commitment, random_ints = self.kzg.commit(poly)
        value = poly.evaluate(point)
        proof = self.kzg.open(poly, point, random_ints)
        self.assertTrue(self.kzg.check(commitment, point, value, proof))

    def test_check_invalid_proof(self):
        poly = UniPolynomial([randint(0, 100) for _ in range(5)])
        point = randint(0, 100)
        commitment, random_ints = self.kzg.commit(poly)
        value = poly.evaluate(point)
        invalid_proof = self.kzg.open(poly, point + 1, random_ints)  # Invalid point
        self.assertFalse(self.kzg.check(commitment, point, value, invalid_proof))

    def test_batch_check(self):
        num_polynomials = 5
        polynomials = [UniPolynomial([randint(0, 100) for _ in range(randint(5, 10))]) for _ in range(num_polynomials)]
        points = [randint(0, 100) for _ in range(num_polynomials)]
        
        commitments = []
        values = []
        proofs = []
        
        for p, point in zip(polynomials, points):
            comm, random_ints = self.kzg.commit(p)
            commitments.append(comm)
            values.append(p.evaluate(point))
            proofs.append(self.kzg.open(p, point, random_ints))
        
        self.assertTrue(self.kzg.batch_check(commitments, points, values, proofs))

    def test_batch_check_invalid_proof(self):
        num_polynomials = 5
        polynomials = [UniPolynomial([randint(0, 100) for _ in range(randint(5, 10))]) for _ in range(num_polynomials)]
        points = [randint(0, 100) for _ in range(num_polynomials)]
        
        commitments = []
        values = []
        proofs = []
        
        for p, point in zip(polynomials, points):
            comm, random_ints = self.kzg.commit(p)
            commitments.append(comm)
            values.append(p.evaluate(point))
            proofs.append(self.kzg.open(p, point, random_ints))
        
        # Invalidate one proof
        invalid_index = randint(0, num_polynomials - 1)
        proofs[invalid_index] = self.kzg.open(polynomials[invalid_index], points[invalid_index] + 1, random_ints)
        
        self.assertFalse(self.kzg.batch_check(commitments, points, values, proofs))

if __name__ == '__main__':
    unittest.main()
