#!/usr/bin/env python3

# WARNING: This implementation may contain bugs and has not undergone auditing. 
# It is intended for educational and research purposes only. 
# DO NOT use it in a production environment.

from functools import reduce
from operator import mul

from utils import is_power_of_two, log_2, next_power_of_two, bit_reverse, inner_product
from utils import prime_field_inv, Scalar

# Implementation of Whir (RS encoding) PCS [ACFY24]
#
# [ACFY24] WHIR: Reed-Solomon Proximity Testing with Super-Fast Verification
#
#  Author: Gal Arnon, Alessandro Chiesa, Giacomo Fenzi, Eylon Yogev
#  URL: https://eprint.iacr.org/2024/1586

from unipoly2 import UniPolynomial, UniPolynomialWithFft, bit_reverse_permutation
from mle2 import MLEPolynomial
from merkle import MerkleTree
from transcript import MerlinTranscript
from curve import Fr as BN254_Fr

from basefold_rs_pcs import Commitment, rs_encode

from typing import Optional, Union
from random import Random, randint

Fp = BN254_Fr

# from ff.tiny import F193
# Fp = F193

MLEPolynomial.set_field_type(Fp)
UniPolynomial.set_field_type(Fp)
UniPolynomialWithFft.set_field_type(Fp)

# TODO:
#  - [ ] Split do_one_fri_round into two functions:
#     - do_one_fri_commit_round
#     - do_one_fri_query_round
#
#  - [ ] Make security parameters configurable
#  - [ ] Add batching proving/verifying
#  - [ ] Support small fields

def eq_eval(r_vec, u_vec):
    assert len(r_vec) == len(u_vec), f"len(r_vec) = {len(r_vec)}, len(u_vec) = {len(u_vec)}"
    factors = [(Fp(1) - r) * (Fp(1) - u) + r * u for r, u in zip(r_vec, u_vec)]

    return reduce(mul, factors, Fp(1))

def compute_powers(alpha: Fp, n: int) -> list[Fp]:
        return [alpha**i for i in range(n)]

def compute_power_of_2_powers(alpha: Fp, n: int) -> list[Fp]:
        return [alpha**(2**i) for i in range(n)]

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

class RSCode:

    def __init__(self, f_coeffs: list[Fp], 
                 coset: Fp, 
                 blowup_factor: int,
                 debug=0):
        code = rs_encode(f_coeffs, coset, blowup_factor)
        self.code = code
        self.coset = coset
        self.blowup_factor = blowup_factor
        self.omega = Fp.nth_root_of_unity(len(code)) # TODO: to be optimized
        self.debug = debug

    def __len__(self):
        return len(self.code)
    
    def __getitem__(self, idx):
        return self.code[idx]
    
    def __setitem__(self, idx, value):
        raise NotImplementedError("RSCode is immutable")
    
    def __repr__(self):
        return f"RSCode(len={len(self.code)}, coset={self.coset}, blowup_factor={self.blowup_factor})"

def fold_code(code: list[Fp], 
              r_vec: list[Fp], 
              coset: Fp, 
              twiddles, debug=0) -> list[Fp]:
    k = len(r_vec)
    assert is_power_of_two(len(code)), "n must be a power of two"
    coseti = coset
    
    for round_idx in range(k):
        code_folded = [(code[2*i] + code[2*i+1]) / 2 
                        + r_vec[round_idx] * (code[2*i] - code[2*i+1]) / (2 * coseti * twiddles[i]) 
                        for i in range(len(code)//2)]
        
        if debug > 2:
            print("fold_code> show code folding")
            for i in range(len(code)//2):
                left = code[2*i]
                right = code[2*i+1]
                print(f"fold_code> 📒: {left} + {right} => {code_folded[i]}, r={r_vec[round_idx]},w={twiddles[i]},coset={coseti}")
        coseti *= coseti
        code = code_folded
    return code_folded

def fold_code_chunk(code_chunk: list[Fp], 
              r_vec: list[Fp], 
              coset: Fp, 
              start_idx: int, 
              size: int, 
              twiddles,
              debug=0) -> list[Fp]:
    assert len(code_chunk) == size, f"len(code_chunk) = {len(code_chunk)}, size = {size}"
    if debug > 2: print(f"fold_code_chunk> start_idx = {start_idx}, size = {size}")
    if debug > 2: print(f"fold_code_chunk> twiddles = {twiddles}")
    coset_round = coset
    twiddles_start_idx = start_idx // 2
    for round_idx in range(len(r_vec)):
        if debug > 0: print(f"fold_code_chunk> {round_idx}-th round, twiddles_start_idx = {twiddles_start_idx}")
        code_chunk_folded = [(code_chunk[2*i] + code_chunk[2*i+1]) / 2 
                        + r_vec[round_idx] * (code_chunk[2*i] - code_chunk[2*i+1]) / (2 * coset_round * twiddles[twiddles_start_idx+i]) 
                        for i in range(len(code_chunk)//2)]

        if debug > 2:
            print("fold_code_chunk> show code chunk folding")
            for i in range(len(code_chunk)//2):
                left = code_chunk[2*i]
                right = code_chunk[2*i+1]
                print(f"fold_code_chunk> 📒: {left} + {right} => {code_chunk_folded[i]}, r={r_vec[round_idx]},w={twiddles[twiddles_start_idx+i]},coset={coset_round}")

        coset_round *= coset_round
        code_chunk = code_chunk_folded
        twiddles_start_idx = twiddles_start_idx // 2
    return code_chunk_folded

def eq_sum(eqs: list[list[Fp]], gamma: Fp) -> list[Fp]:
    n = len(eqs[0])
    new_eq = [Fp(0)] * n
    for i, eq in enumerate(eqs):
        assert len(eq) == n, f"i={i},len(eq) = {len(eq)}, n = {n}"
        for j in range(n):
            new_eq[j] += eq[j] * gamma**i

    return new_eq

class WHIR_RS_PCS:

    # WARNING: the following parameters are not secure. They are only for demonstration,
    #  NOT for production. 
    # TODO: change to configurable parameters

    initial_blowup_factor = 2 
    folding_factor_log = 2              # folding parameters `k0, k1, ..., k_{M-1}` in [Sec 5, ACFY24]
    domain_folding_factor_log = 1       # |L_i| = |L_{i-1}| * 2^domain_folding_factor_log
    coset_gen = Fp.multiplicative_generator()
    max_queries_try = 1000              # NOTE: change it to a practical number
    num_queries = 2                     # repetition parameters `t1, t2, ..., t_M` in [Sec 5, ACFY24]

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
        f_coeffs = MLEPolynomial.compute_coeffs_from_evals(evals)

        f_code = RSCode(f_coeffs, self.coset_gen, self.initial_blowup_factor)
        f_tree = MerkleTree(f_code.code)

        assert len(f_code) == 2**f_mle.num_var * self.initial_blowup_factor, \
            f"len(evals)={len(evals)}, f_mle.num_var={f_mle.num_var}, blowup_factor={self.blowup_factor}"
        cm = Commitment(f_tree)
        return cm

    def do_one_sumcheck_round(self, iteration_idx: int, k: int, f, f_coeffs, eq, sum_checked, tr: MerlinTranscript):
        """
        Do one 2^k-step sumcheck round for the `iteration_idx`-th round.
        """
        assert len(f) == len(eq), f"len(f) = {len(f)}, len(eq) = {len(eq)}"
        assert len(f) >= 2**k, f"len(f) = {len(f)}, k = {k}"

        half = len(f) >> 1
        r_vec = []
        sumcheck_h_vec = []

        if self.debug > 0:
            print(f"P> -- BEGIN Sumcheck Round-{iteration_idx} --")

        for i in range(k):
            f_even = f[::2]
            f_odd = f[1::2]
            eq_even = eq[::2]
            eq_odd = eq[1::2]

            if self.debug > 2:
                print(f"P> Sumcheck> sum_checked = {sum_checked}")
                print(f"P> Sumcheck> f = {f}")
                print(f"P> Sumcheck> eq = {eq}")
                print(f"P> Sumcheck> f_even = {f_even}, f_odd = {f_odd}, eq_even = {eq_even}, eq_odd = {eq_odd}")

            # construct h(X)
            h_eval_at_0 = sum([f_even[j] * eq_even[j] for j in range(half)], Fp.zero())
            h_eval_at_1 = sum([f_odd[j] * eq_odd[j] for j in range(half)], Fp.zero())
            h_eval_at_2 = sum([ (2 * f_odd[j] - f_even[j]) * (2 * eq_odd[j] - eq_even[j]) for j in range(half)])
            h = [h_eval_at_0, h_eval_at_1, h_eval_at_2]
            sumcheck_h_vec.append(h)

            tr.absorb(b"h(X)", h)
            print(f"P> Sumcheck> tr.state = {tr.state}")
            if self.debug > 0:
                print(f"P> Sumcheck> h = {h}")

            # check sum
            assert h_eval_at_0 + h_eval_at_1 == sum_checked, \
                f"h_eval_at_0 + h_eval_at_1 = {h_eval_at_0 + h_eval_at_1}, sum_checked = {sum_checked}"
            
            # Receive a random number from the verifier
            r = tr.squeeze(Fp, b"r", 4)
            if self.debug > 0:
                print(f"P> Sumcheck> r[{i}] = {r}")
            r_vec.append(r)
            
            # fold f
            f = [(Fp(1) - r) * f_even[i] + r * f_odd[i] for i in range(half)]
            eq = [(Fp(1) - r) * eq_even[i] + r * eq_odd[i] for i in range(half)]

            # update sumcheck for the next round
            sum_checked = UniPolynomial.evaluate_from_evals(h, 
                        r, [Fp.zero(), Fp.one(), Fp(2)])
            half >>= 1

        ## End of the big loop for `i`
        if self.debug > 1:
            print(f"P> Sumcheck> sum_checked = {sum_checked}, r_vec = {r_vec}")

        # Compute the folded coefficients of f_i(X), which is folded from f_{i-1}(X) by `r_vec`.
        # NOTE: The f_coeffs will be used to compute code for f_i(X). So we compute 
        #       the folded coefficients here along with the evaluations folding.
        f_coeffs_folded = f_coeffs
        for r in r_vec:
            f_coeffs_even = f_coeffs_folded[::2]
            f_coeffs_odd = f_coeffs_folded[1::2]
            f_coeffs_folded = [f_coeffs_even[i] + r * f_coeffs_odd[i] for i in range(len(f_coeffs_folded)//2)]

        if self.debug > 1:
            print(f"P> Sumcheck> check f_coeffs folding")
            evals = MLEPolynomial.compute_evals_from_coeffs(f_coeffs_folded)
            assert evals == f, f"evals={evals}, f={f}"
            print(f"P> Sumcheck> check f_coeffs folding passed")

        # Check the k-round sumcheck inside one whir-round 
        if self.debug > 1:
            print(f"P> Sumcheck> Check k-round sumcheck")
            eval = Fp.zero()
            for i in range(len(f)):
                eval += f[i] * eq[i]
            assert sum_checked == eval, \
                f"sum_checked = {sum_checked}, eval = {eval}"
            print(f"P> Sumcheck> Check k-round sumcheck passed")

        if self.debug > 0:
            print(f"P> -- END Sumcheck Round-{iteration_idx} --")
    
        return f, f_coeffs_folded, eq, sum_checked, r_vec, sumcheck_h_vec
    
    def do_one_fri_round(self, 
                         iteration_idx: int,            # i-th iteration
                         k: int, 
                         f_folded: list[Fp],        # f_i(X)
                         f_folded_coeffs: list[Fp], # f_i(X)
                         f_code: RSCode,            # f_{i-1}(X)
                         r_vec: list[Fp], 
                         t: int,                    # query factor for L^{2^k}_{i-1}
                         l: int,                    # folding factor for L_{i-1}/L_i
                         omega: Fp,
                         coset: Fp, 
                         tr: MerlinTranscript):
        """
        """

        assert l <= len(r_vec), f"l = {l}, len(r_vec) = {len(r_vec)}"
        assert k == len(r_vec), f"k = {k}, len(r_vec) = {len(r_vec)}"

        new_blowup_factor = f_code.blowup_factor * (2**(k-l))

        if self.debug > 0:
            print(f"P> -- BEGIN FRI round {iteration_idx} --")
            print(f"P> FRI> new_blowup_factor = {new_blowup_factor}")

        f_folded_code = RSCode(f_folded_coeffs, coset, new_blowup_factor, self.debug)
        f_folded_code_cm = Commitment(MerkleTree(f_folded_code.code))
        f_folded_mle = MLEPolynomial(f_folded, log_2(len(f_folded)))

        if self.debug > 1:
            print(f"P> FRI> check f_folded_code ")
            f_folded_coeffs = MLEPolynomial.compute_coeffs_from_evals(f_folded)
            f_folded_uni = UniPolynomialWithFft(f_folded_coeffs)
            omega_code = Fp.nth_root_of_unity(len(f_folded_code))
            D = compute_powers(omega_code, len(f_folded_code))
            D_rbo = bit_reverse_permutation(D)
            evals = [f_folded_uni.evaluate(d * coset) for d in D_rbo]
            assert evals == f_folded_code.code, f"evals={evals}, f1_code={f_folded_code.code}"

            for i in range(len(D_rbo)):
                w = D_rbo[i]
                w_pow = compute_power_of_2_powers(w * coset, f_folded_mle.num_var)
                assert f_folded_code[i] == f_folded_mle.evaluate(w_pow), \
                    f"f_folded_code[{i}] = {f_folded_code[i]}, f_folded_mle.evaluate(w_pow) = {f_folded_mle.evaluate(w_pow)}"

            print(f"P> FRI> check f_folded_code passed")

        tr.absorb(b"f_folded_code_cm", f_folded_code_cm.cm)
        if  self.debug > 0:
            print(f"P> FRI> code = {f_folded_code_cm.cm}, len(code) = {len(f_folded_code)}")

        # > Sample-phase: out-of-domain query and reply.

        z0 = tr.squeeze(Fp, b"z0", 4)
        z0_pow = compute_power_of_2_powers(z0, f_folded_mle.num_var)
        y0 = f_folded_mle.evaluate(z0_pow)

        tr.absorb(b"y0", y0)
        if self.debug > 0:
            print(f"P> FRI> z0={z0}, y0 = {y0}")

        # > Query-phase: in-domain queries to ensure the code is folded correctly.

        # Sample {zi} from f^{2^k}_{i-1} 
        f_code_folded_len = len(f_code)//2**k

        z_idx_vec = []
        for i in range(self.max_queries_try):
            z_idx = tr.squeeze(int, b"zi", 4) % f_code_folded_len
            if z_idx not in z_idx_vec:
                z_idx_vec.append(z_idx)
            else:
                continue
            if len(z_idx_vec) >= t:
                break
        assert len(z_idx_vec) == t, f"len(z_idx_vec) = {len(z_idx_vec)}, t = {t}"
        if self.debug > 1:
            print(f"P> FRI> z_idx_vec = {z_idx_vec}, from [0..{f_code_folded_len})")
        
        # omega is the root of unity for the domain of `f_code`
        # new_omega is the root of unity for the the domain of `f_code_folded`
        new_omega = omega**(2**k)

        # compute {(zi, yi)}, where yi = f_i(zi)
        z_vec, y_vec = [], []
        for i in range(t):
            idx = z_idx_vec[i]
            zi = new_omega** bit_reverse(idx, log_2(f_code_folded_len))
            z_vec.append(zi)
            zi_pow = compute_power_of_2_powers(zi * coset**(2**k), f_folded_mle.num_var)
            y_vec.append(f_folded_mle.evaluate(zi_pow))

        if self.debug > 1:
            print(f"P> FRI> z_vec = {z_vec}, y_vec = {y_vec}")

        # collect leaves of the code `f_{i-1}(X)` for constructing `yi=f(zi)`
        query_replies = []
        for i in range(t):
            idx = z_idx_vec[i]
            start_idx = idx*2**k
            query_reply = f_code[start_idx: start_idx + 2**k]
            query_replies.append(query_reply)

        if self.debug > 1:
            print(f"P> FRI> check query replies (num={t})")
            for i in range(t):
                idx = z_idx_vec[i]
                start_idx = idx*2**k
                query_reply = f_code[start_idx: start_idx + 2**k]
                query_reply_folded = fold_code_chunk(query_reply, r_vec, coset, start_idx, 2**k, self.twiddles)
                print(f"P> FRI> check query-reply-{i} = {query_reply}")
                assert len(query_reply_folded) == int(1), \
                        f"len(code_folded) = {len(query_reply_folded)}, query_reply = {query_reply}, r_vec = {r_vec}, coset = {coset}"
                assert query_reply_folded[0] == y_vec[i], \
                        f"code_folded[0] = {query_reply_folded[0]}, y_vec[{i}] = {y_vec[i]}"
                print(f"P> FRI> check query-reply-{i} passed")

        tr.absorb(b"query_replies", query_replies)

        if self.debug > 1:
            print(f"P> FRI> query_replies = {query_replies}")

        if self.debug > 0:
            print(f"P> -- END FRI round {iteration_idx} --")

        return f_folded_code, f_folded_code_cm, z0, y0, z_vec, y_vec, query_replies

    def do_final_fri_round(self, 
                           iteration_idx: int, 
                           k: int, 
                           f_coeffs: list[Fp], # TODO: remove this
                           f_folded: list[Fp],
                           f_folded_coeffs: list[Fp],
                           f_code: RSCode, 
                           r_vec: list[Fp], 
                           t, 
                           omega: Fp,
                           coset: Fp, 
                           tr: MerlinTranscript):
        
        if self.debug > 0:
            print(f"P> -- BEGIN Final FRI round {iteration_idx} --")

        assert len(f_folded) == len(f_folded_coeffs), \
            f"len(f_folded) = {len(f_folded)}, len(f_folded_coeffs) = {len(f_folded_coeffs)}"
        assert len(f_folded) * 2**k == len(f_coeffs), \
            f"len(f_folded) = {len(f_folded)}, len(f_coeffs) = {len(f_coeffs)}"
        assert len(f_coeffs) * f_code.blowup_factor == len(f_code), \
            f"len(f) = {len(f_coeffs)}, len(f_code) = {len(f_code)}"

        f_folded_mle = MLEPolynomial(f_folded, log_2(len(f_folded)))

        if self.debug > 1:
            print(f"P> FRI> check f_code")
            f_code_folded = fold_code(f_code.code, r_vec, coset, self.twiddles)

            f_code_folded_len = len(f_code_folded)
            new_omega = Fp.nth_root_of_unity(f_code_folded_len)
            D = compute_powers(new_omega, len(f_code_folded))
            D_rbo = bit_reverse_permutation(D)
            # TODO:
            # f_uni = UniPolynomialWithFft(f_coeffs)
            # f_evals = [f_uni.evaluate(d * coset**(2**k)) for d in D_rbo]
            # assert f_evals == f_code_folded, f"f_evals={f_evals}, f_code_folded={f_code_folded}"

            for i in range(len(D_rbo)):
                w = D_rbo[i]
                w_pow = compute_power_of_2_powers(w * coset**(2**k), f_folded_mle.num_var)
                print(f"P> FRI> w = {w}, w_pow = {w_pow}")
                assert f_code_folded[i] == f_folded_mle.evaluate(w_pow), \
                    f"f_code_folded[{i}] = {f_code_folded[i]}, f_folded_mle.evaluate(w_pow) = {f_folded_mle.evaluate(w_pow)}"
            print(f"P> FRI> check f_code passed")

        tr.absorb(b"final_f_evals", f_folded)

        # > No more sample-phase, just query-phase.

        # > Query-phase: in-domain queries to ensure the code is folded correctly.

        f_folded_code_len = len(f_code)//2**k

        z_idx_vec = []
        for i in range(self.max_queries_try):
            z_idx = tr.squeeze(int, b"zi", 4) % f_folded_code_len
            if z_idx not in z_idx_vec:
                z_idx_vec.append(z_idx)
            else:
                continue
            if len(z_idx_vec) >= t:
                break
        assert len(z_idx_vec) == t, f"len(z_idx_vec) = {len(z_idx_vec)}, t = {t}"
        if self.debug > 1:
            print(f"P> FRI> z_idx_vec = {z_idx_vec}, from [0..{f_folded_code_len})")
        
        new_omega = f_code.omega**(2**k)
        print(f"P> FRI> new_omega = {new_omega}")
        # compute {(zi, yi)}, where yi = f_i(zi)
        z_vec, y_vec = [], []
        for i in range(t):
            zi = new_omega** bit_reverse(z_idx_vec[i], log_2(f_folded_code_len))
            z_vec.append(zi)
            zi_pow = compute_power_of_2_powers(zi * coset**(2**k), f_folded_mle.num_var)
            y_vec.append(f_folded_mle.evaluate(zi_pow))

        if self.debug > 1:
            print(f"P> FRI> z_idx_vec = {z_idx_vec}")
            print(f"P> FRI> z_vec = {z_vec}, y_vec = {y_vec}")

        # collect leaves of the code for constructing `yi=f(zi)`
        query_replies = []
        for i in range(t):
            idx = z_idx_vec[i]
            start_idx = idx*2**k
            query_reply = f_code[start_idx: start_idx + 2**k]
            query_replies.append(query_reply)
        print(f"P> FRI> query_replies = {query_replies}")

        if self.debug > 1:
            print(f"P> FRI> check query replies (num={t})")
            for j in range(t):
                idx = z_idx_vec[j]
                start_idx = idx*2**k
                print(f"r_vec = {r_vec}")
                query_reply_folded = fold_code_chunk(query_replies[j], r_vec, coset, start_idx, 2**k, self.twiddles)
                assert len(query_reply_folded) == int(1), \
                    f"len(code_folded) = {len(query_reply_folded)}, query_reply = {query_reply}, r_vec = {r_vec}, coset = {coset}"
                assert query_reply_folded[0] == y_vec[j], \
                    f"code_folded = {query_reply_folded}, y_vec[{j}] = {y_vec[j]}"
                print(f"P> FRI> check query-reply-{j} passed")

        tr.absorb(b"query_replies", query_replies)

        if self.debug > 1:
            print(f"P> FRI> query_replies = {query_replies}")

        if self.debug > 0:
            print(f"P> -- END Final FRI round {iteration_idx} --")

        return z_vec, query_replies

    def do_sumcheck_merge(self,
                          num_queries: int, folding_factor: int, 
                          sum_checked: Fp,
                          f_folded: list[Fp],
                          eq_folded: list[Fp],
                          z0: Fp, y0: Fp, 
                          z_vec: list[Fp], y_vec: list[Fp], 
                          remain_folding_factor: int,
                          coset: Fp,
                          tr: MerlinTranscript):
        """
        Merge sumchecks from the FRI queries into the main sumcheck.
        """

        t = num_queries
        k = folding_factor
        
        gamma = tr.squeeze(Fp, b"gamma", 4)
        if self.debug > 0:
            print(f"P> gamma = {gamma}")
        
        new_sum_checked = sum_checked + gamma * y0

        z0_pow = compute_power_of_2_powers(z0, remain_folding_factor)
        eqz0 = MLEPolynomial.eqs_over_hypercube(z0_pow)

        eqz_list = []
        for i, zi, yi in zip(range(t), z_vec, y_vec):
            # NOTE: `zi` is actually in the coset domain
            zi_pow = compute_power_of_2_powers(zi * (coset**(2**k)), remain_folding_factor)
            eqzi = MLEPolynomial.eqs_over_hypercube(zi_pow)
            new_sum_checked += gamma**(i+2) * yi
            eqz_list.append(eqzi)

        if self.debug > 1:
            print(f"P> new_sum_checked = {new_sum_checked}")

        new_eq = eq_sum([eq_folded, eqz0] + eqz_list, gamma)

        if self.debug > 1:
            print(f"P> check new_eq and new_sum")
            eval = sum([f_folded[i] * new_eq[i] for i in range(len(f_folded))])
            assert eval == new_sum_checked, \
                f"f_folded(z) = {eval}, new_sum_checked = {new_sum_checked}"
            print(f"P> check new_eq and new_sum passed")

        return new_sum_checked, new_eq

    def prove_eval(self, 
                    f_cm: Commitment, 
                    f_mle: MLEPolynomial, 
                    us: list[Fp], 
                    tr: MerlinTranscript) -> tuple[Fp, dict]:
        """
        Generate evaluation proof for f_mle(us) = v

        Args:
            f_cm: the commitment to the polynomial
            f_mle: the MLE polynomial to evaluate
            us: the evaluation point
            tr: the proof transcript

        Returns:
            tuple[Fp, dict]: the evaluation value and the argument
        """

        tr = MerlinTranscript(b"whir-rs-pcs")
        print(f"P> tr.state = {tr.state}")

        assert f_mle.num_var == len(us), f"f_mle.num_var={f_mle.num_var}, len(us)={len(us)}"

        total_k = f_mle.num_var

        k = self.folding_factor_log
        # Evaluate f_mle at the point us
        v = f_mle.evaluate(us)
        f0 = f_mle.evals.copy()

        if self.debug > 0:
            print(f"P> f0_len={len(f0)}, k={k}, f0_code_len ={len(f0) * self.initial_blowup_factor}")

        eq = MLEPolynomial.eqs_over_hypercube(us)
        if self.debug > 0:
            print(f"P> eq0 = {eq}")
        eq_mle = MLEPolynomial(eq, total_k)

        # > Preparation
        
        f0_coeffs = MLEPolynomial.compute_coeffs_from_evals(f0)

        f0_code = RSCode(f0_coeffs, self.coset_gen, self.initial_blowup_factor, debug=self.debug)
        f0_code_len = len(f0_code)
        if self.debug > 0:
            print(f"P> f0_code_len = {f0_code_len}")
            print(f"P> f0_code = {f0_code.code}")

        omega = Fp.nth_root_of_unity(f0_code_len)
        D0 = compute_powers(omega, len(f0_code))
        D0_rbo = bit_reverse_permutation(D0)
        coset = self.coset_gen
        # NOTE: the array of twiddles are bit-reversed, such that it can be reused for all rounds.
        twiddles = UniPolynomialWithFft.precompute_twiddles_for_fft(f0_code_len, is_bit_reversed=True)
        self.twiddles = twiddles

        if self.debug > 1:
            print(f"P> check f0_code")
            f_orig_evals = bit_reverse_permutation(f0_code.code)
            f_orig_coeffs = UniPolynomialWithFft.ifft_coset(f_orig_evals, self.coset_gen, total_k + log_2(self.initial_blowup_factor))
            assert f_orig_coeffs[:len(f0_coeffs)] == f0_coeffs, \
                f"f_orig_coeffs != f_coeffs, {f_orig_coeffs} != {f0_coeffs}"
            print(f"P> check f0_code passed")

        if self.debug > 1:
            print(f"P> check rs_encode")
            f_uni = UniPolynomial(f0_coeffs)
            for i in range(len(f0_code)):
                w = D0_rbo[i]
                assert f_uni.evaluate(w * coset) == f0_code[i], \
                    f"f_uni.evaluate(D_rbo[{i}]) = {f_uni.evaluate(w)}, f0_code[{i}] = {f0_code[i]}"
                w_pow = compute_power_of_2_powers(w * coset, f_mle.num_var)
                assert f_mle.evaluate(w_pow) == f0_code[i], \
                    f"f_mle.evaluate(D_rbo[{i}]) = {f_mle.evaluate(w_pow)}, f0_code[{i}] = {f0_code[i]}"
            print(f"P> check rs_encode passed")

        messages_all_rounds = []

        f = f0
        f_code = f0_code
        f_coeffs = f0_coeffs
        eq = MLEPolynomial.eqs_over_hypercube(us)
        # eq_mle = MLEPolynomial(eq, log_2(f0_len))

        # Update transcript with the context
        tr.absorb(b"f_code_merkle_root", f_cm.root)
        print(f"P> tr.state = {tr.state}")
        tr.absorb(b"point", us)
        print(f"P> tr.state = {tr.state}")
        tr.absorb(b"value", v)
        print(f"P> tr.state = {tr.state}")
        print(f"P> str(v).encode() = {str(v).encode()}, type(v)={type(v)}")
        t = self.num_queries
        all_r_vec = []
        num_iterations = total_k // self.folding_factor_log
        sum_checked = v
        remain_k = total_k

        if self.debug > 0:
            print(f"P> ------- BEFORE ITERATION -------")
            print(f"P> total_k = {total_k}, folding_factor = {self.folding_factor_log}")
            print(f"P> num_iterations = {num_iterations}")

        # > BEGIN of iteration
        for iteration_idx in range(num_iterations+1):

            if self.debug > 0:
                print(f"P> ------- ENTER ITERATION {iteration_idx} -------")

            # > Sumcheck
            rs = self.do_one_sumcheck_round(iteration_idx, self.folding_factor_log, 
                                            f, f_coeffs, eq, sum_checked, tr)
            f_folded, f_folded_coeffs, eq_folded, new_sum_checked, r_vec, sumcheck_h_vec = rs

            if self.debug > 0:
                print(f"P> new_sum_checked = {new_sum_checked}")
                print(f"P> r_vec = {r_vec}")

            # > Update loop variables
            remain_k -= k
            all_r_vec += r_vec

            if iteration_idx == num_iterations or remain_k <= self.folding_factor_log:

                # Break and jump to the final FRI round
                break

            # > Fold code
            rs = self.do_one_fri_round(iteration_idx, self.folding_factor_log, 
                                       f_folded, 
                                       f_folded_coeffs,
                                       f_code,
                                       r_vec, 
                                       t, self.domain_folding_factor_log,
                                       omega, coset, tr)
            
            # TODO: return merkle-paths for queries
            f_folded_code, f_folded_code_cm, z0, y0, z_vec, y_vec, query_replies = rs

            if self.debug > 1:
                print(f"P> code_cm.root = {f_folded_code_cm.cm}, len(code) = {len(f_folded_code)}")
                print(f"P> z0 = {z0}, y0 = {y0}, z_vec = {z_vec}, y_vec = {y_vec}")

            # > Aggregate sumchecks 

            rs = self.do_sumcheck_merge(t, k, new_sum_checked, 
                                        f_folded,
                                        eq_folded, 
                                        z0, y0, z_vec, y_vec, 
                                        remain_k, coset, tr)
            new_sum_checked, new_eq = rs

            # > Update loop variables for the next iteration
            f = f_folded
            f_coeffs = f_folded_coeffs
            f_code = f_folded_code
            sum_checked = new_sum_checked
            eq = new_eq

            # > Record messages
            messages_all_rounds.append((sumcheck_h_vec, (len(f_folded_code), f_folded_code_cm.cm), y0, query_replies))

            if self.debug > 0:
                print(f"P> total_k = {total_k}, acc_k = {total_k-remain_k}, remain_k = {remain_k}")
                print(f"P> ------- EXIT ITERATION {iteration_idx} -------")

        # > END of iteration
        if self.debug > 0:
            print(f"P> f_coeffs = {f_coeffs}")

        # > Final FRI round
        z_vec, query_replies = self.do_final_fri_round(iteration_idx, self.folding_factor_log, 
                                                    f_coeffs,
                                                    f_folded, f_folded_coeffs, f_code, 
                                                    r_vec, t, 
                                                    omega, coset, tr)
        
        if self.debug > 0:
            print(f"P> z_vec = {z_vec}")

        messages_all_rounds.append((sumcheck_h_vec, (), None, query_replies))

        return v, {"messages": messages_all_rounds,
                   "final_poly_evals": f_folded
                   }


    def verify_one_sumcheck_round(self, iteration_idx: int, 
                                  k: int,
                                  sum_checked: Fp,
                                  sumcheck_h_vec: list[list[Fp]],
                                  tr: MerlinTranscript):

        r_vec = []
        for i in range(k):
            if self.debug > 0:
                print(f"V> Sumcheck> Round {i}")
            h = sumcheck_h_vec[i]
            h_eval_at_0 = h[0]
            h_eval_at_1 = h[1]
            h_eval_at_2 = h[2]

            tr.absorb(b"h(X)", h)

            # check sum
            assert h_eval_at_0 + h_eval_at_1 == sum_checked, \
                f"h_eval_at_0 + h_eval_at_1 = {h_eval_at_0 + h_eval_at_1}, sum_checked = {sum_checked}"
            
            # Receive a random number from the verifier
            r = tr.squeeze(Fp, b"r", 4)
            if self.debug > 0:
                print(f"V> Sumcheck> r[{i}] = {r}")
            r_vec.append(r)

            # update sumcheck for the next round
            sum_checked = UniPolynomial.evaluate_from_evals(h, r, [Fp.zero(), Fp.one(), Fp(2)])

        return sum_checked, r_vec

    def verify_one_fri_round(self, iteration_idx: int, 
                              k: int,
                              f_code_cm_root: str,
                              f_folded_code_cm_root: str,
                              f_code_len: int,
                              y0: Fp,
                              query_replies: list[list[Fp]],
                              r_vec: list[Fp],
                              t: int,
                              omega: Fp,
                              coset: Fp,
                              tr: MerlinTranscript):
        if self.debug > 0:
            print(f"V> -- BEGIN FRI round {iteration_idx} --")
    
        # > Recieve the root of the code
        tr.absorb(b"f_folded_code_cm", f_folded_code_cm_root)
        print(f"V> FRI> f_folded_code_cm.root = {f_folded_code_cm_root}, type(f_folded_code_cm.root) = {type(f_folded_code_cm_root)}")

        # > Sample-phase: out-of-domain query and reply.

        z0 = tr.squeeze(Fp, b"z0", 4)

        tr.absorb(b"y0", y0)

        if self.debug > 0:
            print(f"V> FRI> z0={z0}, y0 = {y0}")

        # > Query-phase: in-domain queries to ensure the code is folded correctly.

        # Sample {zi} from f^{2^k}_{i-1} 
        f_code_folded_len = f_code_len//2**k

        z_idx_vec = []
        for i in range(self.max_queries_try):
            z_idx = tr.squeeze(int, b"zi", 4) % f_code_folded_len
            if z_idx not in z_idx_vec:
                z_idx_vec.append(z_idx)
            else:
                continue
            if len(z_idx_vec) >= t:
                break
        assert len(z_idx_vec) == t, f"len(z_idx_vec) = {len(z_idx_vec)}, t = {t}"
        
        if self.debug > 1:
            print(f"V> FRI> z_idx_vec = {z_idx_vec}, from [0..{f_code_folded_len})")

        new_omega = omega**(2**k)

        z_vec, y_vec = [], []
        for i in range(t):
            idx = z_idx_vec[i]
            zi = new_omega** bit_reverse(idx, log_2(f_code_folded_len))
            z_vec.append(zi)
            query_reply = query_replies[i]
            query_reply_folded = fold_code_chunk(query_reply, r_vec, coset, idx*2**k, 2**k, self.twiddles)
            assert len(query_reply_folded) == int(1), \
                f"len(code_folded) = {len(query_reply_folded)}, query_reply = {query_reply}, r_vec = {r_vec}, coset = {coset}"
            yi = query_reply_folded[0]
            y_vec.append(yi)

        tr.absorb(b"query_replies", query_replies)
        if self.debug > 1:
            print(f"V> FRI> query_replies = {query_replies}")

        if self.debug > 0:
            print(f"V> -- END FRI round {iteration_idx} --")

        return z0, y0, z_vec, y_vec

    def verify_final_fri_round(self, iteration_idx: int, k: int, 
                                f_folded: list[Fp],
                                f_code_len: int,
                                query_replies: list[list[Fp]],
                                r_vec: list[Fp], 
                                t: int,
                                omega: Fp, coset: Fp,
                                tr: MerlinTranscript):
        if self.debug > 0:
            print(f"V> -- BEGIN Final FRI round {iteration_idx} --")

        # > Recieve the final polynomial (in evaluations form)
        tr.absorb(b"final_f_evals", f_folded)

        # > No more sample-phase, just query-phase.

        # > Query-phase: in-domain queries to ensure the code is folded correctly.

        f_folded_code_len = f_code_len//2**k

        z_idx_vec = []
        for i in range(self.max_queries_try):
            z_idx = tr.squeeze(int, b"zi", 4) % f_folded_code_len
            if z_idx not in z_idx_vec:
                z_idx_vec.append(z_idx)
            else:
                continue
            if len(z_idx_vec) >= t:
                break
        assert len(z_idx_vec) == t, f"len(z_idx_vec) = {len(z_idx_vec)}, t = {t}"

        if self.debug > 1:
            print(f"V> FRI> z_idx_vec = {z_idx_vec}, from [0..{f_folded_code_len})")
        
        new_omega = Fp.nth_root_of_unity(f_code_len)**(2**k)
        if self.debug > 1:
            print(f"V> FRI> new_omega = {new_omega}")

        # compute {(zi, yi)}, where yi = f_i(zi)
        z_vec, y_vec = [], []
        for i in range(t):
            idx = z_idx_vec[i]
            zi = new_omega** bit_reverse(idx, log_2(f_folded_code_len))
            z_vec.append(zi)
            query_reply = query_replies[i]
            query_reply_folded = fold_code_chunk(query_reply, r_vec, coset, idx*2**k, 2**k, self.twiddles)
            assert len(query_reply_folded) == int(1), \
                f"len(code_folded) = {len(query_reply_folded)}, query_reply = {query_reply}, r_vec = {r_vec}, coset = {coset}"
            yi = query_reply_folded[0]
            y_vec.append(yi)           

        tr.absorb(b"query_replies", query_replies)

        if self.debug > 1:
            print(f"V> FRI> query_replies = {query_replies}")
            print(f"V> FRI> z_vec = {z_vec}, y_vec = {y_vec}")

        if self.debug > 0:
            print(f"V> -- END Final FRI round {iteration_idx} --")

        return z_vec, y_vec
    
    def verify_sumcheck_merge(self,
                          num_queries: int, folding_factor: int, 
                          sum_checked: Fp,
                          z0: Fp, y0: Fp, 
                          z_vec: list[Fp], y_vec: list[Fp], 
                          remain_folding_factor: int,
                          coset: Fp,
                          tr: MerlinTranscript):
        """
        Merge sumchecks from the FRI queries into the main sumcheck.
        """

        t = num_queries
        k = folding_factor
        
        gamma = tr.squeeze(Fp, b"gamma", 4)
        if self.debug > 0:
            print(f"V> gamma = {gamma}")
        
        new_sum_checked = sum_checked + gamma * y0

        # z0_pow = compute_power_of_2_powers(z0, remain_folding_factor - k)
        # eqz0 = MLEPolynomial.eqs_over_hypercube(z0_pow)

        # eqz_list = []
        for i, zi, yi in zip(range(t), z_vec, y_vec):
            # NOTE: `zi` is actually in the coset domain
            # zi_pow = compute_power_of_2_powers(zi * (coset**(2**k)), remain_folding_factor - k)
            # eqzi = MLEPolynomial.eqs_over_hypercube(zi_pow)
            new_sum_checked += gamma**(i+2) * yi
            # eqz_list.append(eqzi)

        # new_eq = eq_sum([eq_folded, eqz0] + eqz_list, gamma)

        return gamma, new_sum_checked
    
    def verify_eval(self, 
                    f_cm: Commitment, 
                    us: list[Fp], 
                    v: Fp,
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
        total_k = len(us)

        # Load the argument
        messages = arg['messages']
        final_poly_evals = arg['final_poly_evals']

        # > Preparation

        eq = MLEPolynomial.eqs_over_hypercube(us)
        eq_mle = MLEPolynomial(eq, total_k)

        tr.absorb(b"f_code_merkle_root", f_cm.cm)
        tr.absorb(b"point", us)
        tr.absorb(b"value", v)

        t = self.num_queries
        all_r_vec = []
        all_gamma_z_y_vec = []
        num_iterations = total_k // self.folding_factor_log
        remain_k = total_k
        acc_k = 0
        if self.debug > 0:
            print(f"V> ------- BEFORE ITERATION -------")
            print(f"V> total_k = {total_k}, folding_factor = {self.folding_factor_log}")
            print(f"V> num_iterations = {num_iterations}")

        sum_checked = v
        f_code_cm_root = f_cm.cm
        f_code_len = 2**total_k * self.initial_blowup_factor
        omega = Fp.nth_root_of_unity(f_code_len)
        coset = self.coset_gen
        
        # > BEGIN of Iteration
        for iteration_idx in range(num_iterations+1):
            
            (sumcheck_h_vec, f_folded_code_cm, y0, query_replies) = messages[iteration_idx]
            if self.debug > 0:
                print(f"V> ------- ENTER ITERATION {iteration_idx} -------")

            # > Sumcheck
            k = self.folding_factor_log
            rs = self.verify_one_sumcheck_round(iteration_idx, k, sum_checked, sumcheck_h_vec, tr)
            new_sum_checked, r_vec = rs

            if self.debug > 1:
                print(f"V> new_sum_checked = {new_sum_checked}")
                print(f"V> r_vec = {r_vec}")

            all_r_vec += r_vec
            remain_k -= k
            acc_k += k
            
            if iteration_idx == num_iterations or remain_k <= self.folding_factor_log:

                # Break and jump to the final FRI round
                break

            # > FRI-commit and FRI-query

            (f_folded_code_len, f_folded_code_cm_root) = f_folded_code_cm

            rs = self.verify_one_fri_round(iteration_idx, k, 
                                           f_code_cm_root, f_folded_code_cm_root,
                                           f_code_len, y0, query_replies, r_vec, t, omega, coset, tr)
            z0, y0, z_vec, y_vec = rs
            if self.debug > 1:
                print(f"V> z0 = {z0}, y0 = {y0}, z_vec = {z_vec}, y_vec = {y_vec}")

            # > Aggregate sumchecks 

            rs = self.verify_sumcheck_merge(t, k, 
                                        new_sum_checked, 
                                        z0, y0, z_vec, y_vec, 
                                        remain_k, coset, tr)
            gamma, new_sum_checked = rs

            if self.debug > 1:
                print(f"V> new_sum_checked = {new_sum_checked}")

            # > Update loop variables for the next iteration
            f_code_cm_root = f_folded_code_cm_root
            f_code_len = f_folded_code_len
            sum_checked = new_sum_checked
            all_gamma_z_y_vec.append((acc_k, gamma, z0, y0, z_vec, y_vec, remain_k))
            omega = omega**(2**k)

            if self.debug > 0:
                print(f"V> ------- EXIT ITERATION {iteration_idx} -------")

        # > END of Iteration

        # > Final FRI round

        rs = self.verify_final_fri_round(iteration_idx, k, 
                                         final_poly_evals, f_code_len, 
                                         query_replies, r_vec, 
                                         t, omega, coset, tr)
        z_vec, y_vec = rs

        # Update variables 
        final_k = remain_k

        if self.debug > 0:
            print(f"V> total_k = {total_k}, all_r_k = {len(all_r_vec)}, final_k = {final_k}, remain_k = {remain_k}")

        # > Check the final polynomial

        final_mle = MLEPolynomial(final_poly_evals, final_k)

        if self.debug > 0:
            print(f"V> Verify final folding")
        
        for zi, yi in zip(z_vec, y_vec):
            zi_pow = compute_power_of_2_powers(zi * coset**(2**k), final_k)
            assert final_mle.evaluate(zi_pow) == yi, \
                f"final_mle.evaluate(zi_pow) = {final_mle.evaluate(zi_pow)}, yi = {yi}"

        if self.debug > 0:
            print(f"V> Verify final folding ... DONE")

        # > Check the final SUM!
        
        assert acc_k + final_k == total_k, \
            f"V> acc_k = {acc_k}, final_k = {final_k}, total_k = {total_k}"
        
        eq_mle = MLEPolynomial(MLEPolynomial.eqs_over_hypercube(us[acc_k:]), final_k)
        eq_mle = Scalar(eq_eval(all_r_vec, us[:acc_k])) * eq_mle
        for i, (acc_k_i, gamma_i, z0_i, y0_i, z_vec_i, y_vec_i, remain_k_i) in enumerate(all_gamma_z_y_vec):
            print(f"i={i}, acc_k_i = {acc_k_i}, remain_k_i = {remain_k_i}, total_k = {total_k}")
            assert acc_k_i + remain_k_i == total_k, \
                f"i={i}, acc_k_i = {acc_k_i}, remain_k_i = {remain_k_i}, total_k = {total_k}"
            print(f"len(z0_pow)={remain_k_i-final_k}")
            print(f"P> gamma_i = {gamma_i}")
            z0_pow = compute_power_of_2_powers(z0_i, remain_k_i)
            z0_mle = MLEPolynomial(MLEPolynomial.eqs_over_hypercube(z0_pow[-final_k:]), final_k)
            z0_mle = Scalar(gamma_i * eq_eval(all_r_vec[acc_k_i:], z0_pow[:-final_k])) * z0_mle
            print(f"P> z0_mle = {z0_mle}")
            eq_mle += z0_mle

            for j in range(t):
                zi = z_vec_i[j]
                print(f"P> zi = {zi}")
                zi_pow = compute_power_of_2_powers(zi * coset**(2**k), remain_k_i)
                print(f"P> zi_pow = {zi_pow}")
                zi_mle = MLEPolynomial(MLEPolynomial.eqs_over_hypercube(zi_pow[-final_k:]), final_k)
                zi_mle = Scalar(gamma_i**(j+2) * eq_eval(all_r_vec[acc_k_i:], zi_pow[:-final_k])) * zi_mle
                print(f"P> zi_mle = {zi_mle}")
                eq_mle += zi_mle        
        if self.debug > 1:
            print(f"V> final_mle = {final_mle}")
            print(f"V> eq_mle = {eq_mle}")
        final_eval = inner_product(final_mle.evals, eq_mle.evals, Fp.zero())

        assert final_eval == new_sum_checked, \
            f"final_eval = {final_eval}, sum_checked = {new_sum_checked}"

        return True


def test_pcs():

    pcs = WHIR_RS_PCS(MerkleTree, debug = 2)

    tr = MerlinTranscript(b"whir-rs-pcs")

    # # A simple instance f(x) = y
    evals = [Fp(1), Fp(3), Fp(2), Fp(1),
            Fp(2), Fp(-2), Fp(1), Fp(0),
            Fp(-1), Fp(2), Fp(3), Fp(1),
            Fp(3), Fp(1), Fp(-2), Fp(3),
            Fp(0), Fp(-1), Fp(-2), Fp(3),
            Fp(0), Fp(-1), Fp(-2), Fp(3),
            Fp(0), Fp(-1), Fp(-2), Fp(3),
            Fp(0), Fp(-1), Fp(-2), Fp(3),
            ]
    us = [Fp(2), Fp(-1), Fp(2), Fp(-2), Fp(3)]
    
    # evals = evals + evals
    # us = us + us

    eqs = MLEPolynomial.eqs_over_hypercube(us)
    print(f"eqs = {eqs}")
    print(f"len(eqs) = {len(eqs)}")

    y = inner_product(evals, eqs, Fp.zero())
    f_mle = MLEPolynomial(evals, len(us))
    assert f_mle.evaluate(us) == y
    print(f"f(x[]) = {y}")
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

if __name__ == "__main__":
    test_pcs()
