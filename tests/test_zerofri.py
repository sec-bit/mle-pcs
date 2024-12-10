from unittest import TestCase, main
from sage.all import *
import sys

sys.path.append('../src')
sys.path.append('src')

from unipolynomial import UniPolynomial
from mle2 import MLEPolynomial
from merlin.merlin_transcript import MerlinTranscript
from zerofri import ZeroFRI

class TestZeroFRI(TestCase):
    def test_zerofri_batch(self):
        from random import randint
        from pickle import dumps
        from sys import getsizeof

        p = 193
        Fp = GF(p)

        UniPolynomial.set_scalar(int, lambda x: Fp(x))
        
        for i in range(2, 5):
            num_vars = i
            rate = 4
            point = [Fp(randint(0, p-1)) for _ in range(num_vars)]
            mle_poly = [Fp(randint(0, p-1)) for _ in range(1 << num_vars)]
            v = MLEPolynomial(mle_poly, num_vars).evaluate(point)

            proof = ZeroFRI.prove_zerofri(mle_poly, rate, point, v, Fp.primitive_element(), p-1, MerlinTranscript(b'zeromorph'), one=Fp(1), debug=0)
            print(f"size of batched proof for {num_vars} variables:", getsizeof(dumps(proof)))
            f_proof, f_val, quotients_proof, quotients_vals = proof
            ZeroFRI.verify_zerofri(f_proof, f_val, quotients_proof, quotients_vals, num_vars, rate, point, v, Fp.primitive_element(), p-1, MerlinTranscript(b'zeromorph'), debug=0)

    def test_zerofri_not_batch(self):
        from random import randint
        from pickle import dumps
        from sys import getsizeof

        p = 193
        Fp = GF(p)

        UniPolynomial.set_scalar(int, lambda x: Fp(x))
        
        for i in range(2, 5):
            num_vars = i
            rate = 4
            point = [Fp(randint(0, p-1)) for _ in range(num_vars)]
            mle_poly = [Fp(randint(0, p-1)) for _ in range(1 << num_vars)]
            v = MLEPolynomial(mle_poly, num_vars).evaluate(point)

            proof = ZeroFRI.prove_zerofri(mle_poly, rate, point, v, Fp.primitive_element(), p-1, MerlinTranscript(b'zeromorph'), one=Fp(1), debug=2, batch=False)
            print(f"size of not batched proof for {num_vars} variables:", getsizeof(dumps(proof)))
            f_proof, f_val, quotients_proof, quotients_vals = proof
            ZeroFRI.verify_zerofri(f_proof, f_val, quotients_proof, quotients_vals, num_vars, rate, point, v, Fp.primitive_element(), p-1, MerlinTranscript(b'zeromorph'), debug=2, batch=False)


if __name__ == "__main__":
    main()
