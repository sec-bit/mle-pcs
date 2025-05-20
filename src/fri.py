from merkle import MerkleTree, verify_decommitment
from merlin.merlin_transcript import MerlinTranscript
from utils import from_bytes, log_2, is_power_of_two
from unipoly2 import UniPolynomialWithFft
import sys

sys.path.append('finite-field')
sys.path.append('../src/ff')

from babybear import BabyBear, BabyBearExtElem

def ext_from_babybear(e):
    if isinstance(e, BabyBearExtElem):
        return e
    elif isinstance(e, BabyBear):
        return BabyBearExtElem([e, BabyBear.zero(), BabyBear.zero(), BabyBear.zero()])
    else:
        raise ValueError(f"Unsupported type: {type(e)}")

class FRI:
    security_level = 128

    @classmethod
    def commit(cls, evals, rate, domain, debug=False):
        if debug: print("evals:", evals)
        N = len(evals)
        assert is_power_of_two(N)
        degree_bound = N
        if debug: print("degree_bound:", degree_bound)
        UniPolynomialWithFft.set_field_type(BabyBear)
        coeffs = UniPolynomialWithFft.ifft(evals, log_2(N), domain[1] ** rate)
        if debug: print("coeffs:", coeffs)
        code = UniPolynomialWithFft.fft(coeffs + [0] * (N * rate - len(coeffs)), log_2(N * rate), domain[1])
        if debug: print("code:", code)
        assert len(code) == N * rate, f"code: {code}, degree_bound: {degree_bound}, rate: {rate}"
        
        return MerkleTree(code), code, coeffs

    @classmethod
    def prove(cls, code, code_tree, val, point, domain, rate, degree_bound, gen, transcript, one=1, debug=False):
        if debug: print("val:", val)
        assert len(domain) == degree_bound * rate, f"domain: {domain}, degree_bound: {degree_bound}, rate: {rate}"
        assert isinstance(transcript, MerlinTranscript), f"transcript: {transcript}"
        
        if type(one) is BabyBearExtElem:
            domain = [ext_from_babybear(d) for d in domain]
            quotient = [(BabyBearExtElem([code[i], BabyBear.zero(), BabyBear.zero(), BabyBear.zero()]) - val) / (domain[i] - point) for i in range(len(code))]
        else:
            quotient = [(code[i] - val) / (domain[i] - point) for i in range(len(code))]

        if debug:
            print('point:', point)
            print('value:', val)

        num_verifier_queries = cls.security_level // log_2(rate)
        if cls.security_level % log_2(rate) != 0:
            num_verifier_queries += 1

        proof = cls.prove_low_degree(code, code_tree, quotient, rate, degree_bound, gen, num_verifier_queries, transcript, one, debug)

        return {
            'proof': proof,
            'degree_bound': degree_bound,
        }

    @classmethod
    def verify(cls, degree_bound, rate, proof, point, value, domain, gen, transcript, one=1, debug=False):

        assert degree_bound >= proof['degree_bound']
        degree_bound = proof['degree_bound']

        assert isinstance(transcript, MerlinTranscript), f"transcript: {transcript}"

        if debug:
            print('point:', point)
            print('value:', value)

        num_verifier_queries = cls.security_level // log_2(rate)
        if cls.security_level % log_2(rate) != 0:
            num_verifier_queries += 1
        
        cls.verify_low_degree(point, value, degree_bound, rate, proof['proof'], gen, num_verifier_queries, transcript, one, debug)

    @staticmethod
    def prove_low_degree(code, code_tree, evals, rate, degree_bound, gen, num_verifier_queries, transcript, one=1, debug=False):
        assert is_power_of_two(degree_bound)

        lambda_ = BabyBearExtElem([BabyBear(from_bytes(transcript.challenge_bytes(b"lambda", 4))) for _ in range(4)])
        evals = [(BabyBearExtElem.one() + lambda_ * gen ** i) * evals[i] for i in range(len(evals))]

        alpha = BabyBearExtElem([BabyBear(from_bytes(transcript.challenge_bytes(b"alpha", 4))) for _ in range(4)])

        trees = []
        tree_evals = []
        for _ in range(log_2(degree_bound)):
            if debug: print("evals:", evals)
            if debug: print("alpha:", alpha)
            if debug: print("generator:", gen)
            evals = FRI.fold(evals, alpha, gen, BabyBearExtElem.one())
            tree = MerkleTree(evals)
            trees.append(tree)
            tree_evals.append(evals)

            transcript.append_message(b"oracle", tree.root.encode('ascii'))
            alpha = BabyBearExtElem([BabyBear(from_bytes(transcript.challenge_bytes(b"alpha", 4))) for _ in range(4)])

            gen *= gen

        if debug:
            assert len(evals) == rate, f"evals: {evals}, rate: {rate}"
            for i in range(len(evals)):
                if i != 0:
                    assert evals[i] == evals[0], f"evals: {evals}"

        # query phase
        query_paths, merkle_paths = FRI.query_phase(transcript, code_tree, code, trees, tree_evals, degree_bound * rate, num_verifier_queries, one, debug)

        return {
            'query_paths': query_paths,
            'merkle_paths': merkle_paths,
            'first_oracle': code_tree.root,
            'intermediate_oracles': [tree.root for tree in trees],
            'degree_bound': degree_bound,
            'final_value': evals[0],
        }

    # f(x) = f0(x^2) + x * f1(x^2)
    # and half degree interpolation is
    # f'(x^2) = f0(x^2) + alpha * f1(x^2), and it can be achieved by just adding up two adjustent (adjustment?)
    # coefficients in the monomial form
    # if we would want to try to get the same result, one can observe that
    # f0(x^2) = (f(x) + f(-x)) / 2
    # f1(x^2) = (f(x) - f(-x)) / 2x
    @staticmethod
    def fold(evals, alpha, g, one=1, debug=False):
        assert len(evals) % 2 == 0
        inv_two = BabyBear.one() / (BabyBear.one() + BabyBear.one())

        evals = [ext_from_babybear(e) for e in evals]

        half = len(evals) // 2
        f0_evals = [(evals[i] + evals[half + i]) * inv_two for i in range(half)]
        f1_evals = [(evals[i] - evals[half + i]) * inv_two * ext_from_babybear(BabyBear.one() / (g ** i)) for i in range(half)]

        if debug:
            x = BabyBearExtElem.random()
            UniPolynomialWithFft.set_field_type(BabyBearExtElem)
            f_x = UniPolynomialWithFft.evaluate_from_evals(evals, x, [ext_from_babybear(g ** i) for i in range(len(evals))])
            f0_x = UniPolynomialWithFft.evaluate_from_evals(f0_evals, x ** 2, [ext_from_babybear((g ** 2) ** i) for i in range(len(f0_evals))])
            f1_x = UniPolynomialWithFft.evaluate_from_evals(f1_evals, x ** 2, [ext_from_babybear((g ** 2) ** i) for i in range(len(f1_evals))])
            assert f_x == f0_x + x * f1_x, f"failed to fold, f_x: {f_x}, f0_x: {f0_x}, f1_x: {f1_x}, alpha: {alpha}"

        return [x + alpha * y for x, y in zip(f0_evals, f1_evals)]


    @staticmethod
    def verify_low_degree(point, value, degree_bound, rate, proof, gen, num_verifier_queries, transcript, one=1, debug=False):
        log_degree_bound = log_2(degree_bound)
        log_evals = log_2(degree_bound * rate)
        T = [[(gen**(2 ** j)) ** i for i in range(2 ** (log_evals - j - 1))] for j in range(0, log_evals)]
        if debug: print("T:", T)
        FRI.verify_queries(proof, log_degree_bound, degree_bound * rate, num_verifier_queries, T, point, value, transcript, one, debug)

    @staticmethod
    def query_phase(transcript: MerlinTranscript, first_tree: MerkleTree, first_oracle, trees: list, oracles: list, num_vars, num_verifier_queries, one=1, debug=False):
        queries = [from_bytes(transcript.challenge_bytes(b"queries", 4)) % num_vars for _ in range(num_verifier_queries)]
        if debug: print("queries:", queries)

        query_paths = []
        # query paths
        for q in queries:
            num_vars_copy = num_vars
            cur_path = []
            indices = []
            x0 = int(q)
            x1 = int(q - num_vars_copy / 2 if q >= num_vars_copy / 2 else q + num_vars_copy / 2)
            if x1 < x0:
                x0, x1 = x1, x0
            
            cur_path.append((first_oracle[x0], first_oracle[x1]))
            if debug: print("x0:", x0, "x1:", x1, "num_vars:", num_vars_copy, "q:", q)
            if debug: print("first_oracle:", first_oracle)
            indices.append(x0)
            q = x0
            num_vars_copy >>= 1

            for oracle in oracles:
                x0 = int(q)
                x1 = int(q - num_vars_copy / 2 if q >= num_vars_copy / 2 else q + num_vars_copy / 2)
                if x1 < x0:
                    x0, x1 = x1, x0
                
                cur_path.append((oracle[x0], oracle[x1]))
                if debug: print("x0:", x0, "x1:", x1, "num_vars:", num_vars_copy, "q:", q)
                if debug: print("oracle:", oracle)
                indices.append(x0)
                q = x0
                num_vars_copy >>= 1
            
            query_paths.append((cur_path, indices))

        # merkle paths
        merkle_paths = []
        for _, indices in query_paths:
            cur_query_paths = []
            for i, idx in enumerate(indices):
                if i == 0:
                    cur_query_paths.append(first_tree.get_authentication_path(idx))
                    if debug: print("mp:", cur_query_paths[-1])
                    if debug: print("commit:", first_tree.root)
                    if debug: print("idx:", idx)
                else:
                    cur_tree = trees[i - 1]
                    assert isinstance(cur_tree, MerkleTree)
                    cur_query_paths.append(cur_tree.get_authentication_path(idx))
                    if debug: print("mp:", cur_query_paths[-1])
                    if debug: print("commit:", first_tree.root)
                    if debug: print("idx:", idx)
            merkle_paths.append(cur_query_paths)

        return query_paths, merkle_paths
    
    @staticmethod
    def verify_queries(proof, k, num_vars, num_verifier_queries, T, point, value, transcript, one=1, debug=False):

        lambda_ = BabyBearExtElem([BabyBear(from_bytes(transcript.challenge_bytes(b"lambda", 4))) for _ in range(4)])

        alpha = BabyBearExtElem([BabyBear(from_bytes(transcript.challenge_bytes(b"alpha", 4))) for _ in range(4)])

        point = ext_from_babybear(point)

        fold_challenges = [alpha]
        for i in range(k):
            transcript.append_message(bytes(f'oracle', 'ascii'), bytes(proof['intermediate_oracles'][i], 'ascii'))
            fold_challenges.append(BabyBearExtElem([BabyBear(from_bytes(transcript.challenge_bytes(b"alpha", 4))) for _ in range(4)]))

        queries = [from_bytes(transcript.challenge_bytes(b"queries", 4)) % num_vars for _ in range(num_verifier_queries)]
        # query loop
        for q, (cur_path, _), mps in zip(queries, proof['query_paths'], proof['merkle_paths']):
            if debug: print("cur_path:", cur_path)
            num_vars_copy = num_vars
            f_code_folded = None
            # fold loop
            for i, mp in enumerate(mps):
                x0 = int(q)
                x1 = int(q - num_vars_copy / 2 if q >= num_vars_copy / 2 else q + num_vars_copy / 2)
                if x1 < x0:
                    x0, x1 = x1, x0
                    
                code_left, code_right = cur_path[i][0], cur_path[i][1]
                decheck = code_left

                if debug: print("x0:", x0)
                if debug: print("x1:", x1)

                table = T[i]
                table = [BabyBearExtElem([t, BabyBear.zero(), BabyBear.zero(), BabyBear.zero()]) for t in table]
                if debug: print("table:", table)
                if i != len(mps) - 1:
                    if i == 0:
                        if type(value) is BabyBearExtElem:
                            code_left = BabyBearExtElem([code_left, BabyBear.zero(), BabyBear.zero(), BabyBear.zero()])
                            code_right = BabyBearExtElem([code_right, BabyBear.zero(), BabyBear.zero(), BabyBear.zero()])
                        code_left = (BabyBearExtElem.one() + lambda_ * table[x0]) * (code_left - value) / (table[x0] - point)
                        code_right = (BabyBearExtElem.one() - lambda_ * table[x0]) * (code_right - value) / (-table[x0] - point)
                    f_code_folded = cur_path[i + 1][0 if x0 < num_vars_copy / 4 else 1]
                    alpha = fold_challenges[i]
                    two = one + one
                    two = ext_from_babybear(two)
                    left = (code_left + code_right)/two
                    right = alpha * (code_left - code_right)/(two*table[x0])
                    if not isinstance(left, BabyBearExtElem):
                        left = BabyBearExtElem([left, BabyBear.zero(), BabyBear.zero(), BabyBear.zero()])
                    if not isinstance(right, BabyBearExtElem):
                        right = BabyBearExtElem([right, BabyBear.zero(), BabyBear.zero(), BabyBear.zero()])
                    if debug: assert x0 < len(table), f"x0: {x0}, table: {table}"
                    if debug: print("f_code_folded:", f_code_folded)
                    if debug: print("expected:", left + right)
                    if debug: print("code_left:", code_left)
                    if debug: print("code_right:", code_right)
                    if debug: print("alpha:", alpha)
                    assert f_code_folded == left + right, f"failed to check fri, i: {i}, x0: {x0}, x1: {x1}, code_left: {code_left}, code_right: {code_right}, alpha: {alpha}, table: {table}"
                else:
                    if f_code_folded is not None:
                        assert proof["final_value"] == f_code_folded, f"failed to check fri, i: {i}, x0: {x0}, x1: {x1}, code_left: {code_left}, code_right: {code_right}, alpha: {alpha}, table: {table}, final_value: {proof['final_value']}, f_code_folded: {f_code_folded}"

                if i == 0:
                    assert verify_decommitment(x0, decheck, mp, proof['first_oracle']), "failed to check decommitment at first level"
                else:
                    assert verify_decommitment(x0, decheck, mp, proof['intermediate_oracles'][i - 1]), "failed to check decommitment at level " + str(i)

                num_vars_copy >>= 1
                q = x0

    @staticmethod
    def rs_encode_single(m, alpha, c, zero=0):
        k0 = len(m)
        code = [None] * (k0 * c)
        for i in range(k0 * c):
            # Compute f_m(alpha[i])
            code[i] = sum([m[j] * (alpha[i] ** j) for j in range(k0)], zero)
        return code

