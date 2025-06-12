#!/usr/bin/env python3

# WARNING: This implementation may contain bugs and has not undergone auditing. 
# It is intended for educational and research purposes only.
# DO NOT use it in a production environment.

from utils import log_2, next_power_of_two, Scalar, is_power_of_two
from utils import inner_product, reverse_bits
from functools import reduce
from operator import mul


# Implementation of Ligerito PCS (RS encoding) [NA25]
#
# [NA25] Ligerito: A Small and Concretely Fast Polynomial Commitment Scheme
#
#  Authors: Andrija Novakovic and Guillermo Angeris
#  URL: https://angeris.github.io/papers/ligerito.pdf
#  URL: https://baincapitalcrypto.com/ligerito-a-small-and-concretely-fast-polynomial-commitment-scheme/

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
    assert is_power_of_two(blowup_factor), "blowup_factor must be a power of 2"

    n = next_power_of_two(len(f))
    N = n * blowup_factor

    omega_Nth = Fp.nth_root_of_unity(N)
    k = log_2(N)
    vec = f + [Fp.zero()] * (N - len(f))
    return UniPolynomialWithFft.fft_coset_rbo(vec, coset, k, omega=omega_Nth)

def tensor_vector_with_monomial_basis(vec: list[Fp]) -> list[Fp]:
    if len(vec) == 0:
        return [Fp(1)]
    v = vec[-1]
    vec_expanded = tensor_vector_with_monomial_basis(vec[:-1])
    vec_right = [vec_expanded[i] * v for i in range(len(vec_expanded))]
    return vec_expanded + vec_right

def tensor_vector_with_multilinear_basis(vec: list[Fp]) -> list[Fp]:
    if len(vec) == 0:
        return [Fp(1)]
    v = vec[-1]
    vec_expanded = tensor_vector_with_multilinear_basis(vec[:-1])
    vec_left = [vec_expanded[i] * (Fp(1)-v) for i in range(len(vec_expanded))]
    vec_right = [vec_expanded[i] * v for i in range(len(vec_expanded))]
    return vec_left + vec_right

def tensor_vector(index: int, k1: int, blowup_factor: int):
    N = 2**k1 * blowup_factor
    omega_Nth = Fp.nth_root_of_unity(N)
    index_rev = reverse_bits(index, log_2(N))
    omega = omega_Nth**index_rev
    return [omega**(2**i) for i in range(k1)]

def tensor_inner_product(r_vec, index: int, f_len:int, blowup_factor):
    n = next_power_of_two(f_len)
    N = n * blowup_factor
    omega_Nth = Fp.nth_root_of_unity(N)
    index_rev = reverse_bits(index, log_2(N))
    omega = omega_Nth**index_rev
    l = len(r_vec)
    ip = [inner_product([Fp(1)-r_vec[i], r_vec[i]], [1, omega**(2**i)], Fp(0)) for i in range(l)]
    product = reduce(mul, ip, Fp(1))
    return product

def rs_generator_matrix_at_row(index:int, f_len: int, coset:Fp, blowup_factor:int) -> list[Fp]:
    n = next_power_of_two(f_len)
    N = n * blowup_factor
    omega_Nth = Fp.nth_root_of_unity(N)
    index_rev = reverse_bits(index, log_2(N))
    omega = omega_Nth**index_rev
    return [coset* omega**i for i in range(n)]

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

class LIGERITO_RS_PCS:

    blowup_factor = 2 # WARNING: this is not secure
    num_queries = 3   # WARNING: this is not secure
    # coset_gen = Fp.multiplicative_generator()
    coset_gen = Fp(1)
    folding_step_size = 1

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
              f_mle_commitment: Commitment, 
              f_mle: MLEPolynomial, 
              point: list[Fp], 
              transcript: MerlinTranscript) -> tuple[Fp, dict]:

        evals = f_mle.evals
        k = f_mle.num_var
        k1_prime = 2
        k1 = k - k1_prime
        n1 = 2**k1
        n1_prime = 2**k1_prime
        v = f_mle.evaluate(point)

        # Update transcript with the context
        transcript.absorb(b"f_code_merkle_root", f_mle_commitment.root)
        transcript.absorb(b"point", point)
        transcript.absorb(b"value", v)

        # Compute the A matrix 
        a_mat = []
        for i in range(n1_prime):
            a_mat.append([evals[i*n1+j] for j in range(n1)])
        
        # Compute encoding of the A matrix
        a_mat_code = [rs_encode(a_mat[i], self.coset_gen, self.blowup_factor) for i in range(n1_prime)]

        # Sumcheck and fold

        f = f_mle.evals
        eq = MLEPolynomial.eqs_over_hypercube(point)
        sumcheck_h_vec = []
        sum_checked = v
        r_vec = []
        for i in range(k1_prime):
            if self.debug > 0:
                print(f"P> sumcheck round {i}")
            half = len(f) // 2
            f_low = f[:half]
            f_high = f[half:]
            eq_low = eq[:half]
            eq_high = eq[half:]

            h_eval_at_0 = sum([f_low[j] * eq_low[j] for j in range(half)], Fp(0))
            h_eval_at_1 = sum([f_high[j] * eq_high[j] for j in range(half)], Fp(0))
            h_eval_at_2 = sum([ (2 * f_high[j] - f_low[j]) * (2 * eq_high[j] - eq_low[j]) for j in range(half)], Fp(0))

            h = [h_eval_at_0, h_eval_at_1, h_eval_at_2]
            sumcheck_h_vec.append(h)

            transcript.absorb(b"h(X)", h)

            if self.debug > 0:
                print(f"P> h = {h}")

            assert h_eval_at_0 + h_eval_at_1 == sum_checked, \
                f"h_eval_at_0 + h_eval_at_1 = {h_eval_at_0 + h_eval_at_1}, sum_checked = {sum_checked}"

            r = transcript.squeeze(Fp, b"r", 4)

            r_vec.append(r)
    
            # fold f

            f_folded = [(Fp(1) - r) * f_low[i] + r * f_high[i] for i in range(half)]
            eq_folded = [(Fp(1) - r) * eq_low[i] + r * eq_high[i] for i in range(half)]

            f = f_folded
            eq = eq_folded

            sum_checked = UniPolynomial.evaluate_from_evals(h, 
                    r, [Fp(0), Fp(1), Fp(2)])
            
        # End of sumcheck and folding loop

        eq_r = MLEPolynomial.eqs_over_hypercube(r_vec[::-1])
        if self.debug > 0:
            print(f"P> check folded f")
            t_folded = []

            for j in range(n1):
                t_folded.append(inner_product(eq_r, [a_mat[i][j] for i in range(n1_prime)], Fp(0)))
            assert t_folded == f_folded, f"t_folded = {t_folded} != f_folded = {f_folded}"
            print(f"P> check folded f passed")

        transcript.absorb(b"f_folded", f_folded)

        if self.debug > 0:
            print(f"P> f_folded = {f_folded}")
        
        if self.debug > 1:
            print(f"P> check folded matrix")
            f_folded_code = rs_encode(f_folded, self.coset_gen, self.blowup_factor)
            print(f"P> f_folded_code = {f_folded_code}")
            a_folded = []
            for j in range(n1*self.blowup_factor):
                a_folded.append(inner_product(eq_r, [a_mat_code[i][j] for i in range(n1_prime)], Fp(0)))
            print(f"P> a_folded = {a_folded}")      
            assert f_folded_code == a_folded, f"f_folded_code != a_folded, {f_folded_code} != {a_folded}, a_mat_code = {a_mat_code}"
            assert sum_checked == inner_product(f_folded, eq, Fp(0)), f"v != inner_product(f_folded, eq, Fp(0)), {v} != {inner_product(f_folded, eq, Fp(0))}"
            print(f"P> check folded matrix passed")

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
            query_replies.append([a_mat_code[i][q] for i in range(n1_prime)])
        if self.debug > 1:
            print(f"P> query_replies={query_replies}")
        
        merkle_paths = []
        for q, reply in zip(queries, query_replies):
            path = f_mle_commitment.tree.get_authentication_path(q)
            merkle_paths.append(path)
            transcript.absorb(b"query_reply", reply)
            transcript.absorb(b"merkle_path", path)

        if self.debug > 1:
            print(f"P> check query_replies")
            for i, (q, reply, path) in enumerate(zip(queries, query_replies, merkle_paths)):
                root_i = MerkleTree(reply).root
                print(f"P> i={i},root_i = {root_i}")
                assert root_i in f_mle_commitment.tree.data, f"root_i = {root_i} not in f_cm.tree.data"
                assert verify_decommitment(q, root_i, path, f_mle_commitment.tree.root), \
                    f"verify_decommitment failed at index {i}, q={q}, reply={reply}, path={path}, root={f_mle_commitment.tree.root}"
            print(f"P> check query_replies passed")

        return v, {
            "f_folded": f_folded,
            "sumcheck_h_vec": sumcheck_h_vec,
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
        k1_prime = 2
        k1 = k - k1_prime
        n1 = 2**k1
        n1_prime = 2**k1_prime

        # Update transcript with the context
        transcript.absorb(b"f_code_merkle_root", f_mle_commitment.root)
        transcript.absorb(b"point", point)
        transcript.absorb(b"value", evaluation)


        eq = MLEPolynomial.eqs_over_hypercube(point)

        # Sumcheck and fold eq
        sumcheck_h_vec = argument['sumcheck_h_vec']
        sum_checked = evaluation 
        r_vec = []
        for i in range(k1_prime):
            half = len(eq) // 2
            eq_low = eq[:half]
            eq_high = eq[half:]
            h = sumcheck_h_vec[i]
            h_eval_at_0 = h[0]
            h_eval_at_1 = h[1]
            h_eval_at_2 = h[2]

            transcript.absorb(b"h(X)", h)

            assert h_eval_at_0 + h_eval_at_1 == sum_checked, \
                f"h_eval_at_0 + h_eval_at_1 = {h_eval_at_0 + h_eval_at_1}, sum_checked = {sum_checked}"
            
            r = transcript.squeeze(Fp, b"r", 4)
            if self.debug > 0:
                print(f"V> r[{i}] = {r}")
            r_vec.append(r)

            # fold eq
            eq = [(Fp(1) - r) * eq_low[i] + r * eq_high[i] for i in range(half)]

            sum_checked = UniPolynomial.evaluate_from_evals(h, r, [Fp(0), Fp(1), Fp(2)])

        f_folded = argument['f_folded']
        transcript.absorb(b"f_folded", f_folded)
        if self.debug > 0:
            print(f"V> f_folded={f_folded}")

        # Generate queries
        queries = []
        for i in range(self.num_queries):
            q = transcript.squeeze(int, b"query", 4) % n1
            queries.append(q)
        if self.debug > 0:
            print(f"V> queries={queries}")
        
        query_replies = argument['query_replies']
        merkle_paths = argument['merkle_paths']

        f_folded_code = rs_encode(f_folded, self.coset_gen, self.blowup_factor)
        assert sum_checked == inner_product(f_folded, eq, Fp(0)), \
            f"sum_checked = {sum_checked} != inner_product(f_folded, eq, Fp(0)) = {inner_product(f_folded, eq, Fp(0))}"

        eq_r = MLEPolynomial.eqs_over_hypercube(r_vec[::-1])
        for i, (q, reply, path) in enumerate(zip(queries, query_replies, merkle_paths)):
            transcript.absorb(b"query_reply", reply)
            transcript.absorb(b"merkle_path", path)
            root = MerkleTree(reply).root
            assert verify_decommitment(q, root, path, f_mle_commitment.root), \
                f"verify_decommitment failed at index {i}, q={q}, reply={reply}, path={path}, root={f_mle_commitment.root}"
            assert inner_product(eq_r, reply, Fp(0)) == f_folded_code[q], \
                f"inner_product(eq_r, reply, Fp(0)) = {inner_product(eq_r, reply, Fp(0))} != f_folded_code[q] = {f_folded_code[q]}"

        return True


    def prove_eval_multiple_iterations(self, 
              f_mle_commitment: Commitment, 
              f_mle: MLEPolynomial, 
              point: list[Fp], 
              transcript: MerlinTranscript) -> tuple[Fp, dict]:

        evals = f_mle.evals
        k = f_mle.num_var
        eval_at_point = f_mle.evaluate(point)

        ks = []
        k1 = k
        while k1 > 0:
            k1_prime = self.folding_step_size
            k2 = k1 - k1_prime
            if k2 > 0: 
                ks.append((k1_prime, k2))
                k1 = k2
            else:
                ks.append((k1, 0))
                break
        
        if self.debug > 1:
            print(f"P> check ks={ks}")
            assert k == sum([ks[i][0] for i in range(len(ks))]), f"k = {k} != sum(ks) = {sum([ks[i][0] for i in range(len(ks))])}"
            print(f"P> check ks passed")
        
        # Update transcript with the context
        transcript.absorb(b"f_code_merkle_root", f_mle_commitment.root)
        transcript.absorb(b"point", point)
        transcript.absorb(b"value", eval_at_point)
        f = f_mle.evals
        eq = MLEPolynomial.eqs_over_hypercube(point)

        f_code_cm_vec = []
        sum_checked = eval_at_point
        sumcheck_h_vec_vec = []
        query_replies_vec = []
        merkle_paths_vec = []
        v_vec_vec = []
        for iteration in range(len(ks)-1):
            k1_prime = ks[iteration][0]
            k1 = ks[iteration][1]

            n1_prime = 2**k1_prime
            n1 = 2**k1

            # Compute the A matrix 
            a_mat = []
            for i in range(n1_prime):
                a_mat.append([f[i*n1+j] for j in range(n1)])
            
            # Compute encoding of the A matrix
            a_mat_code = [rs_encode(a_mat[i], self.coset_gen, self.blowup_factor) for i in range(n1_prime)]

            root_vec = [MerkleTree([a_mat_code[i][j] for i in range(n1_prime)]).root for j in range(n1*self.blowup_factor)]
            a_mat_code_cm = Commitment(MerkleTree(root_vec))
            f_code_cm_vec.append(a_mat_code_cm)

            # Sumcheck and fold
            sumcheck_h_vec = []
            r_vec = []
            v_vec = []

            for i in range(k1_prime):
                if self.debug > 0:
                    print(f"P> Iteration {iteration}, sumcheck round {i}")

                half = len(f) // 2
                f_low = f[:half]
                f_high = f[half:]
                eq_low = eq[:half]
                eq_high = eq[half:]

                h_eval_at_0 = sum([f_low[j] * eq_low[j] for j in range(half)], Fp(0))
                h_eval_at_1 = sum([f_high[j] * eq_high[j] for j in range(half)], Fp(0))
                h_eval_at_2 = sum([ (2 * f_high[j] - f_low[j]) * (2 * eq_high[j] - eq_low[j]) for j in range(half)], Fp(0))

                h = [h_eval_at_0, h_eval_at_1, h_eval_at_2]
                sumcheck_h_vec.append(h)

                transcript.absorb(b"h(X)", h)

                if self.debug > 0:
                    print(f"P> h = {h}")

                assert h_eval_at_0 + h_eval_at_1 == sum_checked, \
                    f"h_eval_at_0 + h_eval_at_1 = {h_eval_at_0 + h_eval_at_1}, sum_checked = {sum_checked}"

                r = transcript.squeeze(Fp, b"r", 4)

                r_vec.append(r)
        
                # fold f
                f = [(Fp(1) - r) * f_low[i] + r * f_high[i] for i in range(half)]
                eq = [(Fp(1) - r) * eq_low[i] + r * eq_high[i] for i in range(half)]

                sum_checked = UniPolynomial.evaluate_from_evals(h, r, [Fp(0), Fp(1), Fp(2)])
                
            # End of sumcheck and folding loop

            eq_r = MLEPolynomial.eqs_over_hypercube(r_vec[::-1])

            if self.debug > 1:
                print(f"P> check folded f")
                f_folded = []
                for j in range(n1):
                    f_folded.append(inner_product(eq_r, [a_mat[i][j] for i in range(n1_prime)], Fp(0)))
                assert f_folded == f, f"f_folded = {f_folded} != f = {f}"
                print(f"P> check folded f passed")

            if self.debug > 0:
                print(f"P> f_folded = {f_folded}")
            
            if self.debug > 1:
                print(f"P> check folded matrix")
                f_folded_code = rs_encode(f_folded, self.coset_gen, self.blowup_factor)
                print(f"P> f_folded_code = {f_folded_code}")
                a_folded = []
                for j in range(n1*self.blowup_factor):
                    a_folded.append(inner_product(eq_r, [a_mat_code[i][j] for i in range(n1_prime)], Fp(0)))
                print(f"P> a_folded = {a_folded}")      
                assert f_folded_code == a_folded, f"f_folded_code != a_folded, {f_folded_code} != {a_folded}, a_mat_code = {a_mat_code}"
                assert sum_checked == inner_product(f_folded, eq, Fp(0)), f"v != inner_product(f_folded, eq, Fp(0)), {v} != {inner_product(f_folded, eq, Fp(0))}"
                print(f"P> check folded matrix passed")

            # Generate queries
            queries = []
            for i in range(self.num_queries):
                q = transcript.squeeze(int, b"query", 4) % (n1 * self.blowup_factor)
                queries.append(q)
            if self.debug > 0:
                print(f"P> queries={queries}")
            
            # Send sampled colums
            query_replies = []
            for q in queries:
                query_replies.append([a_mat_code[i][q] for i in range(n1_prime)])
            if self.debug > 1:
                print(f"P> query_replies={query_replies}")
            
            merkle_paths = []
            for i, (q, reply) in enumerate(zip(queries, query_replies)):
                path = a_mat_code_cm.tree.get_authentication_path(q)
                merkle_paths.append(path)
                transcript.absorb(b"query_reply", reply)
                transcript.absorb(b"merkle_path", path)

                v = inner_product(eq_r, reply, Fp(0))
                transcript.absorb(b"v", v)
                if self.debug > 0:
                    print(f"P> v[{i}] = {v}, q={q}")
                v_vec.append(v)

                beta = transcript.squeeze(Fp, b"beta", 4)
                if self.debug > 0:
                    print(f"P> beta[{i}] = {beta}, q={q}")
                sum_checked += beta * v
                rs_w = rs_generator_matrix_at_row(q, len(f), self.coset_gen, self.blowup_factor)
                eq = [eq[j] + beta * rs_w[j] for j in range(len(eq))]

            if self.debug > 1:
                print(f"P> check query_replies")
                for i, (q, reply, path) in enumerate(zip(queries, query_replies, merkle_paths)):
                    root_i = MerkleTree(reply).root
                    print(f"P> iteration={iteration}, i={i},root_i = {root_i}")
                    assert root_i in a_mat_code_cm.tree.data, f"root_i = {root_i} not in f_cm.tree.data"
                    assert verify_decommitment(q, root_i, path, a_mat_code_cm.tree.root), \
                        f"verify_decommitment failed at index {i}, q={q}, reply={reply}, path={path}, root={f_mle_commitment.tree.root}"
                    print(f"P> verify_decommitment passed,q={q}, root_i={root_i}, path={path}, root={a_mat_code_cm.tree.root}")
                    rs_w = rs_generator_matrix_at_row(q, len(f), self.coset_gen, self.blowup_factor)
                    assert inner_product(rs_w, f, Fp(0)) == inner_product(eq_r, reply, Fp(0)), \
                        f"inner_product(rs_w, f, Fp(0)) = {inner_product(rs_w, f, Fp(0))} != inner_product(eq_r, reply, Fp(0)) = {inner_product(eq_r, reply, Fp(0))}"

                print(f"P> check query_replies passed")
            sumcheck_h_vec_vec.append(sumcheck_h_vec)
            query_replies_vec.append(query_replies)
            v_vec_vec.append(v_vec)
            merkle_paths_vec.append(merkle_paths)

        # End of iteration

        transcript.absorb(b"f_folded", f)
        if self.debug > 1:
            print(f"P> check f_folded={f}")
            assert sum_checked == inner_product(f, eq, Fp(0)), f"v != inner_product(f, eq, Fp(0)), {v} != {inner_product(f, eq, Fp(0))}"
            print(f"P> check f_folded passed")

        return eval_at_point, {
            "f_folded": f,
            "f_folded_cm_vec": f_code_cm_vec,
            "sumcheck_h_vec_vec": sumcheck_h_vec_vec,
            "query_replies_vec": query_replies_vec,
            "v_vec_vec": v_vec_vec,
            "merkle_paths_vec": merkle_paths_vec,
        }

    def verify_eval_multiple_iterations(self, 
                    f_mle_commitment: Commitment, 
                    point: list[Fp], 
                    evaluation: Fp,
                    argument: dict,
                    transcript: MerlinTranscript) -> bool:
        k = len(point)
        ks = []
        k1 = k
        while k1 > 0:
            k1_prime = self.folding_step_size
            k2 = k1 - k1_prime
            if k2 > 0: 
                ks.append((k1_prime, k2))
                k1 = k2
            else:
                ks.append((k1, 0))
                break

        print(f"V> ks = {ks}")  

        # Update transcript with the context
        transcript.absorb(b"f_code_merkle_root", f_mle_commitment.root)
        transcript.absorb(b"point", point)
        transcript.absorb(b"value", evaluation)

        ## NOTE: the following eq polynomial computation (in O(n)) is replaced by 
        #   the accumulated (sunccinct) computation in the end (in O(log n)) as in
        #   Section 6.6 of the paper.
        
        ## eq = MLEPolynomial.eqs_over_hypercube(point)

        # Sumcheck and fold eq
        f_folded_cm_vec = argument['f_folded_cm_vec']
        sumcheck_h_vec_vec = argument['sumcheck_h_vec_vec']
        query_replies_vec = argument['query_replies_vec']
        merkle_paths_vec = argument['merkle_paths_vec']
        v_vec_vec = argument['v_vec_vec']
        sum_checked = evaluation 
        r_vec_vec = []
        beta_vec_vec = []
        queries_vec = []
        for iteration in range(len(ks)-1):
            k1_prime = ks[iteration][0]
            k1 = ks[iteration][1]

            n1_prime = 2**k1_prime
            n1 = 2**k1

            sumcheck_h_vec = sumcheck_h_vec_vec[iteration]
            query_replies = query_replies_vec[iteration]
            merkle_paths = merkle_paths_vec[iteration]

            r_vec = []
            for i in range(k1_prime):
                ## half = len(eq) // 2
                ## eq_low = eq[:half]
                ## eq_high = eq[half:]
                h = sumcheck_h_vec[i]
                h_eval_at_0 = h[0]
                h_eval_at_1 = h[1]

                transcript.absorb(b"h(X)", h)

                if self.debug > 0:
                    print(f"V> h = {h}")

                assert h_eval_at_0 + h_eval_at_1 == sum_checked, \
                    f"h_eval_at_0 + h_eval_at_1 = {h_eval_at_0 + h_eval_at_1}, sum_checked = {sum_checked}"
                
                r = transcript.squeeze(Fp, b"r", 4)
                if self.debug > 0:
                    print(f"V> r[{i}] = {r}")
                r_vec.append(r)

                ## fold eq
                ## eq = [(Fp(1) - r) * eq_low[i] + r * eq_high[i] for i in range(half)]

                sum_checked = UniPolynomial.evaluate_from_evals(h, r, [Fp(0), Fp(1), Fp(2)])

            # Generate queries
            queries = []
            for i in range(self.num_queries):
                q = transcript.squeeze(int, b"query", 4) % (n1 * self.blowup_factor)
                queries.append(q)
            if self.debug > 0:
                print(f"V> queries={queries}")
            
            query_replies = query_replies_vec[iteration]
            merkle_paths = merkle_paths_vec[iteration]
            v_vec = v_vec_vec[iteration]
            f_code_cm = f_folded_cm_vec[iteration]
            # eq_r = MLEPolynomial.eqs_over_hypercube(r_vec[::-1])
            beta_vec = []
            for i, (q, reply, path) in enumerate(zip(queries, query_replies, merkle_paths)):
                transcript.absorb(b"query_reply", reply)
                transcript.absorb(b"merkle_path", path)

                transcript.absorb(b"v", v_vec[i])
                if self.debug > 0:
                    print(f"V> v[{i}] = {v_vec[i]}, q={q}")
                beta = transcript.squeeze(Fp, b"beta", 4)
                if self.debug > 0:
                    print(f"V> beta[{i}] = {beta}, q={q}")
                beta_vec.append(beta)

                sum_checked += beta * v_vec[i]
                ## rs_w = rs_generator_matrix_at_row(q, len(eq), self.coset_gen, self.blowup_factor)
                ## eq = [eq[j] + beta * rs_w[j] for j in range(len(eq))]
                root = MerkleTree(reply).root
                assert verify_decommitment(q, root, path, f_code_cm.root), \
                    f"verify_decommitment failed at index {i}, q={q}, reply={reply}, path={path}, root={f_code_cm.root}"
                # print(f"V> verify_decommitment passed,q={q}, root_i={root}, path={path}, root={f_code_cm.root}")

                # assert inner_product(eq_r, reply, Fp(0)) == f_folded_code[q], \
                #     f"inner_product(eq_r, reply, Fp(0)) = {inner_product(eq_r, reply, Fp(0))} != f_folded_code[q] = {f_folded_code[q]}"
            
            queries_vec.append(queries)
            r_vec_vec.append(r_vec)
            beta_vec_vec.append(beta_vec)
        # End of iteration

        ## print(f"V> final eq0= {eq}")

        k_last = ks[-1][0]
        r_vec_all = [x for rs in r_vec_vec for x in rs][::-1]
        print(f"V> r_vec_all = {r_vec_all}")
        assert len(r_vec_all) == k - k_last, f"len(r_vec_all) = {len(r_vec_all)} != k - k_last = {k - k_last}"
        
        # Compute the folded eq polynomial
        scalar = MLEPolynomial.evaluate_eq_polynomial(point[k_last:], r_vec_all)
        eq_acc = MLEPolynomial.eqs_over_hypercube(point[:k_last])
        eq_acc = [eq_acc[j] * scalar for j in range(2**k_last)]

        # Accumulate the eq polynomial
        for iteration in range(len(ks)-1):
            k1_prime = ks[iteration][0]
            k1 = ks[iteration][1]
            n1 = 2**k1
            # query_replies = query_replies_vec[iteration]
            beta_vec = beta_vec_vec[iteration]
            queries = queries_vec[iteration]
            r_vec = r_vec_all[:k1-k_last]
            print(f"V> r_vec = {r_vec}")
            for i, q in enumerate(queries):
                w_rev = tensor_vector(q, k1, self.blowup_factor)
                scalar = reduce(mul, [inner_product([Fp(1)-r_vec[j], r_vec[j]], [1, w_rev[k_last:][j]], Fp(0)) for j in range(len(r_vec))], Fp(1))
                new_vec = tensor_vector_with_monomial_basis(w_rev[:k_last])
                new_vec = [new_vec[j] * scalar for j in range(2**k_last)]
                eq_acc = [eq_acc[j] + beta_vec[i] * new_vec[j] for j in range(2**k_last)]

            print(f"V> iteration={iteration}, eq_acc = {eq_acc}")   

        f_folded = argument['f_folded']
        transcript.absorb(b"f_folded", f_folded)
        if self.debug > 0:
            print(f"V> f_folded={f_folded}")

        # NOTE: Uncomment this line to check the accumulated eq polynomial
        # assert eq == eq_acc, f"eq != eq_acc, {eq} != {eq_acc}"

        assert sum_checked == inner_product(f_folded, eq_acc, Fp(0)), \
            f"sum_checked = {sum_checked} != inner_product(f_folded, eq, Fp(0)) = {inner_product(f_folded, eq_acc, Fp(0))}"
        
        return True

def test_pcs():

    pcs = LIGERITO_RS_PCS(MerkleTree, debug = 2)

    tr = MerlinTranscript(b"ligerito-rs-pcs")

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
 
def test_multiple_iterations_pcs():

    pcs = LIGERITO_RS_PCS(MerkleTree, debug = 2)

    tr = MerlinTranscript(b"ligerito-rs-pcs")

    # # A simple instance f(x) = y
    evals = [Fp(2), Fp(3), Fp(4), Fp(5), Fp(6), Fp(7), Fp(8), Fp(9), \
             Fp(10), Fp(11), Fp(12), Fp(13), Fp(14), Fp(15), Fp(16), Fp(17)]
    us = [Fp(4), Fp(2), Fp(3), Fp(0)]

    # # A simple instance f(x) = y
    # evals = [Fp(2), Fp(3), Fp(4), Fp(5), Fp(6), Fp(7), Fp(8), Fp(9)]
    # us = [Fp(3), Fp(2), Fp(2)]

    eqs = MLEPolynomial.eqs_over_hypercube(us)
    
    y = inner_product(evals, eqs, Fp.zero())
    f_mle = MLEPolynomial(evals, log_2(len(evals)))
    assert f_mle.evaluate(us) == y
    print(f"f({us}) = {y}")
    f_cm = pcs.commit(f_mle)

    print("🕐 Generating proof ....")
    v, arg = pcs.prove_eval_multiple_iterations(f_cm, f_mle, us, tr.fork(b"ligerito"))
    print("ℹ️ Proof generated.")

    assert v == y
    print("🕐 Verifying proof ....")
    checked = pcs.verify_eval_multiple_iterations(f_cm, us, v, arg, tr.fork(b"ligerito"))
    assert checked
    print("✅ Proof verified")

if __name__ == "__main__":
    # test_pcs()
    test_multiple_iterations_pcs()
