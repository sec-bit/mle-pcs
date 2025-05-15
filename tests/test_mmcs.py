import sys
from unittest import TestCase, main
from random import randint
from hashlib import sha256

sys.path.append("../src")
sys.path.append("src")

from mmcs import MMCS

class TestMMCS(TestCase):
    def setUp(self):
        def hash(x): return sha256(str(x).encode()).digest()
        def compress(x): return sha256(x[0] + x[1]).digest()
        MMCS.configure(hash, compress)

    def test_mmcs(self):
        evals = [[randint(0, 2**32-1) for _ in range(4 * (1 << i))] for i in range(4)]
        evals = list(reversed(evals))
        prover_data = MMCS.commit(evals, debug=False)
        idx = randint(0, 2 ** 32 - 1)
        openings, proof, root = MMCS.open(idx, prover_data, debug=True)
        MMCS.verify(idx, openings, proof, root, debug=True)

if __name__ == "__main__":
    main()
