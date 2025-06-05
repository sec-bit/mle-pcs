from unittest import TestCase, main
from random import randint
import sys

sys.path.append('../src')
sys.path.append('src')

from basefold_rs_opt_pcs import BASEFOLD_RS_PCS, Field
from merlin.merlin_transcript import MerlinTranscript
from merkle import MerkleTree
from mle2 import MLEPolynomial
from utils import inner_product

def random_test(k):

    BASEFOLD_RS_PCS.blowup_factor = 8
    BASEFOLD_RS_PCS.security_bits = 128
    pcs = BASEFOLD_RS_PCS(MerkleTree, debug = 1)

    tr = MerlinTranscript(b"basefold-rs-pcs")

    # A simple instance f(x) = y

    evals = [Field.random() for _ in range(1 << k)]
    us = [Field.random() for _ in range(k)]
    MLEPolynomial.set_field_type(Field)
    eqs = MLEPolynomial.eqs_over_hypercube(us)
    
    y = inner_product(evals, eqs, Field.zero())
    f_mle = MLEPolynomial(evals, k)
    assert f_mle.evaluate(us) == y
    print(f"f(x[]) = {y}")
    f_cm = pcs.commit(f_mle)

    print(f"f(0,us)={f_mle.evaluate([Field(0)]+us[1:])}")
    print(f"f(1,us)={f_mle.evaluate([Field(1)]+us[1:])}")
    print("🕐 Generating proof ....")
    v, arg = pcs.prove_eval(f_cm, f_mle, us, tr.fork(b"basefold_rs_pcs"))
    print("ℹ️ Proof generated.")

    assert v == y
    print("🕐 Verifying proof ....")
    checked = pcs.verify_eval(f_cm, us, v, arg, tr.fork(b"basefold_rs_pcs"))
    assert checked
    print("✅ Proof verified")

def zero_test(k):

    BASEFOLD_RS_PCS.blowup_factor = 8
    BASEFOLD_RS_PCS.security_bits = 128
    pcs = BASEFOLD_RS_PCS(MerkleTree, debug = 1)

    tr = MerlinTranscript(b"basefold-rs-pcs")

    # A simple instance f(x) = y

    evals = [Field.zero() for _ in range(1 << k)]
    us = [Field.random() for _ in range(k)]
    MLEPolynomial.set_field_type(Field)
    eqs = MLEPolynomial.eqs_over_hypercube(us)
    
    y = inner_product(evals, eqs, Field.zero())
    f_mle = MLEPolynomial(evals, k)
    assert f_mle.evaluate(us) == y
    print(f"f(x[]) = {y}")
    f_cm = pcs.commit(f_mle)

    print(f"f(0,us)={f_mle.evaluate([Field(0)]+us[1:])}")
    print(f"f(1,us)={f_mle.evaluate([Field(1)]+us[1:])}")
    print("🕐 Generating proof ....")
    v, arg = pcs.prove_eval(f_cm, f_mle, us, tr.fork(b"basefold_rs_pcs"))
    print("ℹ️ Proof generated.")

    assert v == y
    print("🕐 Verifying proof ....")
    checked = pcs.verify_eval(f_cm, us, v, arg, tr.fork(b"basefold_rs_pcs"))
    assert checked
    print("✅ Proof verified")

def failure_test_1(k):

    BASEFOLD_RS_PCS.blowup_factor = 8
    BASEFOLD_RS_PCS.security_bits = 128
    pcs = BASEFOLD_RS_PCS(MerkleTree, debug = 1)

    tr = MerlinTranscript(b"basefold-rs-pcs")

    # A simple instance f(x) = y
    # evals = [Field(2), Field(3), Field(4), Field(5), Field(6), Field(7), Field(8), Field(9), \
            #  Field(10), Field(11), Field(12), Field(13), Field(14), Field(15), Field(16), Field(17)]
    evals = [Field.random() for _ in range(1 << k)]
    us = [Field.random() for _ in range(k)]
    MLEPolynomial.set_field_type(Field)
    eqs = MLEPolynomial.eqs_over_hypercube(us)
    
    y = inner_product(evals, eqs, Field.zero())
    f_mle = MLEPolynomial(evals, k)
    assert f_mle.evaluate(us) == y
    print(f"f(x[]) = {y}")
    f_cm = pcs.commit(f_mle)

    print(f"f(0,us)={f_mle.evaluate([Field(0)]+us[1:])}")
    print(f"f(1,us)={f_mle.evaluate([Field(1)]+us[1:])}")
    print("🕐 Generating proof ....")
    v, arg = pcs.prove_eval(f_cm, f_mle, us, tr.fork(b"basefold_rs_pcs"))
    print("ℹ️ Proof generated.")

    assert v == y
    print("🕐 Verifying proof ....")
    try:
        checked = pcs.verify_eval(f_cm, us, v + Field(1), arg, tr.fork(b"basefold_rs_pcs"))
        assert checked
        print("❌ Proof passed")
    except Exception as e:
        print(f"✅ Proof verification failed: {e}")
    else:
        raise Exception("Proof verification should fail, but it passed")

def failure_test_2(k):

    BASEFOLD_RS_PCS.blowup_factor = 8
    BASEFOLD_RS_PCS.security_bits = 128
    pcs = BASEFOLD_RS_PCS(MerkleTree, debug = 1)

    tr = MerlinTranscript(b"basefold-rs-pcs")

    # A simple instance f(x) = y
    # evals = [Field(2), Field(3), Field(4), Field(5), Field(6), Field(7), Field(8), Field(9), \
            #  Field(10), Field(11), Field(12), Field(13), Field(14), Field(15), Field(16), Field(17)]
    evals = [Field.random() for _ in range(1 << k)]
    us = [Field.random() for _ in range(k)]
    MLEPolynomial.set_field_type(Field)
    eqs = MLEPolynomial.eqs_over_hypercube(us)
    
    y = inner_product(evals, eqs, Field.zero())
    f_mle = MLEPolynomial(evals, k)
    assert f_mle.evaluate(us) == y
    print(f"f(x[]) = {y}")
    f_cm = pcs.commit(f_mle)

    print(f"f(0,us)={f_mle.evaluate([Field(0)]+us[1:])}")
    print(f"f(1,us)={f_mle.evaluate([Field(1)]+us[1:])}")
    print("🕐 Generating proof ....")
    v, arg = pcs.prove_eval(f_cm, f_mle, us, tr.fork(b"basefold_rs_pcs"))
    print("ℹ️ Proof generated.")
    arg['final_constant'] = arg['final_constant'] + Field(1)

    assert v == y
    print("🕐 Verifying proof ....")
    try:
        checked = pcs.verify_eval(f_cm, us, v, arg, tr.fork(b"basefold_rs_pcs"))
        assert checked
        print("❌ Proof passed")
    except Exception as e:
        print(f"✅ Proof verification failed: {e}")
    else:
        raise Exception("Proof verification should fail, but it passed")

class BasefoldTest(TestCase):
    def test_random_test(self):
        for i in range(7, 10):
            random_test(i)

    def test_zero_test(self):
        for i in range(7, 10):
            zero_test(i)

    def test_failure_test_1(self):
        for i in range(7, 10):
            failure_test_1(i)

    def test_failure_test_2(self):
        for i in range(7, 10):
            failure_test_2(i)

if __name__ == "__main__":
    main()
