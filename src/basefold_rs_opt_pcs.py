#!/usr/bin/env python3

# WARNING: This implementation may contain bugs and has not undergone auditing. 
# It is intended for educational and research purposes only. 
# DO NOT use it in a production environment.

from utils import log_2, next_power_of_two, query_num, delta_johnson_bound

# Implementation of Basefold (RS encoding) with simplified sumcheck, which is 
#   inspired by DeepFold [GLH+25].
#
# [GLH+25] Yanpei Guo, Xuanming Liu, Kexi Huang and others. DeepFold: Efficient 
#    Multilinear Polynomial Commitment from Reed-Solomon Code and Its. 2025.
#    Application to Zero-knowledge Proofs
# [ZCF23] Hadas Zeilberger, Binyi Chen and Ben Fisch. BaseFold: Efficient 
#    Field-Agnostic Polynomial Commitment Schemes from Foldable Codes. 2024.
#

from curve import Fr as BN254_Fr
from merlin.merlin_transcript import MerlinTranscript
from mle2 import MLEPolynomial
from unipoly2 import UniPolynomial, UniPolynomialWithFft, bit_reverse_permutation
from merkle import MerkleTree, verify_decommitment

# TODO:
#
#  - [ ] Make security parameters configurable
#  - [ ] Reduce leaves revealed by the prover and also the corresponding checks
#  - [ ] Compress the merkle proofs
#  - [ ] Add batching proving/verifying

Field = BN254_Fr

class Commitment:

    def __init__(self, tree: MerkleTree):
        self.tree = tree
        self.cm = tree.root

    def __repr__(self):
        return f"Commitment(len={len(self.tree.data)}, root={self.cm})"

def rs_encode(f: list[Field], coset: Field, blowup_factor: int) -> list[Field]:
    n = next_power_of_two(len(f))
    N = n * blowup_factor

    omega_Nth = Field.nth_root_of_unity(N)
    k = log_2(N)
    vec = f + [Field.zero()] * (N - len(f))
    return UniPolynomialWithFft.fft_coset_rbo(vec, coset, k, omega=omega_Nth)

def fold(f: list[Field], r: Field) -> list[Field]:
    """
    Fold (even-with-odd) a list with a given factor.

        f = [f_0, f_1, f_2, f_3, f_4, f_5, f_6, f_7]
        f_fold = [
            (1-r) * f_0 + r * f_1, 
            (1-r) * f_2 + r * f_3, 
            (1-r) * f_4 + r * f_5, 
            (1-r) * f_6 + r * f_7,
            ]
    """
    n = len(f)
    assert n % 2 == 0, f"n = {n}, n must be even"
    half = n >> 1
    f_even = f[::2]
    f_odd = f[1::2]
    return [f_even[i] + r * (f_odd[i] - f_even[i]) for i in range(half)]


# NOTE: The secret recipe of simplified sumcheck is to use a cached partial 
#       evaluation of the MLE polynomial. The cached array follows the folding 
#       pattern of the MLE polynomial, and can be used to help compute the next 
#       sum to be checked.
#
#       This idea is inspired by DeepFold [GLH+25].
#
#       The following function is the implementation of the partial evaluation.
def expanded_partial_evaluate(f: list[Field], us: list[Field]) -> list[Field]:
    """
    Evaluate an mle polynomial *partially* backwards, 
        i.e. from x_{k-1}, x_{k-2}, ..., x_{0}.

        MLE polynomial: f(x_0, x_1, ..., x_{k-1}) 
          =  f_0 * eq_0(x_0,...,x_{k-1}) 
           + f_1 * eq_1(x_0,...,x_{k-1}) 
           + ...
           + f_{k-1} * eq_{k-1}(x_0,...,x_{k-1})

    Args:
        f  = [f_0, f_1, f_2, f_3, f_4, f_5, f_6, f_7]
        us = [r0, r1, r2]
    Returns:
        rs = [
            (1-r2) * f_0 + r2 * f_4, 
            (1-r2) * f_1 + r2 * f_5, 
            (1-r2) * f_2 + r2 * f_6, 
            (1-r2) * f_3 + r2 * f_7,

            (1-r1) * [(1-r2) * f_0 + r2 * f_4] + r1 * [(1-r2) * f_2 + r2 * f_6]
            (1-r1) * [(1-r2) * f_1 + r2 * f_5] + r1 * [(1-r2) * f_3 + r2 * f_7]

            f(r0,r1,r2)
        ]
    """
    k, n = len(us), len(f)
    assert n == 2**k, f"n = {n}, k = {k}"

    rs, e = [], f.copy()
    half = n >> 1
    for i in range(k):
        e_low, e_high = e[:half], e[half:]
        e = [e_low[j] + us[k-i-1] * (e_high[j] - e_low[j]) for j in range(half)]
        rs += e
        half >>= 1
    return rs


class BASEFOLD_RS_PCS:

    blowup_factor = 8       # WARNING: this is not secure
    security_bits = 128     # WARNING: this is not secure
    coset_gen = Field.multiplicative_generator()
    max_queries_try = 1000  # NOTE: change it to a practical number
    random_challenge_bits = 16

    @property
    def num_queries(self):
        return query_num(self.blowup_factor, self.security_bits, delta_johnson_bound)

    def __init__(self, oracle, debug: int = 0):
        """
        Args:
            oracle: the oracle to use for the proof
        """
        self.oracle = oracle
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

    def query_phase(self, 
                    queries: list[int],
                    codes: list[list[Field]], 
                    trees: list[MerkleTree], 
                    ) -> tuple[list[int],                       # query_indices  
                              list[list[tuple[Field, Field]]],  # query_paths
                              list[list[tuple[Field, Field]]]   # merkle_paths
                              ]:
        """
        Generate queries and anwers for the query phase.
        """
        N = len(codes[0])

        # Construct query paths
        query_indices = []
        query_paths = []
        for q in queries:
            cur_path = []
            indices = []
            prev_idx = q
            for c in codes:
                x0, x1 = int(prev_idx//2*2), int(prev_idx//2*2+1)
                cur_path.append((c[x0], c[x1]))
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
                    x0, x1 = indices[j]
                    c0, c1 = cur_query[j]
                    p0, p1 = merkle_path[j]
                    checked0 = verify_decommitment(x0, c0, p0, trees[j].root)
                    assert checked0, f"merkle_path-{i} failed at index {j}, x0={x0} p0={p0}, c0={c0}"
                    checked1 = verify_decommitment(x1, c1, p1, trees[j].root)
                    assert checked1, f"merkle_path-{i} failed at index {j}, x1={x1}, p1={p1}, c1={c1}"
                # print(f"P>> check merkle_path-{i} passed")
            print(f"P> check merkle_paths passed")
        
        return query_indices, query_paths, merkle_paths


    def verify_queries(self, 
                       N:int, 
                       r_vec: list[Field], 
                       codes_cm: list[Commitment], 
                       final_constant: Field, 
                       queries: list[int],
                       query_paths: list[list[tuple[Field, Field]]],
                       merkle_paths: list[list[tuple[Field, Field]]]
                       ):
        """
        Verify the query phase.
        """
        k = len(r_vec)
        assert N == 2**k * self.blowup_factor, \
            f"N = {N}, k = {k}, blowup_factor = {self.blowup_factor}"
        assert self.num_queries == len(query_paths) == len(merkle_paths), \
            f"len(r_vec)={len(r_vec)}, len(query_paths)={len(query_paths)}, len(merkle_paths)={len(merkle_paths)}"
        assert k == len(codes_cm), \
            f"len(r_vec)={len(r_vec)}, len(codes)={len(codes_cm)}"
        
        # Reconstruct query_indices
        query_indices = []
        for q in queries:
            indices = []
            prev_idx = q
            for i in range(k):
                x0, x1 = int(prev_idx//2*2), int(prev_idx//2*2+1)
                indices.append((x0,x1))
                prev_idx = x0//2
            query_indices.append(indices)

        if self.debug > 0:
            print(f"V> queries={self.num_queries}, query_indices={query_indices}")

        # Verify the merkle paths
        for i, (indices, cur_query, merkle_path) in enumerate(zip(query_indices, query_paths, merkle_paths)):
            for j in range(len(indices)):
                x0, x1 = indices[j]
                c0, c1 = cur_query[j]
                p0, p1 = merkle_path[j]
                checked0 = verify_decommitment(x0, c0, p0, codes_cm[j])
                checked1 = verify_decommitment(x1, c1, p1, codes_cm[j])
                assert checked0 and checked1, f"merkle_path-{i} failed at index {j}, x0={x0}, x1={x1}, p0={p0}, p1={p1}"
        if self.debug > 0: print(f"V> check merkle paths passed")

        # Verify the folding
        twiddles = UniPolynomialWithFft.precompute_twiddles_for_fft(N, is_bit_reversed=True)
        for i, (indices, cur_query) in enumerate(zip(query_indices, query_paths)):
            coset = self.coset_gen
            for j, idx in enumerate(indices):
                x0, x1 = idx
                c0, c1 = cur_query[j]
                next_index = x0//2
                folded_value = (Field(1)-r_vec[j]) * (c0 + c1) / 2 + r_vec[j] * (c0 - c1) / (2 * coset * twiddles[next_index]) 
                next_pair= cur_query[j+1] if j<len(indices)-1 else (final_constant, final_constant)
                if (next_index) % 2 == 0:
                    next = next_pair[0]
                else:
                    next = next_pair[1]
                assert next == folded_value, f"folded = {folded_value}, next = {next}"
                coset *= coset
        if self.debug > 0: print(f"V> check folding passed")
        return True
    
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
        assert self.num_queries <= 1 << (f_mle.num_var + log_2(self.blowup_factor)), f"self.num_queries={self.num_queries}, f_mle.num_var={f_mle.num_var}, blowup_factor={self.blowup_factor}"

        k = f_mle.num_var
        
        # Evaluate f_mle at the point us
        v = f_mle.evaluate(us)
        f = f_mle.evals.copy()
        n = 2**k

        if self.debug > 0:
            print(f"P> f_len={len(f)}, k={k}, c_len ={len(f)*self.blowup_factor}")

        # NOTE: The array `eq` is not needed for the simplified sumcheck.
        ## eq = MLEPolynomial.eqs_over_hypercube(us)

        # > Preparation

        f_code_len = len(f) * self.blowup_factor

        # Precompute twiddles for FFT
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
        r_vec = []
        sumcheck_h_vec = []
        code_commitments = []
        trees = [MerkleTree(f_code)]
        codes = [f_code]

        # NOTE: The cached partial evaluations will be used to compute h(u) and h(u+1).
        #  The value at the tail is exactly the evaluation, i.e. h(u0,u1,...,u_{k-1}).
        h_partial = expanded_partial_evaluate(f, us)
        
        for i in range(k):
            if self.debug > 0:
                print(f"P> Round {i}")

            # construct h(X) = f(r0, r1, ..., r_{i-1}, X, u_{i+1}, ..., u_{k-1})
            if i < k - 1:
                # If i in [0, 1, ..., k-2], h(0) and h(1) are at the tail of the cached array. 
                h_at_0 = h_partial[-3]
                h_at_1 = h_partial[-2]
                h_at_u = h_partial[-1]
                h_at_u_plus_1 = h_at_u + (h_at_1 - h_at_0)
            else:
                # If i is k-1, the cached array has been folded into only one element. But
                # we can still get h(0) and h(1) from the folded f.
                h_at_0 = f[0]
                h_at_1 = f[1]
                h_at_u = h_partial[-1]
                h_at_u_plus_1 = h_at_u + (h_at_1 - h_at_0)
            
            if self.debug > 1:
                print(f"P> check h(0), h(1), h(u), h(u+1)")
                print(f"P> h_partial = {h_partial}")
                print(f"P> h_at_0 = {h_at_0}")
                print(f"P> h_at_1 = {h_at_1}")
                print(f"P> h_at_u = {h_at_u}")
                partial_f_mle = MLEPolynomial(f, k-i)
                assert h_at_0 == partial_f_mle.evaluate([Field(0)]+us[i+1:]), \
                    f"h_at_0 = {h_at_0}, partial_f_mle.evaluate(0, us) = {partial_f_mle.evaluate([Field(0)]+us[i+1:])}"
                assert h_at_1 == partial_f_mle.evaluate([Field(1)]+us[i+1:]), \
                    f"h_at_1 = {h_at_1}, partial_f_mle.evaluate(1, us) = {partial_f_mle.evaluate([Field(1)]+us[i+1:])}"
                assert h_at_u == partial_f_mle.evaluate(us[i:]), \
                    f"h_at_u = {h_at_u}, partial_f_mle.evaluate(us) = {partial_f_mle.evaluate(us[i:])}"
                assert h_at_u_plus_1 == partial_f_mle.evaluate([us[i]+Field(1)]+us[i+1:]), \
                    f"h_plus_1_at_u = {h_at_u_plus_1}, partial_f_mle.evaluate([us[i]+Field(1)]+us[i+1:]) = {partial_f_mle.evaluate([us[i]+Field(1)]+us[i+1:])}"
                assert h_at_u == sum_checked, \
                    f"h_at_u = {h_at_u}, sum_checked = {sum_checked}"
                print(f"P> check h(0), h(1), h(u), h(u+1) passed, {h_at_u} = {sum_checked}")

            if self.debug > 0: print(f"P> h_at_u_plus_1 = {h_at_u_plus_1}")

            sumcheck_h_vec.append(h_at_u_plus_1)

            tr.absorb(b"h(X)", h_at_u_plus_1)

            # Receive a random number from the verifier
            r = tr.squeeze(Field, b"r", self.random_challenge_bits)
            if self.debug > 0:
                print(f"P> r[{i}] = {r}")
            r_vec.append(r)

            # NOTE: The verifier is supposed to compute f_i(r), which is *equal to* f_{i+1}(u_i). 
            #   And then in the next round, the prover will only need to send f_{i+1}(u_i+1) to the verifier.
            #   The computation of f_{i+1}(r) at the verifier's side costs only one multiplication.
            h_at_r = h_at_u + (h_at_u_plus_1 - h_at_u) * (r - us[i])

            if self.debug > 0:
                print(f"P> h_at_r[{i}] = {h_at_r}")

            if self.debug > 1:
                print(f"P> check new sumcheck passed")
                assert h_at_r == MLEPolynomial(f, k-i).evaluate([r]+us[i+1:]), \
                    f"h_eval_at_r = {h_at_r}, f(r) = {MLEPolynomial(f, k-i).evaluate([r]+us[i+1:])}"
                new_sum = UniPolynomial.evaluate_from_evals([h_at_u, h_at_u_plus_1], r, [us[i], us[i]+Field(1)])
                assert h_at_r == new_sum
                print(f"P> check new sumcheck passed, {h_at_r} = {new_sum}")
            
            # update sumcheck for the next round
            new_sum_checked = h_at_r

            # fold f

            f = fold(f, r)
            h_partial_folded = fold(h_partial[:-1], r)

            # fold f_code
            # TODO: optimized the field inversion (coset, twiddles[])
            f_code_folded = [(Field(1)-r) * (f_code[2*i] + f_code[2*i+1]) / 2 
                      + r * (f_code[2*i] - f_code[2*i+1]) / (2 * coset * twiddles[i]) 
                      for i in range(len(f_code)//2)]
            
            if i == k-1:
                constant = f_code_folded[0]
                
                assert all([f_code_folded[i] == constant for i in range(len(f_code_folded))]), \
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
            h_partial = h_partial_folded
            half >>= 1
            coset *= coset
            sum_checked = new_sum_checked

        ## End of the big loop for `i`

        assert sum_checked == constant, \
            f"sum_checked = {sum_checked}, constant = {constant}"
        if self.debug > 0:
            print(f"P> check final_sum = f(r_vec) passed, {sum_checked} = {constant}")

        # > Query-phase

        # Construct queries

        queries = []
        for i in range(self.max_queries_try):
            new_query = tr.squeeze(int, b"query", 24) % (f_code_len//2)
            if new_query*2 in queries:
                continue
            queries.append(new_query*2)
            if len(queries) >= self.num_queries:
                break
        if len(queries) < self.num_queries:
            raise ValueError(f"Failed to generate {self.num_queries} queries")
        
        query_indices, query_paths, merkle_paths = self.query_phase(queries, codes, trees)

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

        # eq = MLEPolynomial.eqs_over_hypercube(us)
        # eq_mle = MLEPolynomial(eq, k)

        tr.absorb(b"f_code_merkle_root", f_cm.cm)
        tr.absorb(b"point", us)
        tr.absorb(b"value", v)

        # > Commit-phase 
        # 
        sum_checked = v
        r_vec = []
        for i in range(k):
            h_at_u_plus_1 = sumcheck_h_vec[i]
            h_at_u = sum_checked

            tr.absorb(b"h(X)", h_at_u_plus_1)

            r = tr.squeeze(Field, b"r", self.random_challenge_bits)
            if self.debug > 0:
                print(f"V> r[{i}] = {r}")
            r_vec.append(r)

            h_at_r = h_at_u + (h_at_u_plus_1 - h_at_u) * (r - us[i])

            if self.debug > 0:
                print(f"V> h_at_r[{i}] = {h_at_r}")
            
            sum_checked = h_at_r

            if i < k-1:
                tr.absorb(b"f_code_merkle_root", code_commitments[i])
        
        tr.absorb(b"f_code_merkle_root", final_constant)

        # f_code_folded = [final_constant] * self.blowup_factor

        assert sum_checked == final_constant, \
                    f"sum_checked = {sum_checked}, final_constant = {final_constant}"
        if self.debug > 0:
            print(f"V> check final_sum = f(r_vec) passed, {sum_checked} = {final_constant}")

        # > Query-phase

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
            print(f"V> len(code)={f0_code_len}, queries={self.num_queries}")

        self.verify_queries(f0_code_len, r_vec, [f_cm.cm]+code_commitments, final_constant, 
            queries, query_paths, merkle_paths)

        return True
