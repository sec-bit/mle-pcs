from hashlib import sha256
from unipoly2 import UniPolynomialWithFft
from curve import Fr
from merkle import MerkleTree, verify_decommitment
from transcript import MerlinTranscript
from utils import log_2, bit_reverse

class FRIBFCommitment:
    def __init__(self, data, log_n, log_blowup, code, tree: MerkleTree, root: str):
        self.data = data
        self.log_n = log_n
        self.log_blowup = log_blowup
        self.code = code
        self.tree = tree
        self.root = root

    def __str__(self):
        return f"FRIBFCommitment(data={self.data}, log_blowup={self.log_blowup}, code={self.code}, tree={self.tree}, root={self.root})"


class FRIBFProof:
    def __init__(self, intermediate_commitments: list[str], query_paths: list, merkle_paths: list, folded):
        self.intermediate_commitments = intermediate_commitments
        self.query_paths = query_paths
        self.merkle_paths = merkle_paths
        self.folded = folded


class FRIBigField:
    F = Fr
    twiddles = None
    twiddles_reversed = None
    twiddles_reversed_inv = None
    query_num = None

    @classmethod
    def precompute_twiddles(cls, log_n):
        cls.twiddles = [[cls.F.one()]]
        cls.twiddles_reversed = [[cls.F.one()]]
        cls.twiddles_reversed_inv = [[cls.F.one()]]

        for i in range(1, log_n + 1):
            omega = cls.F.nth_root_of_unity(1 << i)
            base = cls.F.one()

            level = []
            for j in range(1 << i):
                level.append(base)
                base *= omega

            cls.twiddles.append(level.copy())
            
            cls.twiddles_reversed.append(level)
            bit_reverse_inplace(cls.twiddles_reversed[-1])

            cls.twiddles_reversed_inv.append(cls.twiddles_reversed[-1].copy())
            batch_invert_inplace(cls.twiddles_reversed_inv[-1], cls.F)

    @classmethod
    def set_field_type(cls, field_type):
        cls.F = field_type

    @classmethod
    def commit(cls, evals, log_blowup, debug=0):
        assert log_blowup > 0, f"log_blowup should be greater than 0"
        assert len(evals) > 1, f"Length of evals should be greater than 1"
        log_n = log_2(len(evals))
        coeffs = UniPolynomialWithFft.ifft(evals, log_n, cls.F.nth_root_of_unity(1 << log_n))
        bit_reverse_inplace(coeffs)

        code = eval_over_fft_field(coeffs, log_blowup, cls.twiddles, cls.F)
        if debug > 0:
            expected = UniPolynomialWithFft.ifft(code, log_n + log_blowup, cls.F.nth_root_of_unity(1 << (log_n + log_blowup)))
            expected = expected[:1 << log_n]
            bit_reverse_inplace(expected)
            assert expected == coeffs, f"expected: {expected}, coeffs: {coeffs}"
            for i in range(1 << log_n):
                assert evals[i] == code[i * (1 << log_blowup)]

        bit_reverse_inplace(code)

        tree = plant_tree(code)
        return FRIBFCommitment(evals, log_n, log_blowup, code, tree, tree.root)

    @classmethod
    def open(cls, commitment: FRIBFCommitment, point, value, transcript: MerlinTranscript, debug=0):
        '''
        NOTICE: PLEASE MAKE SURE THAT THE COMMITMENT WAS ABSORBED INTO THE TRANSCRIPT BEFORE OPENING.
        '''

        assert isinstance(commitment, FRIBFCommitment), f"commitment should be an instance of FRIBFCommitment"
        assert isinstance(point, cls.F), f"point should be an instance of {cls.F}"
        assert isinstance(value, cls.F), f"value should be an instance of {cls.F}"
        # assert isinstance(transcript, MerlinTranscript), f"transcript should be an instance of MerlinTranscript"

        assert commitment.data is not None, f"commitment should contain data"
        assert commitment.code is not None, f"commitment should contain code"
        assert commitment.tree is not None, f"commitment should contain tree"
        assert commitment.root is not None, f"commitment should contain root"
        assert commitment.log_n is not None, f"commitment should contain log_n"
        assert commitment.log_blowup is not None, f"commitment should contain log_blowup"

        evals = commitment.data
        log_blowup = commitment.log_blowup
        rscode_reversed = commitment.code
        log_n = commitment.log_n

        if debug > 0:
            assert len(evals) == 1 << log_n
            assert len(rscode_reversed) == 1 << (log_n + log_blowup)

        N = 1 << (log_n + log_blowup)
        inv_2 = (cls.F.one() + cls.F.one()).inv()

        if debug > 0:
            assert inv_2 * (cls.F.one() + cls.F.one()) == cls.F.one()

        lambda_ = cls.F.from_bytes(transcript.challenge_bytes(b"lambda", 32))

        # quotient
        numerators = [rscode_reversed[i] - value for i in range(N)]
        denominators = [cls.twiddles_reversed[log_n + log_blowup][i] - point for i in range(N)]
        # denominators = [cls.F.nth_root_of_unity(1 << (log_n + log_blowup)) ** bit_reverse(i, log_n + log_blowup) - point for i in range(N)]
        batch_invert_inplace(denominators, cls.F)
        quotient = [(cls.F.one() + lambda_ * cls.twiddles_reversed[log_n + log_blowup][i]) * numerators[i] * denominators[i] for i in range(N)]

        if debug > 0:
            assert len(quotient) == N
            q_copy = quotient.copy()
            bit_reverse_inplace(q_copy)
            q_coeffs = UniPolynomialWithFft.ifft(q_copy, log_n + log_blowup, cls.F.nth_root_of_unity(1 << (log_n + log_blowup)))
            for i in range(1 << log_n, 1 << (log_n + log_blowup)):
                assert q_coeffs[i] == cls.F.zero(), f"q_coeffs={q_coeffs}"

        # commit phase
        folded = quotient
        intermediate_commitments: list[FRIBFCommitment] = []
        for i in range(log_n):
            hint = ("alpha-" + str(i)).encode()
            alpha = cls.F.from_bytes(transcript.challenge_bytes(hint, 32))
            level = cls.twiddles_reversed_inv[log_n + log_blowup - i]
            if debug > 0: assert len(level) == 1 << (log_n + log_blowup - i)
            new_folded = []
            for j in range(0, 1 << (log_n + log_blowup - i), 2):
                f_even = (folded[j] + folded[j + 1]) * inv_2
                f_odd = (folded[j] - folded[j + 1]) * inv_2 * level[j]
                new_folded.append(f_even + alpha * f_odd)
                if debug > 0: assert level[j] == cls.F.nth_root_of_unity(1 << (log_n + log_blowup - i)).inv() ** bit_reverse(j, log_n + log_blowup - i)
            folded = new_folded

            if debug > 0:
                assert len(folded) == 1 << (log_n + log_blowup - i - 1)
                folded_cp = folded.copy()
                bit_reverse_inplace(folded_cp)
                f_coeffs = UniPolynomialWithFft.ifft(folded_cp, log_n + log_blowup - i - 1, cls.F.nth_root_of_unity(1 << (log_n + log_blowup - i - 1)))
                for j in range(1 << (log_n - i - 1), 1 << (log_n + log_blowup - i - 1)):
                    assert f_coeffs[j] == cls.F.zero(), f"i={i}, f_coeffs={f_coeffs}"

            if i < log_n - 1:
                intermediate_tree = plant_tree(folded)
                intermediate_commitments.append(FRIBFCommitment(None, log_n, log_blowup, folded, intermediate_tree, intermediate_tree.root))
                hint = ("oracle-" + str(i)).encode()
                transcript.absorb(hint, intermediate_commitments[-1].root)
            elif i == log_n - 1:
                transcript.absorb(b"oracle-final", folded[0])
            else:
                raise Exception("Invalid i")

        if debug > 0:
            assert len(intermediate_commitments) == log_n - 1
            assert len(folded) == 1 << log_blowup
            for i in range(1, 1 << log_blowup):
                assert folded[0] == folded[i], f"folded={folded}"

        # query phase
        queries = []
        for i in range(cls.query_num):
            hint = ("query-" + str(i)).encode()
            q = int.from_bytes(transcript.challenge_bytes(hint, 32)) % (N >> 1)
            queries.append(q)

        if debug > 1: print(f"prover: queries={queries}")
        
        if debug > 0:
            assert len(queries) == cls.query_num
        
        merkle_paths = []
        query_paths = []
        for q in queries:
            q <<= 1

            query_path = [rscode_reversed[q], rscode_reversed[q ^ 1]]
            merkle_path = [commitment.tree.get_authentication_path(q >> 1)]

            if debug > 1: print(f"prover: q>>1={q>>1}, query_path={query_path}, merkle_path={merkle_path[0]}, root={commitment.root}")
            if debug > 0: assert verify_merkle_path(q >> 1, query_path, merkle_path[0], commitment.root, debug=debug)

            for i in range(log_n - 1):
                q >>= 1
                q_sibling = q ^ 1
                query_path.append(intermediate_commitments[i].code[q_sibling])
                merkle_path.append(intermediate_commitments[i].tree.get_authentication_path(q >> 1))
                if debug > 0:
                    q_l = min(q, q_sibling)
                    q_r = q + q_sibling - q_l
                    if debug > 1: print(f"prover: q>>1={q>>1}, leaves={intermediate_commitments[i].code[q_l]}, {intermediate_commitments[i].code[q_r]}, merkle_path={merkle_path[-1]}, root={intermediate_commitments[i].root}")
                    assert verify_merkle_path(q >> 1, [intermediate_commitments[i].code[q_l], intermediate_commitments[i].code[q_r]], merkle_path[-1], intermediate_commitments[i].root, debug=debug)

            if debug > 0:
                assert q < 1 << (log_blowup + 1), f"q={q}"
                assert len(merkle_path) == log_n
                assert len(query_path) == log_n + 1
            
            merkle_paths.append(merkle_path)
            query_paths.append(query_path)

        intermediate_commitments: list[str] = [comm.root for comm in intermediate_commitments]
        return FRIBFProof(intermediate_commitments, query_paths, merkle_paths, folded[0])

    @classmethod
    def verify(cls, commitment: FRIBFCommitment, point, value, proof: FRIBFProof, transcript: MerlinTranscript, debug=0):
        '''
        NOTICE: PLEASE MAKE SURE THAT THE COMMITMENT WAS ABSORBED INTO THE TRANSCRIPT BEFORE VERIFYING.
        '''

        assert isinstance(commitment, FRIBFCommitment), f"commitment should be an instance of FRIBFCommitment"
        assert isinstance(point, cls.F), f"point should be an instance of {cls.F}"
        assert isinstance(value, cls.F), f"value should be an instance of {cls.F}"
        assert isinstance(proof, FRIBFProof), f"proof should be an instance of FRIBFProof"
        # assert isinstance(transcript, MerlinTranscript), f"transcript should be an instance of MerlinTranscript"

        assert commitment.data is None, f"commitment should not contain data"
        assert commitment.code is None, f"commitment should not contain code"
        assert commitment.tree is None, f"commitment should not contain tree"
        assert commitment.root is not None, f"commitment should contain root"
        assert commitment.log_n is not None, f"commitment should contain log_n"
        assert commitment.log_blowup is not None, f"commitment should contain log_blowup"

        assert proof.intermediate_commitments is not None, f"proof should contain intermediate_commitments"
        assert proof.query_paths is not None, f"proof should contain query_paths"
        assert proof.merkle_paths is not None, f"proof should contain merkle_paths"
        assert proof.folded is not None, f"proof should contain folded"

        log_blowup = commitment.log_blowup
        log_n = commitment.log_n
        root = commitment.root

        N = 1 << (log_n + log_blowup)
        inv_2 = (cls.F.one() + cls.F.one()).inv()
        intermediate_commitments = proof.intermediate_commitments
        query_paths = proof.query_paths
        merkle_paths = proof.merkle_paths
        folded = proof.folded
        if debug > 0:
            assert len(merkle_paths) == cls.query_num
            assert len(query_paths) == cls.query_num
            assert len(intermediate_commitments) == log_n - 1

        lambda_ = cls.F.from_bytes(transcript.challenge_bytes(b"lambda", 32))

        # commit phase
        challenges = []
        for i in range(log_n):
            hint = ("alpha-" + str(i)).encode()
            alpha = cls.F.from_bytes(transcript.challenge_bytes(hint, 32))
            challenges.append(alpha)

            if i < log_n - 1:
                hint = ("oracle-" + str(i)).encode()
                transcript.absorb(hint, intermediate_commitments[i])
            else:
                hint = b"oracle-final"
                transcript.absorb(hint, folded)

        # query phase
        queries = []
        for i in range(cls.query_num):
            hint = ("query-" + str(i)).encode()
            q = int.from_bytes(transcript.challenge_bytes(hint, 32)) % (N >> 1)
            queries.append(q)

        if debug > 1: print(f"verifier: queries={queries}")
        
        for q, query_path, merkle_path in zip(queries, query_paths, merkle_paths):
            q <<= 1

            assert len(merkle_path) == log_n
            assert len(query_path) == log_n + 1

            if debug > 1: print(f"verifier: q>>1={q>>1}, query_path={query_path[:2]}, merkle_path={merkle_path[0]}, root={root}")
            assert verify_merkle_path(q >> 1, query_path[:2], merkle_path[0], root, debug=debug)

            leaves = query_path[:2]
            leaves[0] = (cls.F.one() + lambda_ * cls.twiddles_reversed[log_n + log_blowup][q]) * (leaves[0] - value) / (cls.twiddles_reversed[log_n + log_blowup][q] - point)
            leaves[1] = (cls.F.one() + lambda_ * cls.twiddles_reversed[log_n + log_blowup][q + 1]) * (leaves[1] - value) / (cls.twiddles_reversed[log_n + log_blowup][q + 1] - point)
            query_value = (leaves[0] + leaves[1]) * inv_2 + challenges[0] * (leaves[0] - leaves[1]) * inv_2 * cls.twiddles_reversed_inv[log_n + log_blowup][q]

            for i in range(1, log_n):
                q >>= 1
                leaves = [query_path[i + 1], query_path[i + 1]]
                leaves[q & 1] = query_value
                if debug > 1: print(f"verifier: q>>1={q>>1}, leaves={leaves}, merkle_path={merkle_path[i]}, root={intermediate_commitments[i - 1]}")
                assert verify_merkle_path(q >> 1, leaves, merkle_path[i], intermediate_commitments[i - 1], debug=debug)

                level = cls.twiddles_reversed_inv[log_n + log_blowup - i]
                query_value = (leaves[0] + leaves[1]) * inv_2 + challenges[i] * (leaves[0] - leaves[1]) * inv_2 * level[min(q, q ^ 1)]
            
            if debug > 0: assert q < 1 << (log_blowup + 1), f"q={q}"
            assert query_value == folded


def eval_over_fft_field(coeffs, log_blowup, twiddles, field_type, debug=0):
    n = len(coeffs)
    log_n = log_2(n)
    N = 1 << (log_n + log_blowup)
    rscode = [field_type.zero()] * N

    for i in range(n):
        for j in range(1 << log_blowup):
            rscode[i * (1 << log_blowup) + j] = coeffs[i]

    chunk_size = 1 << log_blowup
    for i in range(log_n):
        chunk_size <<= 1
        half_chunk = chunk_size >> 1
        level = twiddles[i + log_blowup + 1]
        if debug > 0:
            assert len(level) == chunk_size or log_blowup == 0, f"len(level) = {len(level)}, chunk_size = {chunk_size}, log_blowup = {log_blowup}"
        for start in range(0, N, chunk_size):
            for j in range(half_chunk):
                rhs = rscode[start + j + half_chunk] * level[j]
                rscode[start + j + half_chunk] = rscode[start + j] - rhs
                rscode[start + j] += rhs

    return rscode

def batch_invert_inplace(vec, field_type):
    acc = field_type.one()
    tmp = []
    for v in vec:
        tmp.append(acc)
        acc *= v
    acc = acc.inv()
    for i in range(len(vec) - 1, -1, -1):
        t = tmp[i] * acc
        acc *= vec[i]
        vec[i] = t


def bit_reverse_inplace(vec):
    n = len(vec)
    log_n = log_2(n)
    for i in range(n):
        j = bit_reverse(i, log_n)
        if i < j:
            vec[i], vec[j] = vec[j], vec[i]

def plant_tree(data):
    n = len(data)

    data = [sha256(str(d).encode()).hexdigest() for d in data]
    leaves = []
    for i in range(n >> 1):
        leaves.append(sha256((data[i * 2] + data[i * 2 + 1]).encode()).hexdigest())

    return MerkleTree(leaves)

def verify_merkle_path(leaf_id, leaves: list, decommitment, root, debug=0):
    if debug > 0: assert len(leaves) == 2
    leaves = (sha256(str(leaves[0]).encode()).hexdigest(), sha256(str(leaves[1]).encode()).hexdigest())
    node = sha256((leaves[0] + leaves[1]).encode()).hexdigest()
    return verify_decommitment(leaf_id, node, decommitment, root)
