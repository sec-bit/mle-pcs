from unittest import TestCase, main
from random import randint
import sys

sys.path.append('../src')
sys.path.append('src')

from basefold_pcs import FoldableCoder, FoldableRSCoder, BASEFOLD_PCS, Fp
from curve import BN128_CURVE_ORDER
from utils import log_2
from mle2 import MLEPolynomial
from merlin.merlin_transcript import MerlinTranscript

def matrix_concat(A, B, column_equal=True):
    assert len(A) == len(B), f"A and B must have the same number of rows, {len(A)} != {len(B)}"
    assert not column_equal or len(A[0]) == len(B[0]), f"A and B must have the same number of columns, {len(A[0])} != {len(B[0])}"
    return [A[i] + B[i] for i in range(len(A))]

def columns_mul(matrix, scalars):
    assert len(matrix[0]) == len(scalars), f"Matrix and scalars must have the same number of columns, {len(matrix[0])} != {len(scalars)}"
    new_matrix = []
    for i in range(len(matrix)):
        new_row = []
        for j in range(len(matrix[i])):
            new_row.append(matrix[i][j] * scalars[j])
        new_matrix.append(new_row)
    return new_matrix

def vec_mul_matrix(vec, matrix):
    assert isinstance(vec, list) or isinstance(vec, tuple)
    assert isinstance(matrix, list) or isinstance(matrix, tuple)
    assert isinstance(matrix[0], list) or isinstance(matrix[0], tuple)
    assert len(vec) == len(matrix), "Vector and matrix must have the same length"
    return [sum([vec[i] * matrix[i][j] for i in range(len(vec))]) for j in range(len(matrix[0]))]

def nth_root_of_unity(log_n):
    return Fp.multiplicative_generator() ** (BN128_CURVE_ORDER // (2 ** log_n))

def rscode_matrix(log_n, log_blowup):
    omega = nth_root_of_unity(log_n + log_blowup)
    return [[omega ** (i * j) for j in range(2 ** (log_n + log_blowup))] for i in range(2 ** log_n)]

def derive_Gs(G0, depth, table):
    Gs = [G0]
    for i in range(depth):
        G_last = Gs[-1]
        n = len(G_last[0]) * 2
        G_up = matrix_concat(G_last, G_last)
        G_down_left = columns_mul(G_last, table[log_2(n)][:n // 2])
        G_down_right = columns_mul(G_last, table[log_2(n)][n // 2:])
        G_down = matrix_concat(G_down_left, G_down_right)
        Gs.append(G_up + G_down)
    return Gs

class BasefoldPCSTest(TestCase):
    def setUp(self) -> None:
        return super().setUp()
    
    '''
    Test FoldableCoder
    '''
    
    def test_setup_tables(self):
        table = FoldableCoder.setup_tables(k0=2, c=4, depth=5)
        self.assertEqual(len(table), 9)
        self.assertEqual(len(table[0]), 1)
        self.assertEqual(len(table[1]), 2)
        self.assertEqual(len(table[2]), 4)
        self.assertEqual(len(table[3]), 8)
        self.assertEqual(len(table[4]), 16)
        self.assertEqual(len(table[5]), 32)
        self.assertEqual(len(table[6]), 64)
        self.assertEqual(len(table[7]), 128)
        self.assertEqual(len(table[8]), 256)

    def test_rep_encode(self):
        k0 = 16
        c = 2
        n = k0
        m = [Fp.random() for _ in range(n)]
        encoded = FoldableCoder.rep_encode(m, k0, c)
        self.assertEqual(len(encoded), n * c)
        for i in range(0, n, k0):
            for j in range(c):
                for k in range(k0):
                    self.assertEqual(encoded[i * c + j * k0 + k], m[i + k], f"i = {i}, j = {j}, k = {k}")

    def test_encode(self):
        k0 = 4
        c = 2
        n = 16
        m = [Fp.random() for _ in range(n)]
        assert n % k0 == 0
        depth = log_2(n // k0)
        G0 = [[Fp.random() for _ in range(k0 * c // 2)] for _ in range(k0)]
        for i in range(k0):
            G0[i] += [-e for e in G0[i]]
        assert len(G0) == k0
        assert len(G0[0]) == k0 * c
        coder = FoldableCoder(k0, c, depth, G0=lambda m, k0, c: vec_mul_matrix(m, G0))
        table = coder.tables
        Gs = derive_Gs(G0, depth, table)
        G_last = Gs[-1]
        assert len(G_last) == n, f"len(G_last) != n, {len(G_last)} != {n}"
        assert len(G_last[0]) == n * c, f"len(G_last[0]) != n * c, {len(G_last[0])} != {n * c}"
        encoded = coder.encode(m)
        expected = vec_mul_matrix(m, G_last)
        assert len(encoded) == len(expected)
        self.assertListEqual(encoded, expected, f"encoded != expected, {encoded} != {expected}")

    '''
    Test FoldableRSCoder
    '''

    def test_rs_encode(self):
        k0 = 16
        c = 2
        n = k0
        m = [Fp.random() for _ in range(n)]
        encoded = FoldableRSCoder.rs_encode(m, k0, c)
        self.assertEqual(len(encoded), n * c)

        rs_matrix = rscode_matrix(log_2(n), log_2(c))
        expected = vec_mul_matrix(m, rs_matrix)
        self.assertListEqual(encoded, expected, f"encoded != expected, {encoded} != {expected}")

    def test_rs_tables(self):
        k0 = 16
        c = 2
        depth = 5
        table = FoldableRSCoder.setup_rs_tables(k0, c, depth)
        self.assertEqual(len(table), depth + log_2(k0 * c) + 1)
        for i in range(depth + log_2(k0 * c) + 1):
            self.assertEqual(len(table[i]), 2 ** i)

            omega = nth_root_of_unity(i)
            for j in range(2 ** i):
                self.assertEqual(table[i][j], omega ** j)

    '''
    Test BASEFOLD_PCS
    '''

    def test_fold_with_multilinear_basis(self):
        k0 = 4
        c = 2
        n = 16
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableCoder(k0, c, log_2(n // k0)))
        r = Fp.random()
        folded = pcs.fold_with_multilinear_basis(m, r)
        self.assertEqual(len(folded), n // 2)
        two = Fp(2)
        for i in range(n // 2):
            fe = (m[i] + m[i + n // 2]) / two
            fo = (m[i] - m[i + n // 2]) / (two * pcs.encoder.tables[log_2(n)][i])
            self.assertEqual(folded[i], (1 - r) * fe + r * fo)

    def test_fold_with_multilinear_basis_rs(self):
        k0 = 4
        c = 2
        n = 16
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableRSCoder(k0, c, log_2(n // k0)))
        r = Fp.random()
        folded = pcs.fold_with_multilinear_basis(m, r)
        self.assertEqual(len(folded), n // 2)
        two = Fp(2)
        for i in range(n // 2):
            fe = (m[i] + m[i + n // 2]) / two
            fo = (m[i] - m[i + n // 2]) / (two * pcs.encoder.tables[log_2(n)][i])
            self.assertEqual(folded[i], (1 - r) * fe + r * fo)

    def test_fold_with_monomial_basis(self):
        k0 = 4
        c = 2
        n = 16
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableCoder(k0, c, log_2(n // k0)))
        r = Fp.random()
        folded = pcs.fold_with_monomial_basis(m, r)
        self.assertEqual(len(folded), n // 2)
        two = Fp(2)
        for i in range(n // 2):
            fe = (m[i] + m[i + n // 2]) / two
            fo = (m[i] - m[i + n // 2]) / (two * pcs.encoder.tables[log_2(n)][i])
            self.assertEqual(folded[i], fe + r * fo)

    def test_fold_with_monomial_basis_rs(self):
        k0 = 4
        c = 2
        n = 16
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableRSCoder(k0, c, log_2(n // k0)))
        r = Fp.random()
        folded = pcs.fold_with_monomial_basis(m, r)
        self.assertEqual(len(folded), n // 2)
        two = Fp(2)
        for i in range(n // 2):
            fe = (m[i] + m[i + n // 2]) / two
            fo = (m[i] - m[i + n // 2]) / (two * pcs.encoder.tables[log_2(n)][i])
            self.assertEqual(folded[i], fe + r * fo)

    def test_commit(self):
        k0 = 4
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableCoder(k0, c, depth))
        f_mle = MLEPolynomial(m, log_2(n))
        pcs.commit(f_mle)

    def test_commit_rs(self):
        k0 = 4
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableRSCoder(k0, c, depth))
        f_mle = MLEPolynomial(m, log_2(n))
        pcs.commit(f_mle)

    def test_commit_fail_1(self):
        k0 = 4
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n * 2)]
        pcs = BASEFOLD_PCS(FoldableCoder(k0, c, depth))
        f_mle = MLEPolynomial(m, log_2(n) + 1)
        with self.assertRaises(AssertionError):
            pcs.commit(f_mle)

    def test_commit_fail_1_rs(self):
        k0 = 4
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n * 2)]
        pcs = BASEFOLD_PCS(FoldableRSCoder(k0, c, depth))
        f_mle = MLEPolynomial(m, log_2(n) + 1)
        with self.assertRaises(AssertionError):
            pcs.commit(f_mle)

    def test_commit_fail_2(self):
        k0 = 4
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random()]
        pcs = BASEFOLD_PCS(FoldableCoder(k0, c, depth))
        f_mle = MLEPolynomial(m, 0)
        with self.assertRaises(AssertionError):
            pcs.commit(f_mle)

    def test_commit_fail_2_rs(self):
        k0 = 4
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random()]
        pcs = BASEFOLD_PCS(FoldableRSCoder(k0, c, depth))
        f_mle = MLEPolynomial(m, 0)
        with self.assertRaises(AssertionError):
            pcs.commit(f_mle)

    def test_commit_fail_3(self):
        k0 = 1
        c = 2
        n = 1
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableCoder(k0, c, depth))
        with self.assertRaises(AssertionError):
            pcs.commit(MLEPolynomial(m, log_2(n)))

    def test_commit_fail_3_rs(self):
        k0 = 1
        c = 2
        n = 1
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableRSCoder(k0, c, depth))
        with self.assertRaises(AssertionError):
            pcs.commit(MLEPolynomial(m, log_2(n)))

    def test_commit_fail_4(self):
        k0 = 4
        c = 2
        n = 1
        depth = 1
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableCoder(k0, c, depth))
        with self.assertRaises(AssertionError):
            pcs.commit(MLEPolynomial(m, log_2(n)))

    def test_commit_fail_4_rs(self):
        k0 = 4
        c = 2
        n = 1
        depth = 1
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableRSCoder(k0, c, depth))
        with self.assertRaises(AssertionError):
            pcs.commit(MLEPolynomial(m, log_2(n)))

    def test_prove_eval(self):
        k0 = 1
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableCoder(k0, c, depth))
        comm = pcs.commit(MLEPolynomial(m, log_2(n)))
        tr = MerlinTranscript(b"test_basefold_pcs")
        us = [Fp.random() for _ in range(log_2(n))]
        f_mle = MLEPolynomial(m, log_2(n))
        v, arg = pcs.prove_eval(comm, f_mle, us, tr.fork(b"fork"))
        self.assertEqual(v, f_mle.evaluate(us), f"v != f_mle.evaluate(us), {v} != {f_mle.evaluate(us)}")

    def test_prove_eval_rs(self):
        k0 = 1
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableRSCoder(k0, c, depth))
        comm = pcs.commit(MLEPolynomial(m, log_2(n)))
        tr = MerlinTranscript(b"test_basefold_pcs")
        us = [Fp.random() for _ in range(log_2(n))]
        f_mle = MLEPolynomial(m, log_2(n))
        v, arg = pcs.prove_eval(comm, f_mle, us, tr.fork(b"fork"))
        self.assertEqual(v, f_mle.evaluate(us), f"v != f_mle.evaluate(us), {v} != {f_mle.evaluate(us)}")

    def test_prove_eval_no_blowup(self):
        k0 = 1
        c = 1
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        with self.assertRaises(AssertionError): # blowup_factor must be greater than 1
            BASEFOLD_PCS(FoldableCoder(k0, c, depth))

    def test_prove_eval_no_blowup_rs(self):
        k0 = 1
        c = 1
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        with self.assertRaises(AssertionError): # blowup_factor must be greater than 1
            BASEFOLD_PCS(FoldableRSCoder(k0, c, depth))

    def test_prove_eval_k0_1(self):
        k0 = 1
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableCoder(k0, c, depth))
        comm = pcs.commit(MLEPolynomial(m, log_2(n)))
        tr = MerlinTranscript(b"test_basefold_pcs")
        us = [Fp.random() for _ in range(log_2(n))]
        f_mle = MLEPolynomial(m, log_2(n))
        v, arg = pcs.prove_eval(comm, f_mle, us, tr.fork(b"fork"))
        self.assertEqual(v, f_mle.evaluate(us), f"v != f_mle.evaluate(us), {v} != {f_mle.evaluate(us)}")

    def test_prove_eval_k0_1_rs(self):
        k0 = 1
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableRSCoder(k0, c, depth))
        comm = pcs.commit(MLEPolynomial(m, log_2(n)))
        tr = MerlinTranscript(b"test_basefold_pcs")
        us = [Fp.random() for _ in range(log_2(n))]
        f_mle = MLEPolynomial(m, log_2(n))
        v, arg = pcs.prove_eval(comm, f_mle, us, tr.fork(b"fork"))
        self.assertEqual(v, f_mle.evaluate(us), f"v != f_mle.evaluate(us), {v} != {f_mle.evaluate(us)}")

    def test_verify_eval(self):
        k0 = 1
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableCoder(k0, c, depth))
        comm = pcs.commit(MLEPolynomial(m, log_2(n)))
        tr = MerlinTranscript(b"test_basefold_pcs")
        us = [Fp.random() for _ in range(log_2(n))]
        f_mle = MLEPolynomial(m, log_2(n))
        v, arg = pcs.prove_eval(comm, f_mle, us, tr.fork(b"fork"))
        self.assertEqual(v, f_mle.evaluate(us), f"v != f_mle.evaluate(us), {v} != {f_mle.evaluate(us)}")
        self.assertTrue(pcs.verify_eval(comm, us, v, arg, tr.fork(b"fork")))

    def test_verify_eval_rs(self):
        k0 = 1
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableRSCoder(k0, c, depth))
        comm = pcs.commit(MLEPolynomial(m, log_2(n)))
        tr = MerlinTranscript(b"test_basefold_pcs")
        us = [Fp.random() for _ in range(log_2(n))]
        f_mle = MLEPolynomial(m, log_2(n))
        v, arg = pcs.prove_eval(comm, f_mle, us, tr.fork(b"fork"))
        self.assertEqual(v, f_mle.evaluate(us), f"v != f_mle.evaluate(us), {v} != {f_mle.evaluate(us)}")
        self.assertTrue(pcs.verify_eval(comm, us, v, arg, tr.fork(b"fork")))

    def test_verify_eval_fail_1(self):
        k0 = 1
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableCoder(k0, c, depth))
        comm = pcs.commit(MLEPolynomial(m, log_2(n)))
        tr = MerlinTranscript(b"test_basefold_pcs")
        us = [Fp.random() for _ in range(log_2(n))]
        f_mle = MLEPolynomial(m, log_2(n))
        v, arg = pcs.prove_eval(comm, f_mle, us, tr.fork(b"fork"))
        v = Fp.random()
        self.assertNotEqual(v, f_mle.evaluate(us), f"v != f_mle.evaluate(us), {v} != {f_mle.evaluate(us)}")
        with self.assertRaises(AssertionError):
            pcs.verify_eval(comm, us, v, arg, tr.fork(b"fork"))

    def test_verify_eval_fail_1_rs(self):
        k0 = 1
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableRSCoder(k0, c, depth))
        comm = pcs.commit(MLEPolynomial(m, log_2(n)))
        tr = MerlinTranscript(b"test_basefold_pcs")
        us = [Fp.random() for _ in range(log_2(n))]
        f_mle = MLEPolynomial(m, log_2(n))
        v, arg = pcs.prove_eval(comm, f_mle, us, tr.fork(b"fork"))
        v = Fp.random()
        self.assertNotEqual(v, f_mle.evaluate(us), f"v != f_mle.evaluate(us), {v} != {f_mle.evaluate(us)}")
        with self.assertRaises(AssertionError):
            pcs.verify_eval(comm, us, v, arg, tr.fork(b"fork"))

    def test_verify_eval_fail_2(self):
        k0 = 1
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableCoder(k0, c, depth))
        comm = pcs.commit(MLEPolynomial(m, log_2(n)))
        comm.root = 0
        tr = MerlinTranscript(b"test_basefold_pcs")
        us = [Fp.random() for _ in range(log_2(n))]
        f_mle = MLEPolynomial(m, log_2(n))
        v, arg = pcs.prove_eval(comm, f_mle, us, tr.fork(b"fork"))
        self.assertEqual(v, f_mle.evaluate(us), f"v != f_mle.evaluate(us), {v} != {f_mle.evaluate(us)}")
        with self.assertRaises(AssertionError):
            pcs.verify_eval(comm, us, v, arg, tr.fork(b"fork"))

    def test_verify_eval_fail_2_rs(self):
        k0 = 1
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableRSCoder(k0, c, depth))
        comm = pcs.commit(MLEPolynomial(m, log_2(n)))
        comm.root = 0
        tr = MerlinTranscript(b"test_basefold_pcs")
        us = [Fp.random() for _ in range(log_2(n))]
        f_mle = MLEPolynomial(m, log_2(n))
        v, arg = pcs.prove_eval(comm, f_mle, us, tr.fork(b"fork"))
        self.assertEqual(v, f_mle.evaluate(us), f"v != f_mle.evaluate(us), {v} != {f_mle.evaluate(us)}")
        with self.assertRaises(AssertionError):
            pcs.verify_eval(comm, us, v, arg, tr.fork(b"fork"))

    def test_verify_eval_fail_3(self):
        k0 = 1
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableCoder(k0, c, depth))
        comm = pcs.commit(MLEPolynomial(m, log_2(n)))
        tr = MerlinTranscript(b"test_basefold_pcs")
        us = [Fp.random() for _ in range(log_2(n))]
        f_mle = MLEPolynomial(m, log_2(n))
        v, arg = pcs.prove_eval(comm, f_mle, us, tr.fork(b"fork"))
        arg['final_constant'] = Fp.random()
        self.assertEqual(v, f_mle.evaluate(us), f"v != f_mle.evaluate(us), {v} != {f_mle.evaluate(us)}")
        with self.assertRaises(AssertionError):
            pcs.verify_eval(comm, us, v, arg, tr.fork(b"fork"))

    def test_verify_eval_fail_3_rs(self):
        k0 = 1
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableRSCoder(k0, c, depth))
        comm = pcs.commit(MLEPolynomial(m, log_2(n)))
        tr = MerlinTranscript(b"test_basefold_pcs")
        us = [Fp.random() for _ in range(log_2(n))]
        f_mle = MLEPolynomial(m, log_2(n))
        v, arg = pcs.prove_eval(comm, f_mle, us, tr.fork(b"fork"))
        arg['final_constant'] = Fp.random()
        self.assertEqual(v, f_mle.evaluate(us), f"v != f_mle.evaluate(us), {v} != {f_mle.evaluate(us)}")
        with self.assertRaises(AssertionError):
            pcs.verify_eval(comm, us, v, arg, tr.fork(b"fork"))

    def test_verify_eval_fail_4(self):
        k0 = 1
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableCoder(k0, c, depth))
        comm = pcs.commit(MLEPolynomial(m, log_2(n)))
        tr = MerlinTranscript(b"test_basefold_pcs")
        us = [Fp.random() for _ in range(log_2(n))]
        f_mle = MLEPolynomial(m, log_2(n))
        v, arg = pcs.prove_eval(comm, f_mle, us, tr.fork(b"fork"))
        self.assertEqual(v, f_mle.evaluate(us), f"v != f_mle.evaluate(us), {v} != {f_mle.evaluate(us)}")
        us = us[:-1]
        with self.assertRaises(AssertionError):
            pcs.verify_eval(comm, us, v, arg, tr.fork(b"fork"))

    def test_verify_eval_fail_4_rs(self):
        k0 = 1
        c = 2
        n = 16
        depth = log_2(n // k0)
        m = [Fp.random() for _ in range(n)]
        pcs = BASEFOLD_PCS(FoldableRSCoder(k0, c, depth))
        comm = pcs.commit(MLEPolynomial(m, log_2(n)))
        tr = MerlinTranscript(b"test_basefold_pcs")
        us = [Fp.random() for _ in range(log_2(n))]
        f_mle = MLEPolynomial(m, log_2(n))
        v, arg = pcs.prove_eval(comm, f_mle, us, tr.fork(b"fork"))
        self.assertEqual(v, f_mle.evaluate(us), f"v != f_mle.evaluate(us), {v} != {f_mle.evaluate(us)}")
        us = us[:-1]
        with self.assertRaises(AssertionError):
            pcs.verify_eval(comm, us, v, arg, tr.fork(b"fork"))


if __name__ == "__main__":
    main()
