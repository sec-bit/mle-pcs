from sage.all import *
import sys

sys.path.append("../")
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
i, = C31.gens()

g = 10 + 5 * i
g_30 = g**30

assert g_30**32 == 1

def sq(D):
    rs = []
    for t in D[:len(D)//2]:
        # x' == 2 * x^2 - 1
        rs += [t**2]
    return rs

def group_inv(g1):
    x1, y1 = g1
    return x1 - y1 * i

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

def s_p_at_p(at, log_n):
    x, y = at
    -v_n_prod(x, log_n) * (2 ** (2 * log_n - 1)) * y

def batch_multiplicative_inverse(x):
    return [1 / x_i for x_i in x]

def compute_lagrange_den_batched(points, at, log_n):
    numer = []
    denom = []
    for pt in points:
        diff = at - pt
        x, y = diff
        numer.append(x + 1)
        denom.append(y * s_p_at_p(pt, log_n))
    
    inv_d = batch_multiplicative_inverse(denom)

    return [numer[i] * inv_d[i] for i in range(len(numer))]

def evaluate_at_point(evals, domain, point):
    assert len(evals) == len(domain), "len(evals) != len(domain), {} != {}, evals={}, domain={}".format(len(evals), len(domain), evals, domain)
    x, _ = point
    log_n = log_2(len(evals))
    shift = g ** (5 - log_n)
    lagrange_num = zeroifier(x, shift, log_n)
    lagrange_den = compute_lagrange_den_batched(domain, point, log_n)

    return lagrange_num * sum([evals[i] * lagrange_den[i] for i in range(len(evals))])

def deep_quotient_vanishing_part(x, zeta, alpha_pow_width):
    v_p = lambda p, at: (1 - (p - at)[0], -(p - at)[1])
    re_v_zeta, im_v_zeta = v_p(x, zeta)
    return (re_v_zeta - alpha_pow_width * im_v_zeta, re_v_zeta ** 2 + im_v_zeta ** 2)

def deep_quotient_reduce(evals, domain, alpha, zeta, p_at_zeta):
    vp_nums, vp_demons = zip(*[(deep_quotient_vanishing_part(x, zeta, alpha)) for x in domain])
    vp_denom_invs = batch_multiplicative_inverse(vp_demons)
    
    powers_of_alpha = [alpha ** i for i in range(len(evals))]

    return vp_nums * vp_denom_invs * (sum([evals[i] * powers_of_alpha[i] for i in range(len(evals))]) - p_at_zeta)

def extract_lambda(lde, log_blowup):
    log_lde_size = log_2(len(lde))

    v_d_init = [v_n(p, log_lde_size - log_blowup) for p in CirclePCS.domains[log_lde_size][:1 << log_blowup]]

    v_d = v_d_init + v_d_init[:-1]
    while (len(v_d) < len(lde)):
        v_d += v_d
    
    v_d_2 = C31(2) ** (log_lde_size - 1)
    
    lambda_ = sum([lde[i] * v_d[i] for i in range(len(lde))]) / v_d_2

    for y, v_x in zip(lde, v_d):
        y -= lambda_ * v_x

    return lde, lambda_

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
            f0[pi(x)] = (f[x] + f[-x]) / C31(2)
            f1[pi(x)] = (f[x] - f[-x]) / (C31(2) * x)

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
        D_new = []
        for t in D:
            x, _ = t
            if x not in D_new:
                D_new.append(x)

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
    def extrapolate(cls, evals, blowup_factor):
        new_domain = CirclePCS.natural_domain_for_degree(len(evals) * blowup_factor)
        coeffs = CFFT.ifft(evals)
        coeffs += [0] * (len(evals) * (blowup_factor - 1))
        return CFFT.fft(coeffs, new_domain)
    
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
            f0 = (left[i] + right[i]) / C31(2)
            f1 = (left[i] - right[i]) / (C31(2) * y)
            evals[i] = f0 + beta * f1
            if debug: print(f"f[{i}] = {evals[i]} = ({left[i]} + {right[i]})/2 + {beta} * ({left[i]} - {right[i]})/(2 * {y})")

        return evals
    
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
            f0 = (left[i] + right[i]) / C31(2)
            f1 = (left[i] - right[i]) / (C31(2) * x)
            # f[:N//2] stores the folded polynomial
            if debug: print(f"f[{i}] = {f[i]} = ({left[i]} + {right[i]})/2 + {r} * ({left[i]} - {right[i]})/(2 * {x})")
            f[i] = f0 + r * f1
            # if debug: print(f"{f[i]} = ({left[i]} + {right[i]})/2 + {r} * ({left[i]} - {right[i]})/(2 * {x})")
            # reuse f[N//2:] to store new domain
            f[N//2 + i] = 2 * x^2 - 1

        # return the folded polynomial and the new domain
        return f[:N//2], f[N//2:]
    
    @classmethod
    def commit_phase(cls, input, domain, transcript, debug=False):
        assert isinstance(transcript, MerlinTranscript), "transcript should be a MerlinTranscript"
        folded = input

        # fold
        trees = []
        oracles = []
        for _ in range(log_2(len(input))):
            # random number
            transcript.append_message(b'tree', bytes(trees[-1].root, 'ascii'))

            beta = int.from_bytes(transcript.challenge_bytes(b'beta', int(4)), 'big')
            folded, domain = cls.fold_x(folded, domain, beta, debug)

            if debug: print(f"f={folded}, D={domain}")

            # merkle tree
            trees.append(MerkleTree(folded))
            oracles.append(folded[:])

        final_poly = folded[0]
        if debug:
            for x in folded:
                assert final_poly == x, "final_poly != x, {} != {}, final_poly={}, x={}".format(final_poly, x, final_poly, x)
        transcript.append_message(b"final_poly", bytes(final_poly, 'ascii'))

        return {
            "commits": [tree.root for tree in trees],
            "trees": trees,
            "oracles": oracles,
            "final_poly": final_poly
        }
    
    @classmethod
    def answer_query(cls, trees, oracles, index, degree, debug=False):
        opening_proofs = []
        sibling_values = []
        for i, tree in enumerate(trees):
            index_i = index >> i
            index_i_sibling = 1 << degree - 1 - index_i
            degree >>= 1

            tree = trees[i]
            oracle = oracles[i]

            assert isinstance(tree, MerkleTree), "tree should be a MerkleTree"

            opening_proofs.append((tree.get_authentication_path(index_i), tree.get_authentication_path(index_i_sibling)))
            sibling_values.append(oracle[index_i_sibling])

            if debug:
                assert verify_decommitment(index_i, oracle[index_i], opening_proofs[0], tree.root), "verify_decommitment failed"
                assert verify_decommitment(index_i_sibling, oracle[index_i_sibling], opening_proofs[1], tree.root), "verify_decommitment failed"

        return zip(opening_proofs, sibling_values)

    @classmethod
    def prove(cls, input, domain, transcript, open_input, num_queries, debug=False):
        assert isinstance(transcript, MerlinTranscript), "transcript should be a MerlinTranscript"

        degree = len(input)

        # commit phase
        commit_phase_result = cls.commit_phase(input, domain, transcript, debug)

        # query phase
        sample = lambda: int.from_bytes(transcript.challenge_bytes(b"query", 4), "big")
        queries = [sample() for _ in range(num_queries)]

        query_proofs = []
        for query in queries:
            query_proofs.append({
                "input_proof": open_input(query),
                "commit_phase_openings": cls.answer_query(commit_phase_result["trees"], commit_phase_result["oracles"], query >> (32 - log_2(degree)), degree, debug)
            })

        return {
            "commit_phase_commits": commit_phase_result["commits"],
            "query_proofs": query_proofs,
            "final_poly": commit_phase_result["final_poly"]
        }

    @classmethod
    def verify_query(cls, index, steps, reduced_opening, log_max_height):
        folded_eval = reduced_opening
        for log_folded_height, (beta, comm, opening) in zip(range(log_max_height)[::-1], steps):
            index_sibling = 1 << log_folded_height - 1 - index

            opening_proofs = opening[0]
            sibling_values = opening[1]

            assert verify_decommitment(index, folded_eval, opening_proofs[0], comm), "verify_decommitment failed"
            assert verify_decommitment(index_sibling, sibling_values, opening_proofs[1], comm), "verify_decommitment failed"

            domain = CirclePCS.natural_domain_for_degree(1 << log_folded_height)
            x = domain[index]
            left = folded_eval if index < index_sibling else sibling_values
            right = sibling_values if index < index_sibling else folded_eval
            folded_eval = (left + right) / C31(2) + beta * ((left - right) / (C31(2) * x))

        return folded_eval

    @classmethod
    def verify(cls, proof, transcript, open_input, debug=False):
        assert isinstance(transcript, MerlinTranscript), "transcript should be a MerlinTranscript"

        betas = []
        for i in range(len(proof["trees"])):
            transcript.append_message(b"tree", bytes(proof["commit_phase_commits"][i], 'ascii'))
            beta = transcript.challenge_bytes(b"beta", 4)
            beta = int.from_bytes(beta, "big")
            betas.append(beta)
        transcript.append_message(b"final_poly", bytes(proof["final_poly"], 'ascii'))

        folded_eval = 0
        for qp in proof["query_proofs"]:
            index = transcript.challenge_bytes(b"query", 4)
            index = int.from_bytes(index, "big")
            ro = open_input(index, qp["input_proof"])

            log_max_height = len(proof["commit_phase_commits"])
            folded_eval = cls.verify_query(index >> (32 - log_max_height), zip(betas, proof["commit_phase_commits"], qp["commit_phase_openings"]), ro, log_max_height)

        assert folded_eval == proof["final_poly"], "folded_eval != proof['final_poly'], {} != {}".format(folded_eval, proof["final_poly"])

class CirclePCS:
    G5 = [g**k for k in range(32)]
    G4_standard = [g * t for t in sq(G5)]
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
        
        eval_poly = CFFT.vec_2_poly(eval, domain)
        lde = CFFT.extrapolate(eval_poly, blowup_factor)
        tree = MerkleTree(lde)
        return tree.root, tree
    
    @classmethod
    def open(cls, evals, evals_commit, zeta, log_blowup, transcript, num_queries, debug=False):
        assert isinstance(transcript, MerlinTranscript), "transcript should be a MerlinTranscript"
        alpha = transcript.challenge_bytes(b"alpha", 4)
        alpha = int.from_bytes(alpha, "big")

        # evaluate the polynomial at the point zeta
        domain = cls.natural_domain_for_degree(len(evals))
        p_at_zeta = evaluate_at_point(evals, domain, zeta)

        # deep quotient
        reduced_opening = deep_quotient_reduce(evals, domain, alpha, zeta, p_at_zeta)

        # extract lambda
        first_layer, lambda_ = extract_lambda(reduced_opening, log_blowup)

        # commit first layer
        first_layer_tree = MerkleTree(first_layer)
        transcript.append_message(b"first_layer_root", first_layer_tree.root)
        bivariate_beta = transcript.challenge_bytes(b"bivariate_beta", 4)
        bivariate_beta = int.from_bytes(bivariate_beta, "big")

        # fold first layer
        # a little modified compared to code in p3
        fri_input = FRI.fold_y(first_layer, domain, bivariate_beta, debug)
        domain = sq(domain)

        def open_input(index):
            index >>= 32 - log_2(len(evals))
            assert isinstance(evals_commit, MerkleTree), "evals_commit should be a MerkleTree"
            input_opening = (evals_commit.get_authentication_path(index), evals[index])

            if debug:
                assert verify_decommitment(index, evals[index], input_opening, evals_commit.root), "verify_decommitment failed"

            first_layer_index = index
            first_layer_index_sibling = first_layer_index ^ 1
            first_layer_proof = (first_layer_tree.get_authentication_path(first_layer_index), first_layer_tree.get_authentication_path(first_layer_index_sibling))

            return {
                "input_proof": input_opening,
                "first_layer_proof": first_layer_proof,
                "first_layer_sibling_value": first_layer[first_layer_index_sibling]
            }

        fri_proof = FRI.prove(fri_input, domain, transcript, open_input, num_queries, debug)

        return {
            "first_layer_commitment": first_layer_tree.root,
            "lambda": lambda_,
            "fri_proof": fri_proof
        }

    @classmethod
    def verify(cls, commitment, domain, point, value, proof, transcript, debug=False):
        assert isinstance(transcript, MerlinTranscript), "transcript should be a MerlinTranscript"
        alpha = transcript.challenge_bytes(b"alpha", 4)
        alpha = int.from_bytes(alpha, "big")
        transcript.append_message(b"first_layer_root", proof["first_layer_commitment"])
        bivariate_beta = transcript.challenge_bytes(b"bivariate_beta", 4)
        bivariate_beta = int.from_bytes(bivariate_beta, "big")

        FRI.verify(proof["fri_proof"], transcript, debug)

if __name__ == "__main__":
    evals = [1, 2, 3, 4]
    poly = CFFT.vec_2_poly(evals, CirclePCS.natural_domain_for_degree(4))
    print(CFFT.extrapolate(poly, 4))
