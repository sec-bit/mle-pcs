#!/usr/bin/env python3

# WARNING: This implementation may contain bugs and has not undergone auditing. 
# It is intended for educational and research purposes only. 
# DO NOT use it in a production environment.

from utils import is_power_of_two, log_2, next_power_of_two, bit_reverse, inner_product

# Implementation of Whir (RS encoding) PCS [ACFY24]
#
# [ACFY24] WHIR: Reed-Solomon Proximity Testing with Super-Fast Verification
#
#  Author: Gal Arnon, Alessandro Chiesa, Giacomo Fenzi, Eylon Yogev
#  URL: https://eprint.iacr.org/2024/1586

from unipoly2 import UniPolynomial, UniPolynomialWithFft, bit_reverse_permutation
from mle2 import MLEPolynomial
from merkle import MerkleTree
from merlin.merlin_transcript import MerlinTranscript
from curve import Fr as BN254_Fr

from basefold_rs_pcs import Commitment, rs_encode

Fp = BN254_Fr

# TODO:
#
#  - [ ] Make security parameters configurable
#  - [ ] Add batching proving/verifying
#  - [ ] Support small fields

def compute_powers(alpha: Fp, n: int) -> list[Fp]:
        return [alpha**i for i in range(n)]

def compute_power_of_2_powers(alpha: Fp, n: int) -> list[Fp]:
        return [alpha**(2**i) for i in range(n)]

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
        
        if debug > 0:
            print("P> show code folding")
            for i in range(len(code)//2):
                left = code[2*i]
                right = code[2*i+1]
                print(f"P> 📒: {left} + {right} => {code_folded[i]}, r={r_vec[round_idx]},w={twiddles[i]},coset={coseti}")
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
    if debug > 0: print(f"P> start_idx = {start_idx}, size = {size}")
    if debug > 0: print(f"P> twiddles = {twiddles}")
    coset_round = coset
    twiddles_start_idx = start_idx // 2
    for round_idx in range(len(r_vec)):
        if debug > 0: print(f"P> {round_idx}-th round, twiddles_start_idx = {twiddles_start_idx}")
        code_chunk_folded = [(code_chunk[2*i] + code_chunk[2*i+1]) / 2 
                        + r_vec[round_idx] * (code_chunk[2*i] - code_chunk[2*i+1]) / (2 * coset_round * twiddles[twiddles_start_idx+i]) 
                        for i in range(len(code_chunk)//2)]

        if debug > 1:
            print("P> show code chunk folding")
            for i in range(len(code_chunk)//2):
                left = code_chunk[2*i]
                right = code_chunk[2*i+1]
                print(f"P> 📒: {left} + {right} => {code_chunk_folded[i]}, r={r_vec[round_idx]},w={twiddles[twiddles_start_idx+i]},coset={coset_round}")

        coset_round *= coset_round
        code_chunk = code_chunk_folded
        twiddles_start_idx = twiddles_start_idx // 2
    return code_chunk_folded

def eq_sum(eqs: list[list[Fp]], gamma: Fp) -> list[Fp]:
    n = len(eqs[0])
    new_eq = [Fp(0)] * n
    for i, eq in enumerate(eqs):
        assert len(eq) == n, f"len(eq) = {len(eq)}, n = {n}"
        for j in range(n):
            new_eq[j] += eq[j] * gamma**i

    return new_eq

class WHIR_RS_PCS:

    # WARNING: the following parameters are not secure. They are only for demonstration,
    #  NOT for production. 
    # TODO: change to configurable parameters
    blowup_factor = 2 
    folding_factor = 2     # folding parameters `k0, k1, ..., k_{M-1}` in [Sec 5, ACFY24]
    coset_gen = Fp.multiplicative_generator()
    max_queries_try = 1000  # NOTE: change it to a practical number
    num_queries = 1         # repetition parameters `t1, t2, ..., t_M` in [Sec 5, ACFY24]

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

        f_code = rs_encode(f_coeffs, self.coset_gen, self.blowup_factor)
        f_tree = MerkleTree(f_code)

        assert len(f_code) == 2**f_mle.num_var * self.blowup_factor, \
            f"len(evals)={len(evals)}, f_mle.num_var={f_mle.num_var}, blowup_factor={self.blowup_factor}"
        cm = Commitment(f_tree)
        return cm

    def do_one_sumcheck_round(self, round_idx: int, k: int, f0, eq0, sum_checked, tr: MerlinTranscript):
        """
        Do one 2^k-step sumcheck round for the `round_idx`-th round.
        """
        assert len(f0) == len(eq0), f"len(f0) = {len(f0)}, len(eq0) = {len(eq0)}"
        assert len(f0) >= 2**k, f"len(f0) = {len(f0)}, k = {k}"
        f = f0.copy()
        eq = eq0.copy()
        half = len(f0) >> 1
        r_vec = []
        sumcheck_h_vec = []

        if self.debug > 0:
            print(f"P> -- BEGIN Sumcheck Round-{round_idx} --")

        for i in range(k):
            f_even = f[::2]
            f_odd = f[1::2]
            eq_even = eq[::2]
            eq_odd = eq[1::2]
            if self.debug > 1:
                 print(f"P> f_even = {f_even}, f_odd = {f_odd}, eq_even = {eq_even}, eq_odd = {eq_odd}")
            # construct h(X)
            h_eval_at_0 = sum([f_even[j] * eq_even[j] for j in range(half)], Fp.zero())
            h_eval_at_1 = sum([f_odd[j] * eq_odd[j] for j in range(half)], Fp.zero())
            h_eval_at_2 = sum([ (2 * f_odd[j] - f_even[j]) * (2 * eq_odd[j] - eq_even[j]) for j in range(half)])
            h = [h_eval_at_0, h_eval_at_1, h_eval_at_2]
            sumcheck_h_vec.append(h)

            tr.absorb(b"h(X)", h)

            # check sum
            assert h_eval_at_0 + h_eval_at_1 == sum_checked, \
                f"h_eval_at_0 + h_eval_at_1 = {h_eval_at_0 + h_eval_at_1}, sum_checked = {sum_checked}"
            
            # Receive a random number from the verifier
            r = tr.squeeze(Fp, b"r", 4)
            if self.debug > 0:
                print(f"P> r[{i}] = {r}")
            r_vec.append(r)
            
            # fold f
            f = [(Fp(1) - r) * f_even[i] + r * f_odd[i] for i in range(half)]
            eq = [(Fp(1) - r) * eq_even[i] + r * eq_odd[i] for i in range(half)]

            # update sumcheck for the next round
            sum_checked = UniPolynomial.evaluate_from_evals(h, 
                        r, [Fp.zero(), Fp.one(), Fp(2)])
            half >>= 1

        ## End of the big loop for `i`

        # Check the k-round sumcheck inside one whir-round 
        if self.debug > 1:
            print(f"P> Check k-round sumcheck")
            eval = Fp.zero()
            for i in range(len(f0) // (2**k)):
                eval += f[i] * eq[i]
            assert sum_checked == eval, \
                f"sum_checked = {sum_checked}, eval = {eval}"
            print(f"P> final_sum = Σ_b f(b) * eq(b,us) checked = {eval}")
            print(f"P> Check k-round sumcheck passed")
        if self.debug > 0:
            print(f"P> -- END Sumcheck Round-{round_idx} --")
    
        return f, eq, sum_checked, r_vec
    
    def do_one_fri_round(self, 
                         round_idx: int, 
                         k: int, 
                         f: list[Fp],
                         f_code: list[Fp], 
                         r_vec: list[Fp], 
                         t, 
                         omega: Fp,
                         coset: Fp, 
                         twiddles: list[Fp],
                         tr: MerlinTranscript):
        """
        """

        # TODO: 
        #  - [ ] Use `fold_code_chunk` to speed up the code folding, sinace we only need to 
        #        fold the code chunks for the shift queries.

        if self.debug > 0:
            print(f"P> -- Begin FRI round {round_idx} --")

        f_folded_code = fold_code(f_code, r_vec, coset, twiddles, debug=self.debug)
        f_folded_code_cm = MerkleTree(f_folded_code)

        if self.debug > 0:
            print(f"P> check code folding ")
            f_mle = MLEPolynomial(f, log_2(len(f)))
            f_coeffs = MLEPolynomial.compute_coeffs_from_evals(f)
            f_uni = UniPolynomialWithFft.interpolate(f_coeffs, len(f))
            evals = rs_encode(f_coeffs, coset**4, self.blowup_factor)
            assert evals == f_folded_code, f"evals={evals}, f1_code={f_folded_code}"

            D = compute_powers(omega**(2**k), len(f_folded_code))
            D_rbo = bit_reverse_permutation(D)
            for i in range(len(D_rbo)):
                w = D_rbo[i]
                w_pow = compute_power_of_2_powers(w * coset**4, f_mle.num_var)
                print(f"P> w = {w}, w_pow = {w_pow}")
                assert f_folded_code[i] == f_mle.evaluate(w_pow), \
                    f"f_folded_code[{i}] = {f_folded_code[i]}, f_mle.evaluate(w_pow) = {f_mle.evaluate(w_pow)}"

            print(f"P> check code folding passed")

        tr.absorb(b"f_folded_code_cm", f_folded_code_cm.root)

        # > Sample-phase: out-of-domain query and reply.

        z0 = tr.squeeze(Fp, b"z0", 4)
        z0_pow = compute_power_of_2_powers(z0, f_mle.num_var)
        y0 = f_mle.evaluate(z0_pow)

        tr.absorb(b"y0", y0)
        if self.debug > 0:
            print(f"P> y0 = {y0}")

        # > Query-phase: in-domain queries to ensure the code is folded correctly.

        z_idx_vec = []
        for i in range(self.max_queries_try):
            z_idx = tr.squeeze(int, b"zi", 4) % len(f_folded_code)
            if z_idx not in z_idx_vec:
                z_idx_vec.append(z_idx)
            else:
                continue
            if len(z_idx_vec) >= t:
                break
        assert len(z_idx_vec) == t, f"len(z_idx_vec) = {len(z_idx_vec)}, t = {t}"

        new_omega = omega**(2**k)

        z_vec = []
        y_vec = []
        for i in range(t):
            z_vec.append(new_omega** bit_reverse(z_idx_vec[i], log_2(len(f_folded_code))))
            y_vec.append(f_folded_code[z_idx_vec[i]])
        z_idx_vec, z_vec, y_vec
        
        # double check `y_vec`, every `yi` in which should be equal to `f1(zi)`
        if self.debug > 1:
            for i in range(t):
                z = z_vec[i]
                z_pow = compute_power_of_2_powers(z * coset**4, f_mle.num_var)
                print(f"P> z_pow = {z_pow}")
                assert y_vec[i] == f_mle.evaluate(z_pow), \
                    f"y_vec[{i}] = {y_vec[i]}, f_mle.evaluate({z_pow}) = {f_mle.evaluate(z_pow)}" 

        tr.absorb(b"zi", z_vec)

        # Collect leaves of the code that are used to construct `y0=f(zi)`
        query_replies = []
        for i in range(t):
            idx = z_idx_vec[i]
            start_idx = idx*2**k
            end_idx = (idx+1)*2**k
            query_reply = f_code[start_idx: end_idx]
            query_replies.append(query_reply)

            if self.debug > 0:
                print(f"P> check query reply {i} = {query_reply}")
                # for round_idx in range(k):
                print(f"P> query_reply = {query_reply}, r_vec = {r_vec}")
                start_idx = idx*2**k
                end_idx = (idx+1)*2**k
                print(f"P> start_idx = {start_idx}, end_idx = {end_idx}")
                query_reply_folded = fold_code_chunk(query_reply, r_vec, coset, start_idx, 2**k, twiddles)
                print(f"P> query_reply_folded = {query_reply_folded}")
                assert len(query_reply_folded) == int(1), f"len(code_folded) = {len(query_reply_folded)}, query_reply = {query_reply}, r_vec = {r_vec}, coseti = {coset}"
                assert query_reply_folded[0] == y_vec[i], f"code_folded[0] = {query_reply_folded[0]}, y_vec[{i}] = {y_vec[i]}"
                print(f"P> check query reply passed")

        tr.absorb(b"query_replies", query_replies)

        if self.debug > 0:
            print(f"P> -- END FRI round {round_idx} --")

        return f_folded_code, z0, y0, z_vec, y_vec

    def do_final_fri_round(self, 
                           round_idx: int, 
                           k: int, 
                           f: list[Fp],
                           f_folded: list[Fp],
                           f_code: list[Fp], 
                           r_vec: list[Fp], 
                           t, 
                           omega: Fp,
                           coset: Fp, 
                           twiddles: list[Fp],
                           tr: MerlinTranscript):
        
        if self.debug > 0:
            print(f"P> -- BEGIN Final FRI round {round_idx} --")
        assert len(f_folded) * 2**k
        assert len(f_folded) == int(1), f"len(f) = {len(f)}, not a constant polynomial"
        
        f_folded_mle = MLEPolynomial(f_folded, log_2(len(f_folded)))
        f_folded_code = fold_code(f_code, r_vec, coset, twiddles, debug=self.debug)

        if self.debug > 0:
            print(f"P> f_folded_code = {f_folded_code}")

        if self.debug > 1:
            print(f"P> Check code folding")
            f_coeffs = MLEPolynomial.compute_coeffs_from_evals(f_folded)
            f_uni = UniPolynomialWithFft.interpolate(f_coeffs, len(f))
            f_evals = rs_encode(f_coeffs, coset**4, self.blowup_factor)
            assert f_evals == f_folded_code, f"f_evals={f_evals}, f_folded_code={f_folded_code}"

            D = compute_powers(omega**(2**k), len(f_folded_code))
            D_rbo = bit_reverse_permutation(D)
            for i in range(len(D_rbo)):
                w = D_rbo[i]
                w_pow = compute_power_of_2_powers(w * coset**4, f_folded_mle.num_var)
                print(f"P> w = {w}, w_pow = {w_pow}")
                assert f_folded_code[i] == f_folded_mle.evaluate(w_pow), \
                    f"f_folded_code[{i}] = {f_folded_code[i]}, f_folded_mle.evaluate(w_pow) = {f_folded_mle.evaluate(w_pow)}"
            for i in range(len(f_folded_code)):
                assert f_folded[0] == f_folded_code[i], \
                    f"f_folded[0] = {f_folded[0]}, f_folded_code[{i}] = {f_folded_code[i]}"
            print(f"P> check code folding passed")

        tr.absorb(b"final_f_code", f_folded)

        # > No more sample-phase, just query-phase.

        # > Query-phase: in-domain queries to ensure the code is folded correctly.

        z_idx_vec = []
        for i in range(self.max_queries_try):
            z_idx = tr.squeeze(int, b"zi", 4) % len(f_folded_code)
            if z_idx not in z_idx_vec:
                z_idx_vec.append(z_idx)
            else:
                continue
            if len(z_idx_vec) >= t:
                break
        assert len(z_idx_vec) == t, f"len(z_idx_vec) = {len(z_idx_vec)}, t = {t}"

        new_omega = omega**(2**k)

        z_vec = []
        y_vec = []
        for i in range(t):
            z_vec.append(new_omega** bit_reverse(z_idx_vec[i], log_2(len(f_folded_code))))
            y_vec.append(f_folded_code[z_idx_vec[i]])
        
        # double check `y_vec`, every `yi` in which should be equal to `f1(zi)`
        if self.debug > 1:
            for i in range(t):
                z = z_vec[i]
                z_pow = compute_power_of_2_powers(z * coset**4, f_folded_mle.num_var)
                print(f"P> z_pow = {z_pow}")
                assert y_vec[i] == f_folded_mle.evaluate(z_pow), \
                    f"y_vec[{i}] = {y_vec[i]}, f_mle.evaluate({z_pow}) = {f_folded_mle.evaluate(z_pow)}" 

        tr.absorb(b"zi", z_vec)

        # Collect leaves of the code that are used to construct `y0=f(zi)`
        query_replies = []
        for i in range(t):
            idx = z_idx_vec[i]
            start_idx = idx*2**k
            end_idx = (idx+1)*2**k
            query_reply = f_code[start_idx: end_idx]
            query_replies.append(query_reply)

            if self.debug > 1:
                print(f"P> check query reply {i} = {query_reply}")
                # for round_idx in range(k):
                print(f"P> query_reply = {query_reply}, r_vec = {r_vec}")
                start_idx = idx*2**k
                end_idx = (idx+1)*2**k
                print(f"P> start_idx = {start_idx}, end_idx = {end_idx}")
                query_reply_folded = fold_code_chunk(query_reply, r_vec, coset, start_idx, 2**k, twiddles)
                print(f"P> query_reply_folded = {query_reply_folded}")
                assert len(query_reply_folded) == int(1), f"len(code_folded) = {len(query_reply_folded)}, query_reply = {query_reply}, r_vec = {r_vec}, coseti = {coset}"
                assert query_reply_folded[0] == y_vec[i], f"code_folded[0] = {query_reply_folded[0]}, y_vec[{i}] = {y_vec[i]}"
                print(f"P> check query reply passed")

        tr.absorb(b"query_replies", query_replies)

        if self.debug > 0:
            print(f"P> -- END FRI round {round_idx} --")

        return f_folded_code, z_vec

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

        assert f_mle.num_var == len(us), f"f_mle.num_var={f_mle.num_var}, len(us)={len(us)}"

        k = self.folding_factor
        total_k = f_mle.num_var

        # Evaluate f_mle at the point us
        v = f_mle.evaluate(us)
        f0 = f_mle.evals.copy()
        n = 2**total_k

        if self.debug > 0:
            print(f"P> f_len={len(f0)}, k={k}, c_len ={len(f0)*self.blowup_factor}")

        eq = MLEPolynomial.eqs_over_hypercube(us)
        eq_mle = MLEPolynomial(eq, total_k)

        # > Preparation
        
        f0_code_len = len(f0) * self.blowup_factor
        f0_coeffs = MLEPolynomial.compute_coeffs_from_evals(f0)

        # NOTE: the array of twiddles are bit-reversed, such that it can be reused for all rounds.
        twiddles = UniPolynomialWithFft.precompute_twiddles_for_fft(f0_code_len, is_bit_reversed=True)

        f0_code = rs_encode(f0_coeffs, self.coset_gen, self.blowup_factor)

        f0_len = len(f0)
        f0_code_len = len(f0_code)
        omega = Fp.nth_root_of_unity(f0_code_len)
        D0 = compute_powers(omega, len(f0_code))
        D0_rbo = bit_reverse_permutation(D0)
        coset0 = self.coset_gen

        # Update transcript with the context
        tr.absorb(b"f_code_merkle_root", f_cm.cm)
        tr.absorb(b"point", us)
        tr.absorb(b"value", v)

        if self.debug > 1:
            print(f"P> check f0_code")
            f_orig_evals = bit_reverse_permutation(f0_code)
            f_orig_coeffs = UniPolynomialWithFft.ifft_coset(f_orig_evals, self.coset_gen, total_k + log_2(self.blowup_factor))
            assert f_orig_coeffs[:len(f0_coeffs)] == f0_coeffs, \
                f"f_orig_coeffs != f_coeffs, {f_orig_coeffs} != {f0_coeffs}"
            print(f"P> check f0_code passed")

        if self.debug > 1:
            print(f"check rs_encode")
            f_uni = UniPolynomial(f0_coeffs)
            for i in range(len(f0_code)):
                w = D0_rbo[i]
                assert f_uni.evaluate(w * coset0) == f0_code[i], \
                    f"f_uni.evaluate(D_rbo[{i}]) = {f_uni.evaluate(w)}, f0_code[{i}] = {f0_code[i]}"
                w_pow = compute_power_of_2_powers(w * coset0, f_mle.num_var)
                assert f_mle.evaluate(w_pow) == f0_code[i], \
                    f"f_mle.evaluate(D_rbo[{i}]) = {f_mle.evaluate(w_pow)}, f0_code[{i}] = {f0_code[i]}"
            print(f"check rs_encode passed")

        f = f0.copy()
        f_code = f0_code.copy()
        eq = MLEPolynomial.eqs_over_hypercube(us)
        # eq_mle = MLEPolynomial(eq, log_2(f0_len))
        coset = coset0
        t = self.num_queries
        all_r_vec = []

        # > Initial Sumcheck

        f1, eq, sum_checked, r_vec = self.do_one_sumcheck_round(0, k, f0, eq, v, tr)
        all_r_vec += r_vec

        if self.debug > 0:
            print(f"P> new_sum_checked = {sum_checked}")
            print(f"P> f_folded = {f1}")
            print(f"P> eq_folded = {eq}")
            print(f"P> r_vec = {r_vec}")
        
        # > Fold code

        f1_code, z0, y0, z_vec, y_vec = self.do_one_fri_round(0, k, f1, f0_code, r_vec, t, omega, coset, twiddles, tr)
        f1_mle = MLEPolynomial(f1, log_2(len(f1)))

        # > Aggregating sumchecks 

        gamma = tr.squeeze(Fp, b"gamma", 4)
        if self.debug > 0:
            print(f"P> gamma = {gamma}")

        new_sum_checked = sum_checked + gamma * y0
        z0_pow = compute_power_of_2_powers(z0, total_k - k)
        eqz0 = MLEPolynomial.eqs_over_hypercube(z0_pow)

        if self.debug > 0:
            print(f"P> new_sum_checked(1) = {new_sum_checked}")
            print(f"P> gamma = {gamma}")
            print(f"P> z0_pow = {z0_pow}")
            print(f"P> eqz0 = {eqz0}")

        eqz_list = []
        for i, zi, yi in zip(range(t), z_vec, y_vec):
            # NOTE: `zi` is actually in the coset domain
            zi_pow = compute_power_of_2_powers(zi * (coset**4), total_k - k)
            eqzi = MLEPolynomial.eqs_over_hypercube(zi_pow)
            new_sum_checked += gamma**(i+2) * yi
            eqz_list.append(eqzi)

        if self.debug > 0:
            print(f"P> new_sum_checked(2) = {new_sum_checked}")
            print(f"P> eqz_list = {eqz_list}")
        # new_sum_checked = sum_checked + gamma * y0 + gamma**2 * y1
        new_eq = eq_sum([eq, eqz0]+eqz_list, gamma)

        if self.debug > 0:
            print(f"P> check new_eq and new_sum")
            eval = sum([f1[i] * new_eq[i] for i in range(len(f1))])
            print(f"P> eval = {eval}, new_sum_checked(3) = {new_sum_checked}")
            assert eval == new_sum_checked, \
                f"f1(z) = {eval}, new_sum_checked = {new_sum_checked}"
            print(f"P> check new_eq and new_sum passed")

        # > Second sumcheck

        f2, eq, sum_checked, r_vec = self.do_one_sumcheck_round(1, k, f1, new_eq, new_sum_checked, tr)
        all_r_vec += r_vec

        f2_code, z_vec = self.do_final_fri_round(1, k, f1, f2, f1_code, r_vec, t, omega**(2**k), coset**(2**k), twiddles, tr)

        if self.debug > 0:
            print(f"f2_code = {f2_code}")
        return v, {}
    
def test_pcs():

    pcs = WHIR_RS_PCS(MerkleTree, debug = 2)

    tr = MerlinTranscript(b"basefold-rs-pcs")

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

    # assert v == y
    # print("🕐 Verifying proof ....")
    # checked = pcs.verify_eval(f_cm, us, v, arg, tr.fork(b"basefold_rs_pcs"))
    # assert checked
    # print("✅ Proof verified")

if __name__ == "__main__":
    test_pcs()