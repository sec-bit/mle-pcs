from unittest import TestCase, main
import sys

sys.path.append('../src')
sys.path.append('src')

from fri_babybear import FRI
from utils import is_power_of_two
from unipolynomial import UniPolynomial
class TestFRI(TestCase):
    def setUp(self):
        # Set up a scalar field for testing (e.g., integers modulo a prime)
        prime = 193  # A small prime for testing
        UniPolynomial.set_scalar(int, lambda x: x % prime)

    def test_fold(self):
        from sage.all import GF
        from field import magic

        Fp = magic(GF(193))
    
        evals = FRI.rs_encode_single([2, 3, 4, 5], [Fp.primitive_element() ** (i * 192 // 16) for i in range(16)], 4)
        coset = Fp.primitive_element() ** (192 // len(evals))
        alpha = Fp(7)

        evals = FRI.fold(evals, alpha, coset, debug=False)
        coset = coset ** 2
        evals = FRI.fold(evals, alpha, coset, debug=False)

        assert evals[0] == evals[1] == evals[2] == evals[3]

    def test_low_degree(self):
        from sage.all import GF
        from field import magic
        from random import randint
        from merlin.merlin_transcript import MerlinTranscript

        Fp = magic(GF(193))

        assert Fp.primitive_element() ** 192 == 1

        degree_bound = 8
        blow_up_factor = 2
        num_verifier_queries = 8
        assert is_power_of_two(degree_bound)

        evals = FRI.rs_encode_single([randint(0, 193) for _ in range(degree_bound)], [Fp.primitive_element() ** (i * 192 // (degree_bound * 2 ** blow_up_factor)) for i in range(degree_bound * 2 ** blow_up_factor)], 2 ** blow_up_factor)
        proof = FRI.prove_low_degree(evals, 2 ** blow_up_factor, degree_bound, Fp.primitive_element() ** (192 // len(evals)), num_verifier_queries, MerlinTranscript(b'test'), debug=False)
        FRI.verify_low_degree(degree_bound, 2 ** blow_up_factor, proof, Fp.primitive_element() ** (192 // len(evals)), num_verifier_queries, MerlinTranscript(b'test'), debug=False)

    def test_prove(self):
        from sage.all import GF
        from field import magic
        from random import randint
        from merlin.merlin_transcript import MerlinTranscript

        Fp = magic(GF(193))

        assert Fp.primitive_element() ** 192 == 1
        
        rate = 4
        evals_size = 4
        coset = Fp.primitive_element() ** (192 // (evals_size * rate))
        point = Fp.primitive_element()
        evals = [i for i in range(evals_size)]
        value = UniPolynomial.uni_eval_from_evals(evals, point, [coset ** i for i in range(len(evals))])
        domain = [coset ** i for i in range(evals_size * rate)]
        code_tree, code = FRI.commit(evals, rate, domain, debug=False)
        transcript = MerlinTranscript(b'test')
        transcript.append_message(b"code", code_tree.root.encode('ascii'))
        proof = FRI.prove(code, code_tree, value, point, domain, rate, evals_size, coset, transcript, debug=False)
        FRI.verify(evals_size, rate, proof, point, value, domain, coset, MerlinTranscript(b'test'), debug=False)


if __name__ == '__main__':
    main()
