from unittest import TestCase, main
import sys

sys.path.append('../src')
sys.path.append('src')

from batch_fri import BatchFRI
from unipolynomial import UniPolynomial

class TestBatchFRI(TestCase):
    def setUp(self):
        # Set up a scalar field for testing (e.g., integers modulo a prime)
        prime = 193  # A small prime for testing
        UniPolynomial.set_scalar(int, lambda x: x % prime)

    def test_batch_commit(self):
        from sage.all import GF
        from field import magic
        from random import randint

        Fp = magic(GF(193))
        num_evals = 4
        evals = [[Fp(randint(0, 193)) for _ in range(1 << i)] for i in range(num_evals)]
        evals = list(reversed(evals))
        rate = 4
        gen = Fp.primitive_element() ** (192 // ((1 << (num_evals - 1)) * rate))
        domains = [[gen ** (i * (1 << j)) for i in range(len(evals[j]) * rate)] for j in range(len(evals))]
        _ = BatchFRI.batch_commit(evals, rate, domains, debug=False)

    def test_batch_prove(self):
        from sage.all import GF
        from field import magic
        from random import randint
        from merlin.merlin_transcript import MerlinTranscript

        Fp = magic(GF(193))
        num_evals = 4
        evals = [[Fp(randint(0, 193)) for _ in range(1 << i)] for i in range(num_evals)]
        # in descending order
        evals = list(reversed(evals))
        rate = 4
        gen = Fp.primitive_element() ** (192 // ((1 << (num_evals - 1)) * rate))
        domains = [[gen ** (i * (1 << j)) for i in range(len(evals[j]) * rate)] for j in range(len(evals))]
        commitment, codes = BatchFRI.batch_commit(evals, rate, domains, debug=False)
        root = commitment['layers'][-1][0]
        transcript = MerlinTranscript(b'test')
        transcript.append_message(b'code', root)
        point = int.from_bytes(transcript.challenge_bytes(b'point', 4), 'big')
        point = gen ** point * Fp.primitive_element()
        vals = [UniPolynomial.uni_eval_from_evals(codes[i], point, domains[i][:len(codes[i])], Fp(1)) for i in range(len(codes))]
        _ = BatchFRI.batch_prove(codes, commitment, vals, point, domains, rate, (1 << (num_evals - 1)), domains[0][1], transcript, debug=False)

    def test_batch_verify(self):
        from sage.all import GF
        from field import magic
        from random import randint
        from merlin.merlin_transcript import MerlinTranscript

        Fp = magic(GF(193))
        num_evals = 4
        evals = [[Fp(randint(0, 193)) for _ in range(1 << i)] for i in range(num_evals)]
        # in descending order
        evals = list(reversed(evals))
        rate = 4
        gen = Fp.primitive_element() ** (192 // ((1 << (num_evals - 1)) * rate))
        domains = [[gen ** (i * (1 << j)) for i in range(len(evals[j]) * rate)] for j in range(len(evals))]
        commitment, codes = BatchFRI.batch_commit(evals, rate, domains, debug=False)
        root = commitment['layers'][-1][0]
        transcript = MerlinTranscript(b'test')
        transcript.append_message(b'code', root)
        point = int.from_bytes(transcript.challenge_bytes(b'point', 4), 'big')
        point = gen ** point * Fp.primitive_element()
        vals = [UniPolynomial.uni_eval_from_evals(evals[i], point, domains[i][:len(evals[i])], Fp(1)) for i in range(len(evals))]
        assert vals == [UniPolynomial.uni_eval_from_evals(codes[i], point, domains[i][:len(codes[i])], Fp(1)) for i in range(len(codes))], f"evals and codes are not the same, {vals} != {[UniPolynomial.uni_eval_from_evals(codes[i], point, domains[i][:len(codes[i])], Fp(1)) for i in range(len(codes))]} "
        proof = BatchFRI.batch_prove(codes, commitment, vals, point, domains, rate, (1 << (num_evals - 1)), gen, transcript, debug=False)
        transcript = MerlinTranscript(b'test')
        BatchFRI.batch_verify((1 << (num_evals - 1)), rate, proof, vals, domains, gen, Fp.primitive_element(), transcript, debug=False)


if __name__ == '__main__':
    main()
