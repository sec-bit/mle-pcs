from unittest import TestCase, main
# from sage.all import *
import sys

sys.path.append('../src')
sys.path.append('src')
sys.path.append('../src/finite-field')

from unipolynomial import UniPolynomial
from mle2 import MLEPolynomial
from merlin.merlin_transcript import MerlinTranscript
from zerofri import ZeroFRI

class TestZeroFRI(TestCase):
    def test_zerofri_batch(self):
        from random import randint
        from pickle import dumps
        from sys import getsizeof
        from babybear import BabyBear, BabyBearExtElem

        UniPolynomial.set_scalar(int, lambda x: x)

        FIELD_SIZE = BabyBear.P - 1
        primitive_element = BabyBear(31)
        
        for i in range(2, 5):
            num_vars = i
            rate = 4
            point = [BabyBear.random() for _ in range(num_vars)]
            mle_poly = [BabyBear.random() for _ in range(1 << num_vars)]
            v = MLEPolynomial(mle_poly, num_vars).evaluate(point)

            proof = ZeroFRI.prove_zerofri(mle_poly, rate, point, v, primitive_element, FIELD_SIZE, MerlinTranscript(b'zeromorph'), one=BabyBear.one(), debug=1, batch=True)
            print(f"size of batched proof for {num_vars} variables:", getsizeof(dumps(proof)))
            f_proof, f_val, quotients_proof, quotients_vals = proof
            ZeroFRI.verify_zerofri(f_proof, f_val, quotients_proof, quotients_vals, num_vars, rate, point, v, primitive_element, FIELD_SIZE, MerlinTranscript(b'zeromorph'), one=BabyBear.one(), debug=1, batch=True)

    def test_zerofri_not_batch(self):
        from random import randint
        from pickle import dumps
        from sys import getsizeof
        from babybear import BabyBear, BabyBearExtElem

        UniPolynomial.set_scalar(int, lambda x: x)

        FIELD_SIZE = BabyBear.P - 1
        primitive_element = BabyBear(31)

        for i in range(2, 5):
            num_vars = i
            rate = 4
            point = [BabyBear.random() for _ in range(num_vars)]
            mle_poly = [BabyBear.random() for _ in range(1 << num_vars)]
            v = MLEPolynomial(mle_poly, num_vars).evaluate(point)

            proof = ZeroFRI.prove_zerofri(mle_poly, rate, point, v, primitive_element, FIELD_SIZE, MerlinTranscript(b'zeromorph'), one=BabyBear.one(), debug=1, batch=False)
            print(f"size of not batched proof for {num_vars} variables:", getsizeof(dumps(proof)))
            f_proof, f_val, quotients_proof, quotients_vals = proof
            ZeroFRI.verify_zerofri(f_proof, f_val, quotients_proof, quotients_vals, num_vars, rate, point, v, primitive_element, FIELD_SIZE, MerlinTranscript(b'zeromorph'), one=BabyBear.one(), debug=1, batch=False)


if __name__ == "__main__":
    main()
