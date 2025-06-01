#!/usr/bin/env python3

# WARNING: This implementation may contain bugs and has not undergone auditing. 
# It is intended for educational and research purposes only.
# DO NOT use it in a production environment.

from utils import log_2, next_power_of_two
from utils import inner_product, Scalar


# Implementation of DP23 PCS (RS encoding) [DP23]
#
# [ZCF23] Proximity Testing with Logarithmic Randomness
#
#  Author: Benjamin E. Diamond and Jim Posen
#  URL: https://eprint.iacr.org/2023/630

from curve import Fr as BN254_Fr
from merlin.merlin_transcript import MerlinTranscript
from mle2 import MLEPolynomial
from unipoly2 import UniPolynomial, UniPolynomialWithFft, bit_reverse_permutation
from merkle import MerkleTree, verify_decommitment

# from ff.tiny import Fp

Fp = BN254_Fr
MLEPolynomial.set_field_type(Fp)
UniPolynomial.set_field_type(Fp)
UniPolynomialWithFft.set_field_type(Fp)


def rs_encode(f: list[Fp], coset: Fp, blowup_factor: int) -> list[Fp]:
    n = next_power_of_two(len(f))
    N = n * blowup_factor

    omega_Nth = Fp.nth_root_of_unity(N)
    # print(f"omega_Nth = {omega_Nth}")
    k = log_2(N)
    # print(f"n = {n}, N = {N}, k = {k}")
    vec = f + [Fp.zero()] * (N - len(f))
    # print(f"vec = {vec}, len(vec) = {len(vec)}")
    return UniPolynomialWithFft.fft_coset_rbo(vec, coset, k, omega=omega_Nth)

class Commitment:

    def __init__(self, tree: MerkleTree):
        self.tree = tree
        self.cm = tree.root
        self.root = tree.root

    def __repr__(self):
        return f"Commitment(len={len(self.tree.data)}, root={self.cm})"

def matrix_transpose(M):
    if type(M[0]) == type([]):
        return [[M[j][i] for j in range(len(M))] for i in range(len(M[0]))]
    elif type(M) == type([Fp(0)]):
        return [[M[i]] for i in range(len(M))]
    
def matrix_mul_vec(G, m):
    assert len(G[0]) == len(m), "len(G[0]) != len(m)"
    return [inner_product(G[i], m, Fp(0)) for i in range(len(G))]

def matrix_mul_matrix(G, M):
    m = len(G)
    n = len(G[0])
    k = len(M[0])
    assert n == len(M), "len(G[0]) != len(M[0])"
    A = []
    for i in range(m):
        A.append([inner_product(G[i], [M[l][j] for l in range(n)], Fp(0)) for j in range(k)])
    return A

class LIGERO_DP23_RS_PCS:

    blowup_factor = 2 # WARNING: this is not secure
    num_queries = 3   # WARNING: this is not secure
    # coset_gen = Fp.multiplicative_generator()
    coset_gen = Fp(1)
    max_queries_try = 1000  # NOTE: change it to a practical number

    def __init__(self, oracle, debug: int = 0):
        """
        Args:
            oracle: the oracle to use for the proof
        """
        # self.oracle = oracle
        # self.rng = random.Random("basefold-rs-pcs")
        self.debug = debug

    def commit(self, f_mle: MLEPolynomial) -> Commitment:
        """
        Commit to the MLE polynomial
            col: 1, ..., 2**k2-1
            row: 0, ..., 2**k1-1

            [(1-r2)(1-r3)  r2(1-r3)  r3(1-r2)  r2*r3]   [ t0,  t1,   t2,   t3  ]  [ (1-r0)(1-r1) ]
                                                        [ t4,  t5,   t6,   t7  ]  [ r0(1-r1)     ]
                                                        [ t8,  t9,   t10,  t11 ]  [ (1-r0)r1     ]
                                                        [ t12, t13,  t14,  t15 ]  [ r0*r1        ]
        """
        evals = f_mle.evals
        k = f_mle.num_var
        k2 = k // 2
        k1 = k - k2
        n1 = 2**k1
        n2 = 2**k2
        c_mat = []
        for i in range(n1):
            c_row = [evals[i*n2+j] for j in range(n2)]
            c_row_code = rs_encode(c_row, self.coset_gen, self.blowup_factor)
            c_mat.append(c_row_code)

        c_mat_T = matrix_transpose(c_mat)
        # print(f"c_mat_T={c_mat_T}")
        cm_vec = [MerkleTree(c_mat_T[i]) for i in range(len(c_mat_T))]
        # print(f"cm_vec={[cm_vec[i].root for i in range(len(cm_vec))]})")
        return Commitment(MerkleTree([cm.root for cm in cm_vec]))
    
    def prove_eval(self, 
              f_cm: Commitment, 
              f_mle: MLEPolynomial, 
              point: list[Fp], 
              transcript: MerlinTranscript) -> tuple[Fp, dict]:

        evals = f_mle.evals
        k = f_mle.num_var
        k2 = k // 2
        k1 = k - k2
        n1 = 2**k1
        n2 = 2**k2
        v = f_mle.evaluate(point)

        # Update transcript with the context
        transcript.absorb(b"f_code_merkle_root", f_cm.root)
        transcript.absorb(b"point", point)
        transcript.absorb(b"value", v)

        # Compute the A matrix 
        a_mat = []
        for i in range(n1):
            a_mat.append([evals[i*n2+j] for j in range(n2)])
        
        # Compute encoding of the A matrix
        a_mat_code = [rs_encode(a_mat[i], self.coset_gen, self.blowup_factor) for i in range(n1)]

        r1 = point[:k2]
        r2 = point[k2:]

        # Fold the (t_i) matrix vertically with (r2, r3)
        eq_r2 = MLEPolynomial.eqs_over_hypercube(r2)
        t_folded = []
        for j in range(n2):
            t_folded.append(inner_product(eq_r2, [a_mat[i][j] for i in range(n1)], Fp(0)))
        
        transcript.absorb(b"t_folded", t_folded)
        if self.debug > 0:
            print(f"P> t_folded = {t_folded}")
        
        if self.debug > 1:
            print(f"P> check folded matrix")
            t_folded_code = rs_encode(t_folded, self.coset_gen, self.blowup_factor)
            print(f"P> t_folded_code = {t_folded_code}")
            a_folded = []
            for j in range(n2*self.blowup_factor):
                a_folded.append(inner_product(eq_r2, [a_mat_code[i][j] for i in range(n1)], Fp(0)))
            print(f"P> a_folded = {a_folded}")
            assert t_folded_code == a_folded, f"t_folded_code != a_folded, {t_folded_code} != {a_folded}, a_mat_code = {a_mat_code}"
            print(f"P> check folded matrix passed")
            eq_r1 = MLEPolynomial.eqs_over_hypercube(r1)
            assert v == inner_product(t_folded, eq_r1, Fp(0)), f"v != inner_product(t_folded, eq_r1, Fp(0)), {v} != {inner_product(t_folded, eq_r1, Fp(0))}"
            print(f"P> check v passed")

        # Generate queries
        queries = []
        for i in range(self.num_queries):
            q = transcript.squeeze(int, b"query", 4) % n1
            queries.append(q)
        if self.debug > 0:
            print(f"P> queries={queries}")
        # Send sampled colums
        query_replies = []
        for q in queries:
            query_replies.append([a_mat_code[i][q] for i in range(n1)])

        if self.debug > 1:
            print(f"P> query_replies={query_replies}")
        
        merkle_paths = []
        for q, reply in zip(queries, query_replies):
            path = f_cm.tree.get_authentication_path(q)
            merkle_paths.append(path)
            transcript.absorb(b"query_reply", reply)
            transcript.absorb(b"merkle_path", path)

        if self.debug > 1:
            print(f"P> check query_replies")
            for i, (q, reply, path) in enumerate(zip(queries, query_replies, merkle_paths)):
                root_i = MerkleTree(reply).root
                print(f"P> i={i},root_i = {root_i}")
                assert root_i in f_cm.tree.data, f"root_i = {root_i} not in f_cm.tree.data"
                assert verify_decommitment(q, root_i, path, f_cm.tree.root), \
                    f"verify_decommitment failed at index {i}, q={q}, reply={reply}, path={path}, root={f_cm.tree.root}"
            print(f"P> check query_replies passed")

        return v, {
            "t_folded": t_folded,
            "query_replies": query_replies,
            "merkle_paths": merkle_paths
        }

    def verify_eval(self, 
                    f_mle_commitment: Commitment, 
                    point: list[Fp], 
                    evaluation: Fp,
                    argument: dict,
                    transcript: MerlinTranscript) -> bool:
        k = len(point)
        k2 = k // 2
        k1 = k - k2
        n1 = 2**k1
        n2 = 2**k2
        # Load the argument


        # Update transcript with the context
        transcript.absorb(b"f_code_merkle_root", f_mle_commitment.root)
        transcript.absorb(b"point", point)
        transcript.absorb(b"value", evaluation)

        t_folded = argument['t_folded']
        transcript.absorb(b"t_folded", t_folded)
        if self.debug > 0:
            print(f"V> t_folded={t_folded}")

        r1 = point[:k2]
        r2 = point[k2:]
        eq_r1 = MLEPolynomial.eqs_over_hypercube(r1)
        eq_r2 = MLEPolynomial.eqs_over_hypercube(r2)
        v_checked = inner_product(t_folded, eq_r1, Fp(0))
        assert v_checked == evaluation, f"v_checked = {v_checked} != evaluation = {evaluation}"
        if self.debug > 0:
            print(f"V> v_checked = {v_checked}")

        # Generate queries
        queries = []
        for i in range(self.num_queries):
            q = transcript.squeeze(int, b"query", 4) % n1
            queries.append(q)
        if self.debug > 0:
            print(f"V> queries={queries}")

        t_folded_code = rs_encode(t_folded, self.coset_gen, self.blowup_factor)
        query_replies = argument['query_replies']
        merkle_paths = argument['merkle_paths']
        for i, (q, reply, path) in enumerate(zip(queries, query_replies, merkle_paths)):
            transcript.absorb(b"query_reply", reply)
            transcript.absorb(b"merkle_path", path)
            root = MerkleTree(reply).root
            assert verify_decommitment(q, root, path, f_mle_commitment.root), \
                f"verify_decommitment failed at index {i}, q={q}, reply={reply}, path={path}, root={f_mle_commitment.root}"
            reply_folded = inner_product(eq_r2, reply, Fp(0))
            assert t_folded_code[q] == reply_folded, f"t_folded_code[q] = {t_folded_code[q]} != reply_folded = {reply_folded}"
        return True

def test_pcs():

    pcs = LIGERO_DP23_RS_PCS(MerkleTree, debug = 2)

    tr = MerlinTranscript(b"ligero-dp23-rs-pcs")

    # A simple instance f(x) = y
    evals = [Fp(2), Fp(3), Fp(4), Fp(5), Fp(6), Fp(7), Fp(8), Fp(9), \
             Fp(10), Fp(11), Fp(12), Fp(13), Fp(14), Fp(15), Fp(16), Fp(17)]
    us = [Fp(4), Fp(2), Fp(3), Fp(0)]
    eqs = MLEPolynomial.eqs_over_hypercube(us)
    
    y = inner_product(evals, eqs, Fp.zero())
    f_mle = MLEPolynomial(evals, 4)
    assert f_mle.evaluate(us) == y
    print(f"f(x[]) = {y}")
    f_cm = pcs.commit(f_mle)

    print("🕐 Generating proof ....")
    v, arg = pcs.prove_eval(f_cm, f_mle, us, tr.fork(b"basefold_rs_pcs"))
    print("ℹ️ Proof generated.")

    assert v == y
    print("🕐 Verifying proof ....")
    checked = pcs.verify_eval(f_cm, us, v, arg, tr.fork(b"basefold_rs_pcs"))
    assert checked
    print("✅ Proof verified")

if __name__ == "__main__":
    test_pcs()
