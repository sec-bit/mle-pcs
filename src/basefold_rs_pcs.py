#!/usr/bin/env python3

# WARNING: This implementation may contain bugs and has not undergone auditing. 
# It is intended for educational and research purposes only.
# DO NOT use it in a production environment.

from utils import log_2, next_power_of_two, query_num, delta_johnson_bound
from utils import inner_product, Scalar

# WARNING: 
#   1. For demonstration, we deliberately use an insecure random number 
#      generator, random.Random. To generate secure randomness, use 
#      the standard library `secrets` instead.
#        
#      See more here: https://docs.python.org/3/library/secrets.html
#
#   2. Challenges are only 1 byte long for simplicity, which is not secure.

import random

# Implementation of Basefold (RS encoding) PCS [ZCF23]
#
# [ZCF23] BaseFold: Efficient Field-Agnostic Polynomial Commitment 
#           Schemes from Foldable Codes
#  Author: Hadas Zeilberger, Binyi Chen and Ben Fisch
#  URL: https://eprint.iacr.org/2023/1705

from curve import Fr as BN254_Fr
from merlin.merlin_transcript import MerlinTranscript
from mle2 import MLEPolynomial
from unipoly2 import UniPolynomial, UniPolynomialWithFft, bit_reverse_permutation
from merkle import MerkleTree, verify_decommitment

# TODO:
#
#  - [ ] Make security parameters configurable
#  - [ ] Add batching proving/verifying

Field = BN254_Fr

class Commitment:

    def __init__(self, tree: MerkleTree):
        self.tree = tree
        self.cm = tree.root
        self.root = tree.root

    def __repr__(self):
        return f"Commitment(len={len(self.tree.data)}, root={self.cm})"

# class Oracle:
    
#     def __init__(self, vector: list[Field]):
#         self.vector = vector

#     def open(self, index: int, value: Field, proof: list[Field]) -> bool:
#         return False
    
#     def get_proof(self, index: int, value: Field) -> list[Field]:
#         raise NotImplementedError

#     def query(self, index: int) -> Field:
#         return self.vector[index]

#     def commit(self, f_mle: MLEPolynomial) -> Commitment:
#         raise NotImplementedError


def rs_encode(f: list[Field], coset: Field, blowup_factor: int) -> list[Field]:
    n = next_power_of_two(len(f))
    N = n * blowup_factor

    omega_Nth = Field.nth_root_of_unity(N)
    # print(f"omega_Nth = {omega_Nth}")
    k = log_2(N)
    # print(f"n = {n}, N = {N}, k = {k}")
    vec = f + [Field.zero()] * (N - len(f))
    # print(f"vec = {vec}, len(vec) = {len(vec)}")
    return UniPolynomialWithFft.fft_coset_rbo(vec, coset, k, omega=omega_Nth)

class BASEFOLD_RS_PCS:

    blowup_factor = 8
    coset_gen = Field.multiplicative_generator()
    max_queries_try = 1000  # NOTE: change it to a practical number
    security_bits = 128

    @property
    def num_queries(self):
        return query_num(self.blowup_factor, self.security_bits, delta_johnson_bound)

    def __init__(self, oracle, debug: int = 0):
        """
        Args:
            oracle: the oracle to use for the proof
        """
        self.oracle = oracle
        # self.rng = random.Random("basefold-rs-pcs")
        self.debug = debug

    def commit(self, f_mle: MLEPolynomial) -> Commitment:
        """
        Commit to the evaluations of the MLE polynomial.
        """
        evals = f_mle.evals

        f_code = rs_encode(evals, self.coset_gen, self.blowup_factor)
        f_tree = MerkleTree(f_code)

        assert len(f_code) == 2**f_mle.num_var * self.blowup_factor, \
            f"len(evals)={len(evals)}, f_mle.num_var={f_mle.num_var}, blowup_factor={self.blowup_factor}"
        cm = Commitment(f_tree)
        return cm
    
    def prove_eval(self, 
                    f_cm: Commitment, 
                    f_mle: MLEPolynomial, 
                    us: list[Field], 
                    tr: MerlinTranscript) -> tuple[Field, dict]:
        """
        Generate evaluation proof for f_mle(us) = v

        Args:
            f_cm: the commitment to the polynomial
            f_mle: the MLE polynomial to evaluate
            us: the evaluation point
            tr: the proof transcript

        Returns:
            tuple[Field, dict]: the evaluation value and the argument
        """

        assert f_mle.num_var == len(us), f"f_mle.num_var={f_mle.num_var}, len(us)={len(us)}"

        k = f_mle.num_var
        
        # Evaluate f_mle at the point us
        v = f_mle.evaluate(us)
        f = f_mle.evals.copy()
        n = 2**k

        if self.debug > 0:
            print(f"P> f_len={len(f)}, k={k}, c_len ={len(f)*self.blowup_factor}")

        eq = MLEPolynomial.eqs_over_hypercube(us)
        eq_mle = MLEPolynomial(eq, k)

        # > Preparation

        f_code_len = len(f) * self.blowup_factor

        # precompute twiddles for FFT
        # NOTE: the array of twiddles are bit-reversed, such that it can be reused for all rounds.
        twiddles = UniPolynomialWithFft.precompute_twiddles_for_fft(f_code_len, is_bit_reversed=True)

        f0_code = rs_encode(f, self.coset_gen, self.blowup_factor)

        # Update transcript with the context
        tr.absorb(b"f_code_merkle_root", f_cm.cm)
        tr.absorb(b"point", us)
        tr.absorb(b"value", v)

        if self.debug > 1:
            print(f"P> check f0_code")
            f_orig_evals = bit_reverse_permutation(f0_code)
            f_orig_coeffs = UniPolynomialWithFft.ifft_coset(f_orig_evals, self.coset_gen, k+log_2(self.blowup_factor))
            f_orig = UniPolynomial(f_orig_coeffs)
            assert f_orig.coeffs == f, "f_orig != f0"
            print(f"P> check f0_code passed")

        # > Commit-phase 

        sum_checked = v
        half = n >> 1
        f_code = f0_code
        coset = self.coset_gen
        constant = None
        alpha_vec = []
        sumcheck_h_vec = []
        code_commitments = []
        trees = [MerkleTree(f_code)]
        codes = [f_code]

        for i in range(k):
            if self.debug > 0:
                print(f"P> Round {i}")

            f_even = f[::2]
            f_odd = f[1::2]
            eq_even = eq[::2]
            eq_odd = eq[1::2]

            # construct h(X)
            h_eval_at_0 = sum([f_even[j] * eq_even[j] for j in range(half)], Field.zero())
            h_eval_at_1 = sum([f_odd[j] * eq_odd[j] for j in range(half)], Field.zero())
            h_eval_at_2 = sum([ (2 * f_odd[j] - f_even[j]) * (2 * eq_odd[j] - eq_even[j]) for j in range(half)])
            h = [h_eval_at_0, h_eval_at_1, h_eval_at_2]
            sumcheck_h_vec.append(h)

            tr.absorb(b"h(X)", h)

            # check sum
            assert h_eval_at_0 + h_eval_at_1 == sum_checked, \
                f"h_eval_at_0 + h_eval_at_1 = {h_eval_at_0 + h_eval_at_1}, sum_checked = {sum_checked}"
            
            # Receive a random number from the verifier
            alpha = tr.squeeze(Field, b"alpha", 4)
            if self.debug > 0:
                print(f"P> alpha[{i}] = {alpha}")
                
            alpha_vec.append(alpha)

            # fold f

            f_folded = [(Field(1) - alpha) * f_even[j] + alpha * f_odd[j] for j in range(half)]
            eq_folded = [(Field(1) - alpha) * eq_even[j] + alpha * eq_odd[j] for j in range(half)]

            f = f_folded
            eq = eq_folded

            # update sumcheck for the next round
            sum_checked = UniPolynomial.evaluate_from_evals(h, alpha, [Field(0), Field(1), Field(2)])

            # fold f_code
            f_code_folded = [(Field(1)-alpha) * (f_code[2*j] + f_code[2*j+1]) / 2 
                      + alpha * (f_code[2*j] - f_code[2*j+1]) / (2 * coset * twiddles[j]) 
                      for j in range(len(f_code)//2)]
            if i == k-1:
                constant = f_code_folded[0]
                
                assert all([f_code_folded[j] == constant for j in range(len(f_code_folded))]), \
                    f"the final f_code_folded is not constant, f_code_folded = {f_code_folded}"
                
                tr.absorb(b"f_code_merkle_root", constant)

            else:
                tree = MerkleTree(f_code_folded)
                trees.append(tree)
                codes.append(f_code_folded)
                code_commitments.append(tree.root)
                tr.absorb(b"f_code_merkle_root", tree.root)

            # update parameters for the next round
            f_code = f_code_folded
            half >>= 1
            coset *= coset

        ## End of the big loop for `i`

        eq_mle_at_alpha = eq_mle.evaluate(alpha_vec)
        assert sum_checked == constant * eq_mle_at_alpha, \
            f"sum_checked = {sum_checked}, constant = {constant}, eq_mle_at_alpha = {eq_mle_at_alpha}"
        if self.debug > 0:
            print(f"P> final_sum({sum_checked}) = f(alpha_vec)*eq(alpha_vec), {constant} * {eq_mle_at_alpha}")

        # > Query-phase 
        
        queries = []
        for i in range(self.max_queries_try):
            new_query = tr.squeeze(int, b"query", 24) % (len(f0_code)//2)
            if new_query*2 in queries:
                continue
            queries.append(new_query*2)
            if len(queries) >= self.num_queries:
                break
        if len(queries) < self.num_queries:
            raise ValueError(f"Failed to generate {self.num_queries} queries")
        
        # Construct query paths
        query_indices = []
        query_paths = []
        for q in queries:
            # num_vars_copy = num_vars
            cur_path = []
            indices = []
            prev_idx = q
            for c in codes:
                x0, x1 = int(prev_idx//2*2), int(prev_idx//2*2+1)
                # print(f"q={q}, prev_idx={prev_idx}, x0={x0}, x1={x1}")
                cur_path.append((c[x0], c[x1]))
                # if prev_idx % 2 == 0 and x1 == prev_idx:
                #     indices.append(x0)
                # elif prev_idx % 2 == 0 and x0 == prev_idx:
                #     indices.append(x1)
                # elif prev_idx % 2 == 1 and x1 == prev_idx:
                #     indices.append(x0)
                # else:
                #     indices.append(x1)
                indices.append((x0,x1))
                prev_idx = x0//2
            query_indices.append(indices)
            query_paths.append(cur_path)

        if self.debug > 0:
            print(f"P> queries={self.num_queries}, query_indices={query_indices}")
 
        if self.debug > 1:
            print(f"check query_paths")
            for i, (cur_path, idx) in enumerate(zip(query_paths, query_indices)):
                for j in range(len(indices)):
                    x0, x1 = idx[j]
                    c0, c1 = cur_path[j]
                    assert c0 == codes[j][x0] and c1 == codes[j][x1], \
                        f"P> query-{i} failed at index {j}, x0={x0}, x1={x1}, c0={c0}, c1={c1}"
                # print(f"P>> check query-{i} passed")
            print(f"P> check query_paths passed")

        # Construct merkle paths
        merkle_paths = []
        for i in range(len(query_indices)):
            cur_query_paths = []
            indices = query_indices[i]
            for j in range(len(indices)):
                x0, x1 = indices[j]
                p0 = trees[j].get_authentication_path(x0)
                p1 = trees[j].get_authentication_path(x1)
                cur_query_paths.append((p0, p1))
            merkle_paths.append(cur_query_paths)

        if self.debug > 1:
            print(f"P> check merkle_paths")
            print(f"P> roots={[t.root for t in trees]}")

            for i in range(len(query_paths)):
                cur_query = query_paths[i]
                indices = query_indices[i]
                merkle_path = merkle_paths[i]
                for j in range(len(indices)):
                    # print(f"P> i={i}, j={j}, idx={indices[j]}, cur_query={cur_query[j]}, merkle_path={merkle_path[j]}")
                    x0, x1 = indices[j]
                    c0, c1 = cur_query[j]
                    p0, p1 = merkle_path[j]
                    checked0 = verify_decommitment(x0, c0, p0, trees[j].root)
                    assert checked0, f"merkle_path-{i} failed at index {j}, x0={x0} p0={p0}, c0={c0}"
                    checked1 = verify_decommitment(x1, c1, p1, trees[j].root)
                    assert checked1, f"merkle_path-{i} failed at index {j}, x1={x1}, p1={p1}, c1={c1}"
                    # print(f"P> checked0={checked0}, checked1={checked1}")
                print(f"P>> check merkle_path-{i} passed")
            print(f"P> check merkle_paths passed")

        return v, {
            "sumcheck_h_vec": sumcheck_h_vec,
            "code_commitments": code_commitments,
            "final_constant": constant,
            "query_paths": query_paths,
            "merkle_paths": merkle_paths
        }

    def verify_eval(self, 
                    f_cm: Commitment, 
                    us: list[Field], 
                    v: Field,
                    arg: dict,
                    tr: MerlinTranscript) -> bool:
        """
        Verify the evaluation of a polynomial at a given point.

            arg: `f(us) = v`, 
            
                where f is an MLE polynomial, us is a log-n sized evaluation point.

        Args:
            f_cm: the commitment to the polynomial
            us: the evaluation point
            v: the evaluation value
            arg: the argument generated by the prover
            tr: the proof transcript

        Returns:
            bool: True if the argument is valid, False otherwise
        """
        k = len(us)

        # Load the argument
        sumcheck_h_vec = arg['sumcheck_h_vec']
        code_commitments = arg['code_commitments']
        final_constant = arg['final_constant']
        query_paths = arg['query_paths']
        merkle_paths = arg['merkle_paths']
        f0_code_len = 2**k * self.blowup_factor

        # > Preparation

        eq = MLEPolynomial.eqs_over_hypercube(us)
        eq_mle = MLEPolynomial(eq, k)

        tr.absorb(b"f_code_merkle_root", f_cm.cm)
        tr.absorb(b"point", us)
        tr.absorb(b"value", v)

        # > Commit-phase 
        # 
        sum_checked = v
        alpha_vec = []
        for i in range(k):
            h = sumcheck_h_vec[i]
            h_eval_at_0 = h[0]
            h_eval_at_1 = h[1]
            h_eval_at_2 = h[2]

            tr.absorb(b"h(X)", h)

            assert h_eval_at_0 + h_eval_at_1 == sum_checked, \
                f"h_eval_at_0 + h_eval_at_1 = {h_eval_at_0 + h_eval_at_1}, sum_checked = {sum_checked}"
            
            alpha = tr.squeeze(Field, b"alpha", 4)
            if self.debug > 0:
                print(f"V> alpha[{i}] = {alpha}")
            alpha_vec.append(alpha)

            sum_checked = UniPolynomial.evaluate_from_evals(h, alpha, [Field(0), Field(1), Field(2)])
            
            if i < k-1:
                tr.absorb(b"f_code_merkle_root", code_commitments[i])
        
        tr.absorb(b"f_code_merkle_root", final_constant)

        # f_code_folded = [final_constant] * self.blowup_factor

        assert sum_checked == final_constant * eq_mle.evaluate(alpha_vec), \
                    f"sum_checked = {sum_checked}, final_constant = {final_constant}, eq_mle_at_alpha = {eq_mle.evaluate(alpha_vec)}"
        
        # Reconstruct queries
        queries = []
        for i in range(self.max_queries_try):
            new_query = tr.squeeze(int, b"query", 24) % (f0_code_len//2)
            if new_query*2 in queries:
                continue
            queries.append(new_query*2)
            if len(queries) >= self.num_queries:
                break
        if self.debug > 0:
            print(f"V> len(codes)={len(code_commitments)}, queries={self.num_queries}")

        # Reconstruct query_indices
        query_indices = []
        for q in queries:
            indices = []
            prev_idx = q
            for i in range(k):
                x0, x1 = int(prev_idx//2*2), int(prev_idx//2*2+1)
                # print(f"V> q={q}, prev_idx={prev_idx}, x0={x0}, x1={x1}")
                indices.append((x0,x1))
                prev_idx = x0//2
            query_indices.append(indices)

        if self.debug > 0:
            print(f"V> queries={self.num_queries}, query_indices={query_indices}")

        # Verify the merkle paths
        roots = [f_cm.cm] + code_commitments
        for i, (indices, cur_query, merkle_path) in enumerate(zip(query_indices, query_paths, merkle_paths)):
            for j in range(len(indices)):
                x0, x1 = indices[j]
                c0, c1 = cur_query[j]
                p0, p1 = merkle_path[j]
                checked0 = verify_decommitment(x0, c0, p0, roots[j])
                checked1 = verify_decommitment(x1, c1, p1, roots[j])
                assert checked0 and checked1, f"merkle_path-{i} failed at index {j}, x0={x0}, x1={x1}, p0={p0}, p1={p1}"
            print(f"V> check merkle_path-{i} passed")

        twiddles = UniPolynomialWithFft.precompute_twiddles_for_fft(f0_code_len, is_bit_reversed=True)
        for i, (indices, cur_query) in enumerate(zip(query_indices, query_paths)):
            coset = self.coset_gen
            for j, idx in enumerate(indices):
                x0, x1 = idx
                c0, c1 = cur_query[j]
                next_index = x0//2
                folded_value = (Field(1)-alpha_vec[j]) * (c0 + c1) / 2 + alpha_vec[j] * (c0 - c1) / (2 * coset * twiddles[next_index]) 
                next_pair= cur_query[j+1] if j<len(indices)-1 else (final_constant, final_constant)
                # print(f"V> idx={idx}, cur={cur_query[j]}, next_pair={next_pair}")
                if (next_index) % 2 == 0:
                    next = next_pair[0]
                else:
                    next = next_pair[1]
                assert next == folded_value, f"folded = {folded_value}, next = {next}"
                coset *= coset
            print(f"V> check folding-{i} passed")
        return True
    
def test_pcs():

    pcs = BASEFOLD_RS_PCS(MerkleTree, debug = 2)

    tr = MerlinTranscript(b"basefold-rs-pcs")

    # A simple instance f(x) = y
    log_n = 10
    evals = [Field.random() for _ in range(1 << log_n)]
    us = [Field.random() for _ in range(log_n)]
    MLEPolynomial.set_field_type(Field)
    eqs = MLEPolynomial.eqs_over_hypercube(us)
    
    y = inner_product(evals, eqs, Field.zero())
    f_mle = MLEPolynomial(evals, log_n)
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