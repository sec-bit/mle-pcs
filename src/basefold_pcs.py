#!/usr/bin/env python3

# WARNING: This implementation may contain bugs and has not undergone auditing. 
# It is intended for educational and research purposes only.
# DO NOT use it in a production environment.

from utils import is_power_of_two, log_2, query_num, delta_uni_decoding, delta_johnson_bound
from random import randint
from mle2 import MLEPolynomial
from unipoly2 import UniPolynomial, UniPolynomialWithFft    
from merkle import MerkleTree, verify_decommitment
from merlin.merlin_transcript import MerlinTranscript


# Implementation of Basefold PCS(with foldable code scheme)[ZCF23]
#
# [ZCF23] BaseFold: Efficient Field-Agnostic Polynomial Commitment 
#           Schemes from Foldable Codes
#  Author: Hadas Zeilberger, Binyi Chen and Ben Fisch
#  URL: https://eprint.iacr.org/2023/1705

from basefold_rs_pcs import Commitment

# DEBUG: please use this tiny finite field (F193) for debugging
# from ff.tiny import Fp

from curve import Fr as Fp

MLEPolynomial.set_field_type(Fp)
UniPolynomial.set_field_type(Fp)
UniPolynomialWithFft.set_field_type(Fp)

class FoldableCoder:

    @staticmethod
    def setup_tables(k0, c, depth):
        """
        Setup the parameters for the basefold encoding.

        Args:
            k0 (int): The size of each chunk in the message.
            c (int): Blowup factor.
            depth (int): The depth of the randomized table.

        Returns:
            list: The randomized table.
        """
        tables = [[Fp.random()]]
        tables += [[Fp.random() for _ in range(1 << (i - 1))] for i in range(1, depth + log_2(k0 * c) + 1)]
        for i in range(1, depth + log_2(k0 * c) + 1):
            tables[i] += [-e for e in tables[i]]
        return tables
    
    @staticmethod
    def rep_encode(m, k0, c):
        """
        Perform repetition encoding on the input message.

        Args:
            m (list): The input message to be encoded.
            k0 (int): The size of each chunk in the message.
            c (int): The number of times each chunk should be repeated.

        Returns:
            list: The repetition-encoded message.

        Raises:
            AssertionError: If k0 or c is not positive, or if the length of m is not a multiple of k0.
        """
        assert k0 > 0 and c > 0, f"k0 <= 0 or c <= 0, k0: {k0}, c: {c}"
        assert len(m) == k0, "len(m): %d is not equal to k0: %d" % (len(m), k0)
        code = []
        for i in range(0, c*len(m), k0):
            for j in range(0, c):
                code += m[i:i+k0]
        return code

    def __init__(self, k0: int, c: int, depth: int, G0=None):
        """
        Setup the parameters for the basefold encoding.
           (T0, T1, ..., T_{depth-1})

           Ti: Fp^{k0 * c * 2^i}
        """
        self.tables = self.setup_tables(k0, c, depth)

        self.k0 = k0
        self.depth = depth
        self.blowup_factor = c

        if G0 is None:
            self.generator_func = self.rep_encode
        else:
            self.generator_func = G0

    def encode(self, m: list[Fp], debug=False) -> list[Fp]:
        """
        Perform basefold encoding on the input message.

        This function encodes the input message `m` using the basefold encoding scheme with
        specified parameters. It divides `m` into chunks, applies an encoding function `G0`
        (default is repetition encoding), and iteratively combines chunks using transformation
        tables `T` over a given depth.

        Returns:
            list: The basefold encoded code as a list.
        """
        assert len(m) % self.k0 == 0, f"len(m): {len(m)} is not a multiple of k0: {self.k0}"
        blowup_factor = self.blowup_factor
        k0 = self.k0
        n0 = k0 * blowup_factor
        kd = len(m)
        depth = log_2(kd // k0)
        assert self.depth >= depth, f"self.depth: {self.depth} >= depth: {depth}"

        if debug: print(f">>> basefold_encode: m={m}, k0={k0}, d={depth}, blowup_factor={blowup_factor}")

        kd = k0 * 2 ** depth
        assert len(m) == kd, f"len(m): {len(m)} != kd: {kd}, depth={depth}"
        
        chunk_size = k0
        chunk_num = 2 ** depth
        G0 = self.generator_func
        T = self.tables
        assert len(T) >= depth, f"len(T): {len(T)} < depth: {depth}"

        code = []
        for i in range(chunk_num):
            chunk = m[i*chunk_size: (i+1)*chunk_size]
            chunk_code = G0(chunk, chunk_size, blowup_factor)
            code += chunk_code
        if debug: print(">>> basefold_encode: code=", code)

        if depth == 0:
            return code

        chunk_size = k0 * blowup_factor
        if debug: print(">>> basefold_encode: chunk_size=", chunk_size)
        if debug: print(">>> basefold_encode: chunk_num=", chunk_num)

        for i in range(0, depth):
            table = T[log_2(chunk_size) + 1]
            assert len(table) == chunk_size * 2, f"table[{i}] != chunk_size * 2, len(table)={len(table)}, chunk_size={chunk_size}"
            if debug: print(f">>> basefold_encode: table={table}")
            for c in range(0, chunk_num, 2):
                left  = code[    c*chunk_size : (c+1)*chunk_size]
                right = code[(c+1)*chunk_size : (c+2)*chunk_size]
                if debug: print(f">>> basefold_encode: left={left}, right={right}")

                for j in range(0, chunk_size):
                    if debug: print(f">>> basefold_encode: i={i}, c={c}, j={j}")
                    rhs = right[j] * table[j]
                    lhs = left[j]
                    code[(c)*chunk_size + j] = lhs + rhs
                    code[(c+1)*chunk_size + j] = lhs - rhs
            chunk_size = chunk_size * 2
            chunk_num = chunk_num // 2
        return code

class FoldableRSCoder(FoldableCoder):
    def __init__(self, k0, c, depth):
        assert is_power_of_two(c), "c must be a power of two"
        assert is_power_of_two(k0), "k0 must be a power of two"
        self.k0 = k0
        self.depth = depth
        self.blowup_factor = c
        self.tables = self.setup_rs_tables(k0, c, depth)
        self.generator_func = self.rs_encode

    @staticmethod
    def rs_encode(m: list[Fp], k0: int, c: int) -> list[Fp]:
        """
        (Deprecated)
        """
        assert is_power_of_two(k0 * c), "len(m) is not a power of two"
        assert len(m) <= k0, "len(m) is greater than k0"
        if len(m) < k0:
            m = m + [Fp.zero()] * (k0 - len(m))
        omega = Fp.nth_root_of_unity(k0 * c)
        code = [None] * (k0 * c)
        for i in range(k0 * c): 
            # comput f_m(alpha[i])
            code[i] = sum(m[j] * (omega**(i*j)) for j in range(k0))
        return code

    @staticmethod
    def rs_encode_k0_1(m: list[Fp], k0:int, c: int) -> list[Fp]:
        assert k0 == 1, "k0 must be 1"
        assert len(m) == 1, "len(m) must be 1"
        return [m[0]] * c
    
    @staticmethod
    def setup_rs_tables(k0, c, depth):
        """
            T = 
        """
        T = [[Fp.one()]]
        for i in range(1, depth + log_2(k0 * c) + 1):
            base = Fp.one()
            omega = Fp.nth_root_of_unity(1 << i)
            level = []
            for j in range(1 << i):
                level.append(base)
                base *= omega
            T.append(level)
        return T

class BASEFOLD_PCS:

    # TODO: make this configurable
    num_queries = 3
    security_bits = 100

    def __init__(self, encoder: FoldableCoder, debug: int = 0):
        """
        Args:
            encoder: the encoder to use for the proof
        """
        self.debug = debug
        self.encoder = encoder
        use_rscode = isinstance(encoder, FoldableRSCoder)
        delta_func = delta_johnson_bound if use_rscode else delta_uni_decoding
        self.num_queries = query_num(encoder.blowup_factor, self.security_bits, delta_func)

    # def encode(self, m: list[Fp], k0: int, depth: int, c: int, T: list[list[Fp]], G0=rep_encode, debug=False):
    #     pass

    def fold_with_multilinear_basis(self, vs: list[Fp], r: Fp):
        n = len(vs)
        assert is_power_of_two(n), "len(vs) is not a power of two"
        enc = self.encoder
        table = enc.tables[log_2(n)]
        assert len(table) == len(vs), f"len(table) is not double len(vs), len(table) = {len(table)}, len(vs) = {len(vs)}"
        half = n // 2
        left = vs[:half]
        right = vs[half:]
        new_vs = [(Fp(1)-r) * (left[i] + right[i])/2 + (r) * (left[i] - right[i])/(2*table[i]) for i in range(half)]
        return new_vs

    def fold_with_monomial_basis(self, vs: list[Fp], r: Fp):
        n = len(vs)
        assert is_power_of_two(n), "len(vs) is not a power of two"

        table = self.encoder.tables[log_2(n)]

        assert len(table) == len(vs), f"len(table) is not double len(vs), len(table) = {len(table)}, len(vs) = {len(vs)}"
        half = n // 2
        left = vs[:half]
        right = vs[half:]
        new_vs = [(left[i] + right[i])/2 + r * (left[i] - right[i])/(2*table[i]) for i in range(half)]
        return new_vs

    def commit(self, f_mle: MLEPolynomial) -> Commitment:
        """
        Commit to the evaluations of the MLE polynomial.
        """
        evals = f_mle.evals
        d = f_mle.num_var
        assert d > 0, "d must be greater than 0"
        assert len(evals) % self.encoder.k0 == 0, "len(evals) is not a multiple of k0"
        kd = len(evals)

        f_code = self.encoder.encode(evals)
        f_tree = MerkleTree(f_code)

        assert len(f_code) == kd * self.encoder.blowup_factor, \
            f"len(evals)={kd}, d={d}, blowup_factor={self.encoder.blowup_factor}"
        cm = Commitment(f_tree)
        return cm
    
    def prove_eval(self, 
                    f_cm: Commitment,
                    f_mle: MLEPolynomial, 
                    us: list[Fp], 
                    tr: MerlinTranscript):
        """
        Args:
            f_cm: the commitment to the MLE polynomial
            f_mle: the MLE polynomial
            us: the evaluation points
            tr: the Merlin transcript
        """
        k = f_mle.num_var
        assert  k <= len(us), f"k > len(us), k = {k}, len(us) = {len(us)}"
        n = len(f_mle.evals)
        half = n >> 1
        f = f_mle.evals[:]
        v = f_mle.evaluate(us)
        eq = MLEPolynomial.eqs_over_hypercube(us)
        
        f0_code = self.encoder.encode(f)
        f0_code_tree = MerkleTree(f0_code)
        # Update transcript with the context
        tr.absorb(b"f_code_merkle_root", f_cm.cm)
        tr.absorb(b"point", us)
        tr.absorb(b"value", v)

        # Sumcheck & FRI loop
        challenge_vec = []
        sumcheck_sum = v
        h_poly_vec = []
        f_code_vec = [f0_code]
        f_code_trees = [f0_code_tree]
        f_code_cm_vec = []
        f_code = f0_code
        for i in range(k):
            if self.debug > 0: 
                print("P> sumcheck round {}".format(i))

            f_low = f[:half]
            f_high = f[half:]
            eq_low = eq[:half]
            eq_high = eq[half:]
            
            h_eval_at_0 = sum([f_low[j] * eq_low[j] for j in range(half)])
            h_eval_at_1 = sum([f_high[j] * eq_high[j] for j in range(half)])
            h_eval_at_2 = sum([ (2 * f_high[j] - f_low[j]) * (2 * eq_high[j] - eq_low[j]) for j in range(half)])
            h = [h_eval_at_0, h_eval_at_1, h_eval_at_2]
            h_poly_vec.append(h)
            
            if self.debug > 0: 
                print(f"P> sumcheck: h=[{h_eval_at_0},{h_eval_at_1},{h_eval_at_2}]")
            
            tr.absorb(b"h(X)", h)

            assert h_eval_at_0 + h_eval_at_1 == sumcheck_sum, f"{h_eval_at_0} + {h_eval_at_1} != {sumcheck_sum}"

            if self.debug > 1: 
                print(f"P> sumcheck: {h_eval_at_0 + h_eval_at_1} == {sumcheck_sum}")

            # Receive a random number from the verifier
            r = tr.squeeze(Fp, b"alpha", 4)
            if self.debug > 0: 
                print(f"P> r[{i}] = {r}")

            challenge_vec.append(r)

            # fold(low, high, alpha)
            f = [(1 - r) * f_low[i] + r * f_high[i] for i in range(half)]
            eq = [(1 - r) * eq_low[i] + r * eq_high[i] for i in range(half)]
            if self.debug > 1: print(f"P> sumcheck: f_folded = {f}")
            if self.debug > 1: print(f"P> sumcheck: eq_folded = {eq}")

            # compute the new sum = h(alpha)
            sumcheck_sum = UniPolynomial.evaluate_from_evals([h_eval_at_0, h_eval_at_1, h_eval_at_2], r, [Fp(0),Fp(1),Fp(2)])
            if self.debug > 0: print(f"P> sumcheck: sumcheck_sum = {sumcheck_sum}")

            if self.debug > 0: print(f"P> fri round {i}")

            # fold code
            f_code = self.fold_with_multilinear_basis(f_code, r)
            if self.debug > 1: 
                print("P> fri: f_code_folded=", f_code)

            if i == k-1:
                constant = f_code[0]
                assert all([f_code[j] == constant for j in range(len(f_code))]), \
                    "f_code is not a constant code, f_code = {f_code}"
                # f_code_vec.append(f_code)
                tr.absorb(b"f_final_code", constant)
            else:
                f_code_tree = MerkleTree(f_code)
                f_code_trees.append(f_code_tree)
                f_code_vec.append(f_code)
                f_code_cm_vec.append(f_code_tree.root)
                tr.absorb(b"f_code_cm", f_code_tree.root)

            if self.debug > 1:
                # DEBUG: consistency check (invariant)
                print(f"P> check enc(fold(message)) == fold(enc(message))")
                # Enc(fold(message)) = fold(Enc(message)) 
                debug_f_folded_code = self.encoder.encode(f)
                if self.debug > 2: 
                    print(f"P> fri: enc({f})={debug_f_folded_code}")
                assert f_code == debug_f_folded_code, "Enc(fold(message)) != fold(Enc(message))"
                print(f"P> check enc(fold(message)) == fold(enc(message)) passed")
            
            half = half >> 1

        ## End of the big loop for `i in range(k)`

        # DEBUG:
        if self.debug > 1:
            f_eval_at_random = sumcheck_sum/eq[0]
            assert self.encoder.encode([f_eval_at_random]) == f_code, \
                "Encode(f(rs)) != f_code_0"
            print(f"P> fold(f_code) == encode(fold(f_eq)/fold(eq(us)))")

        # > FRI-query phase
        queries = []
        for i in range(self.num_queries):
            new_query = tr.squeeze(int, b"query", 16) % (len(f0_code))
            queries.append(new_query)

        if self.debug > 0:
            print(f"P> queries={queries}")
        query_paths, merkle_paths = self.prove_queries(queries, f_code_vec, f_code_trees)

        # return (h_poly_vec, challenge_vec, f_code_vec)
        return v, {
            'h_poly_vec': h_poly_vec,
            'f_code_cm_vec': f_code_cm_vec,
            'final_constant': constant,
            'query_paths': query_paths,
            'merkle_paths': merkle_paths
        }

    def prove_queries(self, 
                      queries: list[int],
                      f_code_vec: list[list[Fp]], 
                      f_code_trees: list[MerkleTree]):
        """
        Construct the merkle paths for the queried leaves in the trees of codewords

        Args:
            queries: [q0, q1, ..., q_{num_queries-1}]
            f_code_vec: [f0], [f1], ..., [f_{d-1}]
            f_code_trees: [f0_tree], [f1_tree], ..., [f_{d-1}_tree]

        """
        assert len(queries) == self.num_queries, \
            f"len(queries) != self.num_queries, len(queries) = {len(queries)}, self.num_queries = {self.num_queries}"
        assert len(f_code_vec) == len(f_code_trees), \
            f"len(f_code_vec) != len(f_code_trees), len(f_code_vec) = {len(f_code_vec)}, len(f_code_trees) = {len(f_code_trees)}"
        
        # Construct query paths
        query_indices = []
        query_paths = []
        for q in queries:
            # num_vars_copy = num_vars
            cur_path = []
            indices = []
            prev_idx = q
            for codeword in f_code_vec:
                half = len(codeword)//2
                if prev_idx >= half:
                    x0, x1 = prev_idx - half, prev_idx
                else:
                    x0, x1 = prev_idx, prev_idx + half
                cur_path.append((codeword[x0], codeword[x1]))
                indices.append((x0,x1))
                prev_idx = x0
            query_indices.append(indices)
            query_paths.append(cur_path)

        if self.debug > 0:
            print(f"P> query_indices={query_indices}")
 
        if self.debug > 1:
            print(f"P> check query_paths")
            for i, (cur_path, idx) in enumerate(zip(query_paths, query_indices)):
                for j in range(len(indices)):
                    x0, x1 = idx[j]
                    c0, c1 = cur_path[j]
                    assert c0 == f_code_vec[j][x0] and c1 == f_code_vec[j][x1], \
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
                p0 = f_code_trees[j].get_authentication_path(x0)
                p1 = f_code_trees[j].get_authentication_path(x1)
                cur_query_paths.append((p0, p1))
            merkle_paths.append(cur_query_paths)

        if self.debug > 1:
            print(f"P> check merkle_paths")

            for i in range(len(query_paths)):
                cur_query = query_paths[i]
                indices = query_indices[i]
                merkle_path = merkle_paths[i]
                for j in range(len(indices)):
                    x0, x1 = indices[j]
                    c0, c1 = cur_query[j]
                    p0, p1 = merkle_path[j]
                    checked0 = verify_decommitment(x0, c0, p0, f_code_trees[j].root)
                    assert checked0, f"merkle_path-{i} failed at index {j}, x0={x0} p0={p0}, c0={c0}"
                    checked1 = verify_decommitment(x1, c1, p1, f_code_trees[j].root)
                    assert checked1, f"merkle_path-{i} failed at index {j}, x1={x1}, p1={p1}, c1={c1}"
                print(f"P>> check merkle_path-{i} passed")
            print(f"P> check merkle_paths passed")
        return query_paths, merkle_paths
    
    def verify_eval(self, 
                    f_cm: Commitment,
                    us: list[Fp], 
                    v: Fp, 
                    proof: dict, 
                    tr: MerlinTranscript) -> bool: 
        """
        Verify the proof of evaluation
        """

        k = len(us)
        kd = 1 << k
        nd = kd * self.encoder.blowup_factor

        # Update transcript with the context
        tr.absorb(b"f_code_merkle_root", f_cm.cm)
        tr.absorb(b"point", us)
        tr.absorb(b"value", v)
        
        # Load proof
        h_poly_vec = proof['h_poly_vec']
        f_code_cm_vec = proof['f_code_cm_vec']
        final_constant = proof['final_constant']
        query_paths = proof['query_paths']
        merkle_paths = proof['merkle_paths']

        r_vec = []
        sumcheck_sum = v
        half = kd >> 1
        for i in range(k):
            if self.debug > 0: 
                print("V> sumcheck round {}".format(i))

            h_evals = h_poly_vec[i]

            tr.absorb(b"h(X)", h_evals)

            assert len(h_evals) == 3, f"len(h_evals) != 3, len(h_evals) = {len(h_evals)}"

            assert sumcheck_sum == h_evals[0] + h_evals[1], \
                f"sumcheck_sum != h_evals[0] + h_evals[1], sumcheck_sum = {sumcheck_sum}, h[0] = {h_evals[0]}, h[1] = {h_evals[1]}"

            # Receive a random number from the verifier
            r = tr.squeeze(Fp, b"alpha", 4)
            if self.debug: 
                print(f"V> r[{i}] = {r}")
            r_vec.insert(0, r)
            sumcheck_sum = UniPolynomial.evaluate_from_evals(h_evals, r, [Fp(0),Fp(1),Fp(2)])

            if self.debug > 0: 
                print("V> FRI round {}".format(i))

            # f_code_folded = f_code_vec[i]
            # assert len(f_code_folded) == half * self.encoder.blowup_factor, \
            #     f"len(f_code_folded) != half * blowup_factor, len(f_code_folded) = {len(f_code_folded)}, half = {half}, blowup_factor = {self.encoder.blowup_factor}"
            
            if i == k-1:
                tr.absorb(b"f_final_code", final_constant)
            else:
                f_code_tree_root = f_code_cm_vec[i]
                tr.absorb(b"f_code_cm", f_code_tree_root)
            
            half = half >> 1

        eq_eval = MLEPolynomial.evaluate_eq_polynomial(us, r_vec)

        if self.debug > 0:
            print(f"V> verify sumcheck_sum")
            print(f"V> eq_eval = {eq_eval}, final_code[0] = {final_constant}, sumcheck_sum = {sumcheck_sum}")
            assert eq_eval * final_constant == sumcheck_sum, \
                f"eq_eval * final_code[0] != sumcheck_sum, eq_eval = {eq_eval}, final_code[0] = {final_constant}, sumcheck_sum = {sumcheck_sum}"
            print(f"V> verify sumcheck_sum passed ")

        checked01 = eq_eval * final_constant == sumcheck_sum

        # Reconstruct queries
        queries = []
        for i in range(self.num_queries):
            new_query = tr.squeeze(int, b"query", 16) % (nd)
            queries.append(new_query)

        checked02 = self.verify_queries(queries, k, f_cm.root, f_code_cm_vec, final_constant, 
                                      r_vec, query_paths, merkle_paths, nd)
        if self.debug > 0:
            print(f"V> verify queries")
            assert checked02, f"failed to verify queries"
            print(f"V> verify queries passed")

        return checked01 and checked02

    def verify_queries(self, 
                       queries: list[int],
                       d: int,
                       f0_code_cm: str,
                       f_code_cm_vec: list[str],
                       final_constant: Fp,
                       r_vec: list[Fp],
                       query_paths: list[list[tuple[Fp, Fp]]],
                       merkle_paths: list[list[tuple[list, list]]],
                       f0_code_len: int):
        """
        Verify the queries and the merkle paths

        Args:
            queries: [q0, q1, ..., q_{num_queries-1}]
            d: the number of rounds
            f0_code_cm: [f0]
            f_code_cm_vec: [f1], [f2], ..., [f_{d-1}]
            final_constant: f_d[0]
            r_vec: [r_{d-1}, r_{d-2}, ..., r_0]
            query_paths: [[(p0, p1), (p2, p3), ..., (p_{2^{d-1}-1}, p_{2^{d-1}})]
            merkle_paths: [[(p0, p1), (p2, p3), ..., (p_{2^{d-1}-1}, p_{2^{d-1}})]
            f0_code_len: |f0|
        """

        assert d == len(f_code_cm_vec) + 1, \
            f"d != len(f_code_cm_vec) + 1, d = {d}, len(f_code_cm_vec) = {len(f_code_cm_vec)}"
        
        # Reconstruct query_indices
        query_indices = []
        for q in queries:
            indices = []
            prev_idx = q
            half = f0_code_len//2
            for i in range(d):
                if prev_idx >= half:
                    x0, x1 = prev_idx - half, prev_idx
                else:
                    x0, x1 = prev_idx, prev_idx + half
                indices.append((x0,x1))
                prev_idx = x0
                half = half >> 1
            query_indices.append(indices)

        if self.debug > 0:
            print(f"V> query_indices={query_indices}")

        # Verify the merkle paths
        roots = [f0_code_cm] + f_code_cm_vec
        for i, (indices, cur_query, merkle_path) in enumerate(zip(query_indices, query_paths, merkle_paths)):
            for j in range(len(indices)):
                x0, x1 = indices[j]
                c0, c1 = cur_query[j]
                p0, p1 = merkle_path[j]
                checked0 = verify_decommitment(x0, c0, p0, roots[j])
                checked1 = verify_decommitment(x1, c1, p1, roots[j])
                assert checked0 and checked1, f"merkle_path-{i} failed at index {j}, x0={x0}, x1={x1}, p0={p0}, p1={p1}"
            if self.debug > 0:
                print(f"V> check merkle_path-{i} passed")

        # Verify the foldings
        for i, (indices, cur_query) in enumerate(zip(query_indices, query_paths)):
            half = f0_code_len//2
            for j, idx in enumerate(indices):
                x0, x1 = idx
                c0, c1 = cur_query[j]
                next_index = x0
                r = r_vec[d-j-1]  # NOTE: r_vec is in reverse order
                
                # print(f"table={tables[j]}, x0={x0}, c0={c0}, c1={c1}, r={r}")

                folded_value = (Fp(1)-r) * (c0 + c1) / Fp(2) + r * (c0 - c1) / (Fp(2) * self.encoder.tables[log_2(half) + 1][x0]) 
                next_pair= cur_query[j+1] if j<len(indices)-1 else (final_constant, final_constant)
                half >>= 1
                if next_index < half:
                    next = next_pair[0]
                else:
                    next = next_pair[1]
                assert next == folded_value, f"i={i}, j={j}, folded = {folded_value}, half = {half}, next_index = {next_index}, next = {next}"
            if self.debug > 0:
                print(f"V> check folding-{i} passed")
        return True

def test_prove_verify():
    
    encoder = FoldableRSCoder(k0=1, depth=3, c=2)
    print(f"encoder.tables={encoder.tables}")

    pcs = BASEFOLD_PCS(encoder, debug = 2)

    tr = MerlinTranscript(b"whir-rs-pcs")

    # # A simple instance f(x) = y
    evals = [Fp(1), Fp(3), Fp(2), Fp(1),
            Fp(2), Fp(-2), Fp(1), Fp(0),
            ]
    us = [Fp(2), Fp(-1), Fp(2)]

    f_mle = MLEPolynomial(evals, len(us))
    y = f_mle.evaluate(us)
    print(f"f({us}) = {y}")
    f_cm = pcs.commit(f_mle)

    print(f"f_cm.root = {f_cm.root}")
    print("🕐 Generating proof ....")
    v, arg = pcs.prove_eval(f_cm, f_mle, us, tr.fork(b"fork"))
    print("ℹ️ Proof generated.")

    assert v == y
    print("🕐 Verifying proof ....")
    checked = pcs.verify_eval(f_cm, us, v, arg, tr.fork(b"fork"))
    assert checked
    print("✅ Proof verified")

def test_prove_verify_random():

    blowup_factor_log2 = randint(1, 3)
    log_n = 10

    encoder = FoldableCoder(k0=1, depth=log_n, c=2 ** blowup_factor_log2)

    # print(f"encoder.tables={encoder.tables}")
    pcs = BASEFOLD_PCS(encoder, debug=2)

    tr = MerlinTranscript(b"basefold-pcs")

    # # A simple instance f(x) = y
    evals = [Fp.random() for _ in range(2 ** log_n)]
    us = [Fp.random() for _ in range(log_n)]

    f_mle = MLEPolynomial(evals, len(us))
    y = f_mle.evaluate(us)
    print(f"f({us}) = {y}")
    f_cm = pcs.commit(f_mle)

    print(f"f_cm.root = {f_cm.root}")
    print("🕐 Generating proof ....")
    v, arg = pcs.prove_eval(f_cm, f_mle, us, tr.fork(b"fork"))
    print("ℹ️ Proof generated.")

    assert v == y
    print("🕐 Verifying proof ....")
    checked = pcs.verify_eval(f_cm, us, v, arg, tr.fork(b"fork"))
    assert checked
    print("✅ Proof verified")


if __name__ == '__main__':

    test_prove_verify()
