from unittest import TestCase, main
import sys

sys.path.append('../src')
sys.path.append('../src/finite-field')
sys.path.append('src')

from fri import FRI
from utils import is_power_of_two
from unipolynomial import UniPolynomial
from babybear import BabyBearExtElem, BabyBear

def ext_elem_eq(l):
    assert isinstance(l[0], BabyBearExtElem)
    for i in range(1, len(l)):
        if l[i] != l[0]:
            return False
    return True

class TestFRI(TestCase):
    def setUp(self):
        # Set up a scalar field for testing (e.g., integers modulo a prime)
        # prime = 193  # A small prime for testing
        # UniPolynomial.set_scalar(int, lambda x: x % prime)
        UniPolynomial.set_scalar(BabyBearExtElem, lambda x: x)

    def test_fold(self):
        # from sage.all import GF
        # from field import magic

        # Fp = magic(GF(193))
        FIELD_SIZE = BabyBear.P - 1
        primitive_element = BabyBear(31)

        evals = FRI.rs_encode_single([BabyBear.random() for _ in range(4)], [primitive_element ** (i * FIELD_SIZE // 16) for i in range(16)], 4, BabyBear.zero())
        coset = primitive_element ** (FIELD_SIZE // len(evals))
        alpha = BabyBearExtElem([BabyBear(7), BabyBear.zero(), BabyBear.zero(), BabyBear.zero()])

        evals = FRI.fold(evals, alpha, coset, debug=False)
        coset = coset * coset
        evals = FRI.fold(evals, alpha, coset, debug=False)

        assert ext_elem_eq(evals)

    def test_low_degree(self):
        from merlin.merlin_transcript import MerlinTranscript

        FIELD_SIZE = BabyBear.P - 1
        primitive_element = BabyBear(31)

        degree_bound = 8
        blow_up_factor = 2
        num_verifier_queries = 8
        assert is_power_of_two(degree_bound)

        evals = FRI.rs_encode_single([BabyBear.random() for _ in range(degree_bound)], [primitive_element ** (i * FIELD_SIZE // (degree_bound * 2 ** blow_up_factor)) for i in range(degree_bound * 2 ** blow_up_factor)], 2 ** blow_up_factor, BabyBear.zero())
        proof = FRI.prove_low_degree(evals, 2 ** blow_up_factor, degree_bound, primitive_element ** (FIELD_SIZE // len(evals)), num_verifier_queries, MerlinTranscript(b'test'), debug=False)
        FRI.verify_low_degree(degree_bound, 2 ** blow_up_factor, proof, primitive_element ** (FIELD_SIZE // len(evals)), num_verifier_queries, MerlinTranscript(b'test'), debug=False)

    def test_prove(self):
        from merlin.merlin_transcript import MerlinTranscript

        FIELD_SIZE = BabyBear.P - 1
        primitive_element = BabyBear(31)
        
        rate = 4
        evals_size = 4
        coset = primitive_element ** (FIELD_SIZE // (evals_size * rate))
        point = primitive_element
        evals = [BabyBear(i) for i in range(evals_size)]
        # value = UniPolynomial.uni_eval_from_evals(evals, point, [coset ** i for i in range(len(evals))], BabyBear.one())
        domain = [coset ** i for i in range(evals_size * rate)]
        code_tree, code, coeffs = FRI.commit(evals, rate, domain, debug=False)
        value = UniPolynomial.evaluate_at_point(coeffs, point)
        transcript = MerlinTranscript(b'test')
        transcript.append_message(b"code", code_tree.root.encode('ascii'))
        proof = FRI.prove(code, code_tree, value, point, domain, rate, evals_size, coset, transcript, debug=False)
        transcript = MerlinTranscript(b'test')
        transcript.append_message(b"code", code_tree.root.encode('ascii'))
        FRI.verify(evals_size, rate, proof, point, value, domain, coset, transcript, debug=False)


if __name__ == '__main__':
    main()
