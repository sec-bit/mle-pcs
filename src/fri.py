from merkle import MerkleTree, verify_decommitment
from merlin.merlin_transcript import MerlinTranscript
from utils import from_bytes, log_2, is_power_of_two

class FRI:
    @staticmethod
    def prove_low_degree(evals, degree_bound, coset, num_verifier_queries, debug=False):
        assert is_power_of_two(degree_bound)

        first_tree = MerkleTree(evals)
        evals_copy = evals
        transcript = MerlinTranscript(b"FRI")
        transcript.append_message(b"first_oracle", first_tree.root.encode('ascii'))

        alpha = transcript.challenge_bytes(b"alpha", 4)
        alpha = from_bytes(alpha)

        trees = []
        tree_evals = []
        for _ in range(log_2(degree_bound)):
            if debug: print("evals:", evals)
            if debug: print("alpha:", alpha)
            if debug: print("coset:", coset)
            evals = FRI.fold(evals, alpha, coset)
            tree = MerkleTree(evals)
            trees.append(tree)
            tree_evals.append(evals)

            transcript.append_message(b"oracle", tree.root.encode('ascii'))
            alpha = transcript.challenge_bytes(b"alpha", 4)
            alpha = from_bytes(alpha)

            coset *= coset

        # query phase
        query_paths, merkle_paths = FRI.query_phase(transcript, first_tree, evals_copy, trees, tree_evals, len(evals_copy), num_verifier_queries, debug)

        return {
            'query_paths': query_paths,
            'merkle_paths': merkle_paths,
            'first_oracle': first_tree.root,
            'intermediate_oracles': [tree.root for tree in trees]
        }

    # f(x) = f0(x^2) + x * f1(x^2)
    # and half degree interpolation is
    # f'(x^2) = f0(x^2) + alpha * f1(x^2), and it can be achieved by just adding up two adjustent (adjustment?)
    # coefficients in the monomial form
    # if we would want to try to get the same result, one can observe that
    # f0(x^2) = (f(x) + f(-x)) / 2
    # f1(x^2) = (f(x) - f(-x)) / 2x
    @staticmethod
    def fold(evals, alpha, coset):
        assert len(evals) % 2 == 0

        half = len(evals) // 2
        f0_evals = [(evals[i] + evals[half + i]) // 2 for i in range(half)]
        f1_evals = [(evals[i] - evals[half + i]) // (2 * coset) for i in range(half)]
        return [x + alpha * y for x, y in zip(f0_evals, f1_evals)]


    @staticmethod
    def verify_low_degree(degree_bound, proof, coset, num_verifier_queries, debug=False):
        log_degree_bound = log_2(degree_bound)
        log_evals = log_2(len(evals))
        T = [coset**(2 ** j) for j in range(0, log_evals)]
        FRI.verify_queries(proof, log_degree_bound, len(evals), num_verifier_queries, T, debug)

    @staticmethod
    def query_phase(transcript: MerlinTranscript, first_tree: MerkleTree, first_oracle, trees: list, oracles: list, num_vars, num_verifier_queries, debug=False):
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
    def verify_queries(proof, k, num_vars, num_verifier_queries, T, debug=False):
        transcript = MerlinTranscript(b"FRI")
        transcript.append_message(b"first_oracle", bytes(proof['first_oracle'], 'ascii'))
        alpha = transcript.challenge_bytes(b"alpha", 4)
        alpha = from_bytes(alpha)

        fold_challenges = [alpha]
        for i in range(k):
            transcript.append_message(bytes(f'oracle', 'ascii'), bytes(proof['intermediate_oracles'][i], 'ascii'))
            fold_challenges.append(from_bytes(transcript.challenge_bytes(b"alpha", 4)))

        queries = [from_bytes(transcript.challenge_bytes(b"queries", 4)) % num_vars for _ in range(num_verifier_queries)]
        # query loop
        for q, (cur_path, _), mps in zip(queries, proof['query_paths'], proof['merkle_paths']):
            if debug: print("cur_path:", cur_path)
            num_vars_copy = num_vars
            # fold loop
            for i, mp in enumerate(mps):
                x0 = int(q)
                x1 = int(q - num_vars_copy / 2 if q >= num_vars_copy / 2 else q + num_vars_copy / 2)
                if x1 < x0:
                    x0, x1 = x1, x0
                    
                code_left, code_right = cur_path[i][0], cur_path[i][1]

                if debug: print("x0:", x0)
                if debug: print("x1:", x1)

                if i != len(mps) - 1:
                    coset = T[i]
                    if debug: print("coset:", coset)
                    f_code_folded = cur_path[i + 1][0 if x0 < num_vars_copy / 4 else 1]
                    alpha = fold_challenges[i]
                    if debug: print("f_code_folded:", f_code_folded)
                    if debug: print("expected:", ((code_left + code_right)/2 + alpha * (code_left - code_right)/(2*coset)))
                    if debug: print("code_left:", code_left)
                    if debug: print("code_right:", code_right)
                    if debug: print("alpha:", alpha)
                    assert f_code_folded == ((code_left + code_right)/2 + alpha * (code_left - code_right)/(2*coset)), f"failed to check fri, i: {i}, x0: {x0}, x1: {x1}, code_left: {code_left}, code_right: {code_right}, alpha: {alpha}, coset: {coset}"

                if i == 0:
                    assert verify_decommitment(x0, code_left, mp, proof['first_oracle']), "failed to check decommitment at first level"
                else:
                    assert verify_decommitment(x0, code_left, mp, proof['intermediate_oracles'][i - 1]), "failed to check decommitment at level " + str(i)

                num_vars_copy >>= 1
                q = x0


def rs_encode_single(m, alpha, c):
    k0 = len(m)
    code = [None] * (k0 * c)
    for i in range(k0 * c):
        # Compute f_m(alpha[i])
        code[i] = sum(m[j] * (alpha[i] ** j) for j in range(k0))
    return code


if __name__ == "__main__":
    from sage.all import *
    from field import magic
    from random import randint

    Fp = magic(GF(193))

    assert Fp.primitive_element() ** 192 == 1

    degree_bound = 8
    blow_up_factor = 4
    num_verifier_queries = 8

    assert is_power_of_two(degree_bound)

    evals = rs_encode_single([randint(0, 193) for _ in range(degree_bound)], [Fp.primitive_element() ** (i * 192 // (degree_bound * 2 ** blow_up_factor)) for i in range(degree_bound * 2 ** blow_up_factor)], 2 ** blow_up_factor)
    proof = FRI.prove_low_degree(evals, degree_bound, Fp.primitive_element() ** (192 // len(evals)), num_verifier_queries, debug=False)
    FRI.verify_low_degree(degree_bound, proof, Fp.primitive_element() ** (192 // len(evals)), num_verifier_queries, debug=False)
