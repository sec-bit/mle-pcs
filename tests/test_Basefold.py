from unittest import TestCase, main
from random import randint
import sys

sys.path.append('../src')
sys.path.append('src')

import Basefold
from merlin.merlin_transcript import MerlinTranscript
from merkle import MerkleTree
from mle2 import MLEPolynomial
from unipolynomial import UniPolynomial
from utils import log_2, query_num, delta_uni_decoding

class BasefoldTest(TestCase):
    def test_rep_encode(self):
        self.assertEqual(Basefold.rep_encode([1, 2], 2, 2), [1, 2, 1, 2])
        self.assertEqual(Basefold.rep_encode([1, 2, 3, 4], 2, 3), [1, 2, 1, 2, 1, 2, 3, 4, 3, 4, 3, 4])
        
    def test_rep_encode_invalid_input(self):
        with self.assertRaises(AssertionError):
            Basefold.rep_encode([1, 2], 0, 2)
        
        with self.assertRaises(AssertionError):
            Basefold.rep_encode([1, 2], 2, 0)
        
        with self.assertRaises(AssertionError):
            Basefold.rep_encode([1, 2], -1, 2)
        
        with self.assertRaises(AssertionError):
            Basefold.rep_encode([1, 2], 2, -1)

    def test_rs_encode_single(self):
        m = [1, 2, 3]
        alpha = [0, 1, 2, 3, 4, 5]
        c = 2
        result = Basefold.rs_encode_single(m, alpha, c)
        self.assertEqual(result, [1, 6, 17, 34, 57, 86])

    def test_rs_encode(self):
        m = [1, 2, 3, 4, 5, 6]
        k0 = 3
        c = 2
        result = Basefold.rs_encode(m, k0, c)
        self.assertEqual(result, [1, 6, 17, 34, 57, 86, 4, 15, 38, 73, 120, 179])

    def test_basefold_encode(self):
        m = [1, 2, 3, 4]
        k0 = 2
        depth = 1
        c = 2
        T = [[1, 2, 3, 4]]
        result = Basefold.basefold_encode(m, k0, depth, c, T)
        self.assertEqual(result, [4, 10, 10, 18, -2, -6, -8, -14])

    def test_query_phase(self):
        num_vars = 10
        transcript = MerlinTranscript(b"test")
        first_oracle = [randint(0, 100) for _ in range(2 ** num_vars)]
        first_tree = MerkleTree(first_oracle)
        oracles = []
        trees = []
        num_vars_copy = num_vars - 1
        while num_vars_copy > 0:
            oracles.append([randint(0, 100) for _ in range(2 ** num_vars_copy)])
            trees.append(MerkleTree(oracles[-1]))
            num_vars_copy -= 1
        blowup_factor = 8
        security_bits = 128
        num_verifier_queries = query_num(blowup_factor, security_bits, delta_uni_decoding)
        query_paths, merkle_paths = Basefold.query_phase(transcript, first_tree, first_oracle, trees, oracles, num_vars, num_verifier_queries)
        self.assertEqual(len(query_paths), num_verifier_queries)
        self.assertEqual(len(merkle_paths), num_verifier_queries)

    def test_basefold(self):
        num_vars = 10
        blowup_factor = 8
        security_bits = 128
        depth = num_vars
        k = depth
        num_verifier_queries = query_num(blowup_factor, security_bits, delta_uni_decoding)
        us = [randint(0, 100) for _ in range(num_vars)]
        f_evals = [randint(0, 100) for _ in range(2 ** num_vars)]
        v = MLEPolynomial.evaluate_from_evals(f_evals, us)

        params = {
            'num_vars': num_vars,
            'blowup_factor': blowup_factor,
            'depth': depth,
            'k': k,
            'num_verifier_queries': num_verifier_queries,
            'us': us,
            'f_evals': f_evals,
            'v': v
        }
        # print(f'{i}th test, params:{params}')

        T = []
        cnt = 0
        k0 = 2 ** (num_vars - depth)
        for i in range(depth):
            T.append([randint(1, 100) for j in range(k0 * blowup_factor * 2 ** i)])
            cnt += len(T[-1])

        f_code = Basefold.basefold_encode(m=f_evals, k0=k0, depth=depth, c=blowup_factor, T=T, G0=Basefold.rs_encode)
        commit = MerkleTree(f_code)
        
        transcript = MerlinTranscript(b"verify queries")
        transcript.append_message(b"commit.root", bytes(commit.root, 'ascii'))
        proof = Basefold.prove_basefold_evaluation_arg_multilinear_basis(f_code, f_evals, us, v, k, k0, T, blowup_factor, commit, num_verifier_queries, transcript)
        self.assertTrue(Basefold.verify_basefold_evaluation_arg_multilinear_basis(2 ** num_vars * blowup_factor, commit, proof, us, v, 2, k, T, blowup_factor, num_verifier_queries))

    def test_basefold_fri_monomial_basis(self):
        UniPolynomial.scalar_constructor = lambda x: x
        table = [randint(1, 100) for _ in range(10)]
        coeffs = [randint(0, 100) for _ in range(2)]
        vs = [UniPolynomial(coeffs).evaluate(x) for x in table + [-x for x in table]]
        alpha = randint(0, 100)
        result = Basefold.basefold_fri_monomial_basis(vs, table, alpha)
        eval = coeffs[0] + alpha * coeffs[1]
        for e in result:
            self.assertEqual(e, eval)

    def test_basefold_fri_multilinear_basis(self):
        table = [randint(1, 100) for _ in range(10)]
        coeffs = [randint(0, 100) for _ in range(2)]
        vs = [UniPolynomial(coeffs).evaluate(x) for x in table + [-x for x in table]]
        c = randint(0, 100)
        result = Basefold.basefold_fri_multilinear_basis(vs, table, c)
        eval = (1 - c) * coeffs[0] + c * coeffs[1]
        for e in result:
            self.assertEqual(e, eval)


if __name__ == '__main__':
    main()
