from sage.all import *
import sys

sys.path.append("src")
sys.path.append("../src")

from utils import log_2
from merkle import MerkleTree, verify_decommitment
from merlin.merlin_transcript import MerlinTranscript

F31 = GF(31)
R = PolynomialRing(F31, ['X'])
R.inject_variables()
X, = R.gens()

C31 = R.extension(X ** 2 + 1, 'i')
C31.inject_variables()
I, = C31.gens()

# g = 10 + 5 * I # not a generator
# g = 29 + 11 * I # neither

def test_generator(x, y):
    g = x + y * I
    g_30 = g**30
    for i in range(1, 32):
        if g_30**i == 1:
            return False
    return True

g = 0

for x in range(31):
    for y in range(31):
        if test_generator(x, y):
            g = x + y * I
            break

g_30 = g**30

assert g_30**32 == 1

def sq(D):
    rs = []
    for t in D[:len(D)//2]:
        # x' == 2 * x^2 - 1
        rs += [t**2]
    return rs

G5 = [g_30**k for k in range(32)]
G = [G5]
tmp = G[-1]
for i in range(5):
    tmp = sq(tmp)
    G = [tmp] + G

standard_position_cosets = [[G[i + 1][1] * p for p in G[i]] for i in range(4)]

def group_inv(g1):
    x1, y1 = g1
    return x1 - y1 * I

def group_mul(g1, g2):
    x1, y1 = g1
    x2, y2 = g2
    return (x1 * x2 - y1 * y2) + (x1 * y2 + y1 * x2) * I

def pi(t):
    # x^2 - y^2 == 2 * x^2 - 1 (x^2 + y^2 = 1)
    return C31(2 * t**2 - 1)

def pie_group(D):
    D_new = []
    for x in D:
        x_new = pi(x)
        if x_new not in D_new:
            D_new.append(x_new)

    # Check that the new domain is exactly half size of the old domain
    assert len(D_new) * 2 == len(D), "len(D_new) * 2 != len(D), {} * 2 != {}, D_new={}, D={}".format(len(D_new), len(D), D_new, D)
    
    return D_new

def v_n(x, log_n):
    for _ in range(log_n - 1):
        x = 2 * x**2 - 1
    return x

def zeroifier(at, shift, log_n):
    return v_n(at, log_n) - v_n(shift, log_n)

def v_n_prod(x, log_n):
    output = x
    for _ in range(log_n - 2):
        x = 2 * x ** 2 - 1
        output *= x
    return output

def s_p_at_p(at, log_n, debug=False):
    x, y = at
    if debug:
        print('v_n_prod(x):', v_n_prod(x, log_n), 'y:', y)
    return -v_n_prod(x, log_n) * (2 ** (2 * log_n - 1)) * y

def batch_multiplicative_inverse(x):
    return [1 / x_i for x_i in x]

def compute_lagrange_den_batched(points, at, log_n, debug=False):
    numer = []
    denom = []
    for pt in points:
        diff = at - pt
        x, y = diff
        numer.append(x + 1)
        if debug:
            print('y:', y, 'pt:', pt, 's_p_at_p:', s_p_at_p(pt, log_n))
        denom.append(y * s_p_at_p(pt, log_n, debug=False))
    
    inv_d = batch_multiplicative_inverse(denom)

    return [numer[i] * inv_d[i] for i in range(len(numer))]

def evaluate_at_point(evals, domain, point, debug=False):
    assert len(evals) == len(domain), "len(evals) != len(domain), {} != {}, evals={}, domain={}".format(len(evals), len(domain), evals, domain)
    x, _ = point
    log_n = log_2(len(evals))
    shift = g_30 ** (5 - log_n)
    lagrange_num = zeroifier(x, shift, log_n)
    lagrange_den = compute_lagrange_den_batched(domain, point, log_n, debug)

    return sum([lagrange_den[i] * evals[i] for i in range(len(evals))]) * lagrange_num

def deep_quotient_vanishing_part(x, zeta, alpha_pow_width, debug=False):
    v_p = lambda p, at: (1 - (p - at)[0], -(p - at)[1])
    re_v_zeta, im_v_zeta = v_p(x, zeta)
    # if debug: print('re_v_zeta:', re_v_zeta, 'im_v_zeta:', im_v_zeta)
    return (re_v_zeta - alpha_pow_width * im_v_zeta, re_v_zeta ** 2 + im_v_zeta ** 2)

def deep_quotient_reduce(evals, domain, alpha, zeta, p_at_zeta, debug=False):
    vp_nums, vp_demons = zip(*[(deep_quotient_vanishing_part(x, zeta, alpha, debug)) for x in domain])
    vp_denom_invs = batch_multiplicative_inverse(vp_demons)
    if debug: print('vp_nums:', vp_nums, 'vp_denom_invs:', vp_denom_invs, 'p_at_zeta:', p_at_zeta, 'evals:', evals)

    return [vp_nums[i] * vp_denom_invs[i] * (-p_at_zeta + evals[i]) for i in range(len(evals))]

def deep_quotient_reduce_row(alpha, x, zeta, ps_at_x, ps_at_zeta, debug=False):
    vp_num, vp_denom = deep_quotient_vanishing_part(x, zeta, alpha)
    if debug: print('vp_num:', vp_num, 'vp_denom:', vp_denom, 'ps_at_x:', ps_at_x, 'ps_at_zeta:', ps_at_zeta)
    return vp_num * (-ps_at_zeta + ps_at_x) / vp_denom

def extract_lambda(lde, log_blowup, debug=False):
    if debug:
        assert isinstance(lde, list), f'lde is not of type list: {lde}'
    log_lde_size = log_2(len(lde))

    if debug: print('log_lde_size:', log_lde_size, ', log_blowup:', log_blowup)
    if debug: print('CirclePCS.domains[log_lde_size][:1 << log_blowup]:', CirclePCS.domains[log_lde_size][:1 << log_blowup])
    v_d_init = [v_n(p[0], log_lde_size - log_blowup) for p in CirclePCS.domains[log_lde_size][:1 << log_blowup]]

    v_d = v_d_init + v_d_init[::-1]
    while (len(v_d) < len(lde)):
        v_d += v_d
    
    v_d_2 = C31(2) ** (log_lde_size - 1)
    
    if debug: print('lde:', lde)
    if debug: print('v_d:', v_d)
    lambda_ = sum([lde[i] * v_d[i] for i in range(len(lde))]) * (1 / v_d_2)
    if debug: print('lambda_:', lambda_)

    new_lde = []
    for y, v_x in zip(lde, v_d):
        new_lde.append(y - lambda_ * v_x)

    return new_lde, lambda_

def twin_cosets(n, size):
    k = log_2(size * n)
    log_size = log_2(size)
    G_size_over_2 = G[log_size - 1]

    shifts = [standard_position_cosets[k][i] for i in range(size * n // 4)]
    shifts_inv = [group_inv(shifts[i]) for i in range(size * n // 4)]
    coset_1 = [[G_size_over_2[j] * shifts[i] for j in range(size // 2)] for i in range(n)]
    coset_2 = [[G_size_over_2[(j + 1) % (size // 2)] * shifts_inv[i] for j in range(size // 2)] for i in range(n)]
    res = []
    for i in range(n):
        c1 = coset_1[i]
        c2 = coset_2[i]
        tmp = zip(c1, c2)
        res += [[x for y in tmp for x in list(y)]]
    return res

def pop(v):
    assert len(v) > 0, "v is empty"
    return v[0], v[1:]

def combine(cosets):
    cosets = cosets[:]
    n = len(cosets)
    res = []
    while len(cosets[0]) > 0:
        for i in range(n):
            t, cosets[i] = pop(cosets[i])
            res += [t]
        for i in range(n):
            t, cosets[n - 1 - i] = pop(cosets[n - 1 - i])
            res += [t]
    return res

# test twin_cosets
tcs = twin_cosets(2, 4)
for tc in tcs:
    for t in tc:
        assert t in standard_position_cosets[log_2(8)]
assert combine(tcs) == standard_position_cosets[log_2(8)], f'combine error, {combine(tcs)}, {standard_position_cosets[log_2(8)]}'

class CFFT:
    @classmethod
    def _ifft_first_step(cls, f):
        f0 = {}
        f1 = {}
        for t in f:
            x, y = t

            f0[x] = (f[t] + f[group_inv(t)]) / C31(2)
            f1[x] = (f[t] - f[group_inv(t)]) / (C31(2) * y)

            # Check that f is divided into 2 parts correctly
            assert f[t] == f0[x] + y * f1[x]

        return f0, f1
    
    @classmethod
    def _ifft_normal_step(cls, f):
        if len(f) == 1:
            res = []
            for x in f:
                res.append(f[x])
            return res

        f0 = {}
        f1 = {}

        for x in f:
            assert x != 0, "f should be on coset"
            f0[pi(x)] = (f[x] + f[-x]) / F31(2)
            f1[pi(x)] = (f[x] - f[-x]) / (F31(2) * x)

            # Check that f is divided into 2 parts correctly
            assert f[x] == f0[pi(x)] + x * f1[pi(x)]

        return cls._ifft_normal_step(f0) + cls._ifft_normal_step(f1)
    
    @classmethod
    def ifft(cls, f):
        f0, f1 = cls._ifft_first_step(f)
        f0 = cls._ifft_normal_step(f0)
        f1 = cls._ifft_normal_step(f1)

        return f0 + f1
    
    @classmethod
    def fft_first_step(cls, f, D):
        # Check that the polynomial and the domain have the same length
        assert len(f) == len(D), "len(f) != len(D), {} != {}, f={}, D={}".format(len(f), len(D), f, D)

        # divide the polynomial into 2 parts
        len_f = len(f)
        f0 = f[:len_f//2]
        f1 = f[len_f//2:]

        # halve the domain by simply removing the y coordinate
        D_new = [p[0] for p in D[:len(D)//2]]

        # Check that the new domain is exactly half size of the old domain
        assert len(D_new) * 2 == len(D), "len(D_new) * 2 != len(D), {} * 2 != {}, D_new={}, D={}".format(len(D_new), len(D), D_new, D)

        return f0, f1, D_new
    
    @classmethod
    def fft_normal_step(cls, f, D):
        if len(f) == 1:
            return {D[0]: f[0]}
        
        next_domain = pie_group(D)

        # Check that the new domain is exactly half size of the old domain
        assert len(next_domain) * 2 == len(D), "len(next_domain) * 2 != len(D), {} * 2 != {}, next_domain={}, D={}".format(len(next_domain), len(D), next_domain, D)
        # Check that the polynomial and the domain have the same length
        assert len(f) == len(D), "len(f) != len(D), {} != {}, f={}, D={}".format(len(f), len(D), f, D)

        f0 = cls.fft_normal_step(f[:len(f)//2], next_domain)
        f1 = cls.fft_normal_step(f[len(f)//2:], next_domain)

        f_new = {}
        for x in D:
            f_new[x] = f0[pi(x)] + f1[pi(x)] * x

        # Check that f is divided into 2 parts correctly
        for x in D:
            if x != 0:
                assert f0[pi(x)] == (f_new[x] + f_new[-x]) / C31(2), "f0[pi(x)] = {}".format(f0[pi(x)])
                assert f1[pi(x)] == (f_new[x] - f_new[-x]) / (C31(2) * x), "f1[pi(x)] = {}".format(f1[pi(x)])
            else:
                assert f0[pi(x)] == f_new[x], "f0[pi(x)] = {}".format(f0[pi(x)])

        # Check that the polynomial and the domain have the same length
        assert len(f) == len(f_new), "len(f) != len(f_new), {} != {}, f={}, f_new={}, D={}".format(len(f), len(f_new), f, f_new, D)

        # Check that ifft and fft are correct inverse operations
        assert cls._ifft_normal_step(f_new) == f, "ifft(f_new) != f, {} != {}".format(cls._ifft_normal_step(f_new), f)
            
        return f_new
    
    @classmethod
    def fft(cls, f, D):
        # Check that the polynomial and the domain have the same length
        assert len(f) == len(D), "len(f) != len(D), {} != {}, f={}, D={}".format(len(f), len(D), f, D)

        D_copy = D[:]
        f0, f1, D = cls.fft_first_step(f, D)

        # Check that the polynomial and the domain have the same length
        assert len(f0) == len(D), "len(f0) != len(D), {} != {}, f0={}, D={}".format(len(f0), len(D), f0, D)
        assert len(f1) == len(D), "len(f1) != len(D), {} != {}, f1={}, D={}".format(len(f1), len(D), f1, D)

        f0 = cls.fft_normal_step(f0, D)
        f1 = cls.fft_normal_step(f1, D)

        f = {}
        # supply y to the polynomial
        for t in D_copy:
            x, y = t
            f[t] = f0[x] + f1[x] * y

        return f
    
    @classmethod
    def vec_2_poly(cls, vec, domain):
        f = {}
        for i, t in enumerate(domain):
            f[t] = vec[i]
        return f
    
    @classmethod
    def poly_2_vec(cls, poly):
        return [poly[t] for t in poly]
    
    @classmethod
    def extrapolate(cls, evals, domain, blowup_factor):
        evals = cls.vec_2_poly(evals, domain)
        coeffs = cls.ifft(evals)
        cosets = twin_cosets(blowup_factor, len(evals))
        res = []
        for coset in cosets:
            res += [cls.fft(coeffs, coset)]
        res = [cls.poly_2_vec(x) for x in res]
        return combine(res)
    
class FRI:
    @classmethod
    def fold_y(cls, evals, domain, beta, debug=False):
        # first step (J mapping)
        # for f in natural order, we just divide f into 2 parts from the middle
        N = len(evals)
        assert N % 2 == 0, "N must be even, N={}".format(N)

        left = evals[:N//2]
        right = evals[:N//2-1:-1]
        assert len(left) == len(right), "len(left) != len(right), {} != {}, left={}, right={}".format(len(left), len(right), left, right)
        evals = [None for _ in range(N//2)]
        for i, (_, y) in enumerate(domain[:N//2]):
            f0 = (left[i] + right[i]) / 2
            f1 = (left[i] - right[i]) / (2 * y)
            evals[i] = f0 + group_mul(beta, f1)
            if debug: print('fold y')
            if debug: print(f"f0 = (({left[i]}) + ({right[i]}))/2 = {f0}")
            if debug: print(f"f1 = (({left[i]}) - ({right[i]}))/(2 * {y}) = {f1}")
            if debug: print(f"f0 + ({beta}) * f1 = ({f0}) + ({beta}) * ({f1}) = {f0 + group_mul(beta, f1)}")

        return evals
    
    @classmethod
    def fold_y_row(cls, y, beta, left, right, debug=False):
        f0 = (left + right) / 2
        f1 = (left - right) / (2 * y)
        if debug: print('fold y row')
        if debug: print(f"f0 = (({left}) + ({right}))/2 = {f0}")
        if debug: print(f"f1 = (({left}) - ({right}))/(2 * {y}) = {f1}")
        if debug: print(f"f0 + ({beta}) * f1 = ({f0}) + ({beta}) * ({f1}) = {f0 + group_mul(beta, f1)}")
        return f0 + group_mul(beta, f1)
    
    # Inputs:
    #   f is the polynomial to be folded
    #   D is the domain of f
    #   r is the random number for random linear combination
    # Outputs:
    #   The first return value is the folded polynomial
    #   The second return value is the new domain
    @classmethod
    def fold_x(cls, f, D, r, debug=False):
        assert len(f) == len(D), "len(f) != len(D), {} != {}, f={}, D={}".format(len(f), len(D), f, D)

        # divide
        N = len(f)
        # left is the first half of f, of x from 1 to g^(N/2)
        left = f[:N//2]
        # right is the second half of f, of x from g^(N-1) to g^(N/2), which corresponds to minus x in left
        right = f[:N//2-1:-1]
        assert len(left) == len(right), "len(left) != len(right), {} != {}, left={}, right={}".format(len(left), len(right), left, right)

        for i, x in enumerate(D[:N//2]):
            # f == f0 + x * f1
            f0 = (left[i] + right[i]) * (1 / F31(2))
            f1 = (left[i] - right[i]) * (1 / (F31(2) * x))
            # f[:N//2] stores the folded polynomial
            if debug: print('fold x')
            if debug: print(f"f[{i}] = {f[i]} = ({left[i]} + {right[i]})/2 + {r} * ({left[i]} - {right[i]})/(2 * {x})")
            f[i] = f0 + r * f1
            # if debug: print(f"{f[i]} = ({left[i]} + {right[i]})/2 + {r} * ({left[i]} - {right[i]})/(2 * {x})")
            # reuse f[N//2:] to store new domain
            f[N//2 + i] = 2 * x ** 2 - 1

        # return the folded polynomial and the new domain
        return f[:N//2], f[N//2:]
    
    @classmethod
    def commit_phase(cls, input, blowup_factor, domain, transcript, debug=False):
        assert isinstance(transcript, MerlinTranscript), "transcript should be a MerlinTranscript"
        folded = input

        # fold
        trees = []
        oracles = []
        while len(folded) > blowup_factor:
            # commit
            tree = MerkleTree(folded)
            transcript.append_message(b'tree', bytes(tree.root, 'ascii'))

            # merkle tree
            trees.append(tree)
            oracles.append(folded[:])

            beta = int.from_bytes(transcript.challenge_bytes(b'beta', int(4)), 'big')
            if debug: print('beta:', beta)
            if debug: print('folded:', folded, ', domain:', domain)
            folded, domain = cls.fold_x(folded, domain, beta, debug)

            if debug: print(f"f={folded}, D={domain}")

        final_poly = folded[0]
        if debug:
            print('folded:', folded)
            for x in folded:
                assert final_poly == x, "final_poly != x, {} != {}, final_poly={}, x={}".format(final_poly, x, final_poly, x)
        transcript.append_message(b"final_poly", bytes(str(final_poly), 'ascii'))

        if debug: print('oracles:', oracles)

        return {
            "commits": [tree.root for tree in trees],
            "trees": trees,
            "oracles": oracles,
            "final_poly": final_poly
        }
    
    @classmethod
    def answer_query(cls, trees, oracles, index, debug=False):
        if debug: print('answer_query')
        opening_proofs = []
        sibling_values = []
        if debug:
            print('trees:', [tree.data for tree in trees])
        index_i = index
        for i, tree in enumerate(trees):
            assert isinstance(tree, MerkleTree), "tree should be a MerkleTree"
            if debug:
                print('len(tree.data):', len(tree.data), ', index_i:', index_i)
            assert len(tree.data) >= 1 + index_i, "len(tree.data) < 1 + index_i, {} < {}, tree.data={}, index_i={}".format(len(tree.data), 1 + index_i, tree.data, index_i)
            index_i_sibling = len(tree.data) - 1 - index_i

            tree = trees[i]
            oracle = oracles[i]

            assert isinstance(tree, MerkleTree), "tree should be a MerkleTree"

            opening_proofs.append((tree.get_authentication_path(index_i), tree.get_authentication_path(index_i_sibling)))
            sibling_values.append(oracle[index_i_sibling])

            if debug:
                print('index_i:', index_i, ', oracle[index_i]:', oracle[index_i], ', opening_proofs[-1][0]:', opening_proofs[-1][0], ', tree.root:', tree.root)
                assert verify_decommitment(index_i, oracle[index_i], opening_proofs[-1][0], tree.root), "verify_decommitment failed"
                print('index_i_sibling:', index_i_sibling, ', oracle[index_i_sibling]:', oracle[index_i_sibling], ', opening_proofs[-1][1]:', opening_proofs[-1][1], ', tree.root:', tree.root)
                assert verify_decommitment(index_i_sibling, oracle[index_i_sibling], opening_proofs[-1][1], tree.root), "verify_decommitment failed"

            index_i = min(index_i, index_i_sibling)

        return zip(opening_proofs, sibling_values)

    @classmethod
    def prove(cls, input, blowup_factor, domain, transcript, open_input, num_queries, debug=False):
        assert isinstance(transcript, MerlinTranscript), "transcript should be a MerlinTranscript"

        degree = len(input)

        # commit phase
        commit_phase_result = cls.commit_phase(input, blowup_factor, domain, transcript, debug)

        # query phase
        queries = []
        for _ in range(num_queries):
            queries.append(int.from_bytes(transcript.challenge_bytes(b"query", 4), "big"))
            if debug: print('query:', queries[-1])

        query_proofs = []
        if debug: print('queries:', queries, ', degree:', degree, ', query >> (32 - log_2(degree)):', [query >> (32 - log_2(degree)) for query in queries])
        for query in queries:
            index = query >> (32 - log_2(degree) - 1)
            index_sibling = degree * 2 - 1 - index
            query_proofs.append({
                "input_proof": open_input(index),
                "commit_phase_openings": cls.answer_query(commit_phase_result["trees"], commit_phase_result["oracles"], min(index, index_sibling), debug)
            })

        return {
            "commit_phase_commits": commit_phase_result["commits"],
            "query_proofs": query_proofs,
            "final_poly": commit_phase_result["final_poly"]
        }

    @classmethod
    def verify_query(cls, index, steps, reduced_opening, log_max_height, debug=False):
        if debug: print('verify_query')
        if debug: print('index:', index)
        folded_eval = reduced_opening
        if debug: print('log_max_height:', log_max_height)
        for log_folded_height, (beta, comm, opening) in zip(range(log_max_height, 0, -1), steps):
            assert 1 << log_folded_height >= 1 + index, "1 << log_folded_height < 1 + index, {} < 1 + {}".format(1 << log_folded_height, index)
            if debug:
                print('log_folded_height:', log_folded_height, ', index:', index)
            index_sibling = (1 << log_folded_height) - 1 - index

            opening_proofs = opening[0]
            sibling_values = opening[1]

            if debug: print('index:', index, ', folded_eval:', folded_eval, ', opening_proofs[0]:', opening_proofs[0], ', comm:', comm)
            assert verify_decommitment(index, folded_eval, opening_proofs[0], comm), "verify_decommitment failed"
            if debug: print('index_sibling:', index_sibling, ', sibling_values:', sibling_values, ', opening_proofs[1]:', opening_proofs[1], ', comm:', comm)
            assert verify_decommitment(index_sibling, sibling_values, opening_proofs[1], comm), "verify_decommitment failed"

            domain = CirclePCS.natural_domain_for_degree(2 << log_folded_height)
            domain = [t[0] for t in domain]
            x = domain[min(index, index_sibling)]
            left = folded_eval if index < index_sibling else sibling_values
            right = sibling_values if index < index_sibling else folded_eval
            if debug: print('left:', left, ', right:', right, ', x:', x)
            folded_eval = (left + right) / F31(2) + beta * ((left - right) / (F31(2) * x))

            index = min(index, index_sibling)

        return folded_eval

    @classmethod
    def verify(cls, proof, transcript, open_input, debug=False):
        assert isinstance(transcript, MerlinTranscript), "transcript should be a MerlinTranscript"

        betas = []
        for commit in proof["commit_phase_commits"]:
            transcript.append_message(b"tree", bytes(commit, 'ascii'))
            beta = int.from_bytes(transcript.challenge_bytes(b"beta", 4), "big")
            if debug: print('beta:', beta)
            betas.append(beta)
        transcript.append_message(b"final_poly", bytes(str(proof["final_poly"]), 'ascii'))

        folded_eval = 0
        for qp in proof["query_proofs"]:
            index = int.from_bytes(transcript.challenge_bytes(b"query", 4), "big")
            if debug: print('query:', index)

            log_max_height = len(proof["commit_phase_commits"])
            index >>= (32 - log_max_height - 1)
            index_sibling = (1 << log_max_height) * 2 - 1 - index
            if debug: print('log_max_height:', log_max_height, ', index:', index, ', index_sibling:', index_sibling)

            ro = open_input(index, qp["input_proof"])
            folded_eval = cls.verify_query(min(index, index_sibling), zip(betas, proof["commit_phase_commits"], qp["commit_phase_openings"]), ro, log_max_height, debug)

            if debug: print('folded_eval:', folded_eval)

        assert folded_eval == proof["final_poly"], "folded_eval != proof['final_poly'], {} != {}".format(folded_eval, proof["final_poly"])

class CirclePCS:
    G5 = [g_30**k for k in range(32)]
    G4_standard = [g_30 * t for t in sq(G5)]
    G3_standard = sq(G4_standard)
    G2_standard = sq(G3_standard)
    G1_standard = sq(G2_standard)
    G0_standard = sq(G1_standard)
    domains = [G0_standard, G1_standard, G2_standard, G3_standard, G4_standard]

    @classmethod
    def natural_domain_for_degree(cls, degree):
        log_degree = log_2(degree)
        if log_degree > 4:
            raise ValueError("Degree too high")
        
        return cls.domains[log_degree]
    
    @classmethod
    def commit(cls, eval, domain, blowup_factor):
        log_n = log_2(len(eval))
        if log_n + log_2(blowup_factor) > 4:
            raise ValueError("Eval too long")
        
        lde = CFFT.extrapolate(eval, domain, blowup_factor)
        return MerkleTree(lde), lde
    
    @classmethod
    def open(cls, evals, evals_commit, zeta, log_blowup, transcript, num_queries, debug=False):
        if debug: print('evals:', evals)
        assert isinstance(transcript, MerlinTranscript), "transcript should be a MerlinTranscript"
        alpha = int.from_bytes(transcript.challenge_bytes(b"alpha", 4), "big")
        if debug: print('alpha:', alpha)

        # evaluate the polynomial at the point zeta
        domain = cls.natural_domain_for_degree(len(evals))
        p_at_zeta = evaluate_at_point(evals, domain, zeta, debug)
        if debug: print('p_at_zeta:', p_at_zeta)

        # deep quotient
        reduced_opening = deep_quotient_reduce(evals, domain, alpha, zeta, p_at_zeta, debug)
        if debug: print('reduced_opening:', reduced_opening)
        # extract lambda
        first_layer, lambda_ = extract_lambda(reduced_opening, log_blowup, debug)
        if debug: print('first_layer:', first_layer, ', lambda_:', lambda_)

        # commit first layer
        first_layer_tree = MerkleTree(first_layer)
        transcript.append_message(b"first_layer_root", bytes(first_layer_tree.root, 'ascii'))
        bivariate_beta = int.from_bytes(transcript.challenge_bytes(b"bivariate_beta x", 4), "big") + int.from_bytes(transcript.challenge_bytes(b"bivariate_beta y", 4), "big") * I
        if debug: print('bivariate_beta:', bivariate_beta)
        # fold first layer
        # a little modified compared to code in p3
        fri_input = FRI.fold_y(first_layer, domain, bivariate_beta, debug)
        fri_input = [t[0] for t in fri_input]
        domain = [t[0] for t in domain[:len(domain)//2]]
        if debug:
            print('fri_input:', fri_input)
            print('domain:', domain)

        def open_input(index):
            if debug: print('open_input')
            # index >>= 32 - log_2(len(evals))
            assert isinstance(evals_commit, MerkleTree), "evals_commit should be a MerkleTree"
            input_opening = (evals_commit.get_authentication_path(index), evals[index])

            if debug:
                print('index:', index, ', evals:', evals, ', input_opening[0]:', input_opening[0], ', evals_commit.root:', evals_commit.root)
                assert verify_decommitment(index, evals[index], input_opening[0], evals_commit.root), "verify_decommitment failed"

            first_layer_index = index
            first_layer_index_sibling = len(first_layer) - 1 - first_layer_index
            first_layer_proof = (first_layer_tree.get_authentication_path(first_layer_index), first_layer_tree.get_authentication_path(first_layer_index_sibling))

            if debug:
                print('first_layer_index:', first_layer_index, ', first_layer[first_layer_index]:', first_layer[first_layer_index], ', first_layer_proof[0]:', first_layer_proof[0], ', first_layer_tree.root:', first_layer_tree.root)
                assert verify_decommitment(first_layer_index, first_layer[first_layer_index], first_layer_proof[0], first_layer_tree.root), "verify_decommitment failed"
                print('first_layer_index_sibling:', first_layer_index_sibling, ', first_layer[first_layer_index_sibling]:', first_layer[first_layer_index_sibling], ', first_layer_proof[1]:', first_layer_proof[1], ', first_layer_tree.root:', first_layer_tree.root)
                assert verify_decommitment(first_layer_index_sibling, first_layer[first_layer_index_sibling], first_layer_proof[1], first_layer_tree.root), "verify_decommitment failed"

            return {
                "input_opening": input_opening,
                "first_layer_proof": first_layer_proof,
                "first_layer_sibling_value": first_layer[first_layer_index_sibling]
            }

        fri_proof = FRI.prove(fri_input, 1 << log_blowup, domain, transcript, open_input, num_queries, debug)

        return {
            "first_layer_commitment": first_layer_tree.root,
            "lambda": lambda_,
            "fri_proof": fri_proof
        }

    @classmethod
    def verify(cls, commitment, domain, log_blowup, point, value, proof, transcript, debug=False):
        assert isinstance(transcript, MerlinTranscript), "transcript should be a MerlinTranscript"
        alpha = int.from_bytes(transcript.challenge_bytes(b"alpha", 4), "big")
        if debug: print('alpha:', alpha)
        transcript.append_message(b"first_layer_root", bytes(proof["first_layer_commitment"], 'ascii'))
        bivariate_beta = int.from_bytes(transcript.challenge_bytes(b"bivariate_beta x", 4), "big") + int.from_bytes(transcript.challenge_bytes(b"bivariate_beta y", 4), "big") * I
        if debug: print('bivariate_beta:', bivariate_beta)

        def open_input(index, input_proof):
            if debug: print('open_input')
            if debug: print('index:', index)
            # verify first layer
            input_opening = input_proof['input_opening']
            first_layer_proof = input_proof['first_layer_proof']
            first_layer_sibling_value = input_proof['first_layer_sibling_value']

            # index_shifted = index >> (32 - log_2(len(domain)))
            index_shifted = index
            if debug: print('len(domain):', len(domain))
            if debug: print('index_shifted:', index_shifted, ', input_opening[0]:', input_opening[0], ', commitment:', commitment)
            assert verify_decommitment(index_shifted, input_opening[1], input_opening[0], commitment)

            # deep quotient
            reduced_opening = deep_quotient_reduce_row(alpha, domain[index_shifted], point, input_opening[1], value, debug)
            if debug: print('domain:', domain, ', log_2(len(domain)) - log_blowup:', log_2(len(domain)) - log_blowup, ', v_n(domain[index_shifted], log_2(len(domain)) - log_blowup):', v_n(domain[index_shifted], log_2(len(domain)) - log_blowup))
            if debug: print('reduced_opening:', reduced_opening, ', proof["lambda"]:', proof["lambda"])
            lambda_corrected = reduced_opening - proof["lambda"] * v_n(domain[index_shifted][0], log_2(len(domain)) - log_blowup)
            if debug: print('lambda_corrected:', lambda_corrected)

            left = lambda_corrected if index_shifted < len(domain) // 2 else first_layer_sibling_value
            right = first_layer_sibling_value if index_shifted < len(domain) // 2 else lambda_corrected
            index_sibling = len(domain) - 1 - index_shifted
            _, y = domain[min(index_shifted, index_sibling)]
            fri_input = FRI.fold_y_row(y, bivariate_beta, left, right, debug)
            fri_input = fri_input[0]
            if debug: print('fri_input:', fri_input)

            if debug: print('index_shifted:', index_shifted, ', lambda_corrected:', lambda_corrected, ', first_layer_proof[0]:', first_layer_proof[0], ', commitment:', proof['first_layer_commitment'])
            assert verify_decommitment(index_shifted, lambda_corrected, first_layer_proof[0], proof['first_layer_commitment'])
            if debug: print('len(domain) - 1 - index_shifted:', len(domain) - 1 - index_shifted, ', first_layer_sibling_value:', first_layer_sibling_value, ', first_layer_proof[1]:', first_layer_proof[1], ', commitment:', proof['first_layer_commitment'])
            assert verify_decommitment(len(domain) - 1 - index_shifted, first_layer_sibling_value, first_layer_proof[1], proof['first_layer_commitment'])

            return fri_input

        FRI.verify(proof["fri_proof"], transcript, open_input, debug)

if __name__ == "__main__":
    from random import randint
    rand_ext = lambda: randint(0, 31) + randint(0, 31) * I
    # evals = [rand_ext() for _ in range(2)]
    evals = [F31(1), F31(2), F31(3), F31(4)]
    domain = CirclePCS.natural_domain_for_degree(len(evals))
    print('domain:', domain)
    log_blowup = 1

    commitment, lde = CirclePCS.commit(evals, domain, 1 << log_blowup)
    print('lde:', lde)

    transcript = MerlinTranscript(b'circle pcs')
    transcript.append_message(b'commitment', bytes(str(commitment.root), 'ascii'))

    query_num = 1

    domain = CirclePCS.natural_domain_for_degree(len(lde))
    point = CirclePCS.G5[5]
    proof = CirclePCS.open(lde, commitment, point, log_blowup, transcript, query_num, True)

    transcript = MerlinTranscript(b'circle pcs')
    transcript.append_message(b'commitment', bytes(str(commitment.root), 'ascii'))
    CirclePCS.verify(commitment.root, domain, log_blowup, point, evaluate_at_point(evals, CirclePCS.natural_domain_for_degree(len(evals)), point), proof, transcript, True)
