import sys
from unittest import TestCase, main
from random import randint

sys.path.append("../src")
sys.path.append("src")

from mmcs import MMCS

class TestMMCS(TestCase):
    def setUp(self):
        def hash(x): return x
        def compress(x): return x[0] + x[1]
        MMCS.configure(hash, compress)

    def test_mmcs(self):
        evals = [[randint(0, 2**32-1) for _ in range(1 << i)] for i in range(4)]
        evals = list(reversed(evals))
        prover_data = MMCS.commit(evals, debug=False)
        openings, proof, root = MMCS.open(0, prover_data, debug=False)
        MMCS.verify(0, openings, proof, root, debug=False)

if __name__ == "__main__":
    main()
