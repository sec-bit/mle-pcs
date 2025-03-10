from merkle import MerkleTree, verify_decommitment
from merlin.merlin_transcript import MerlinTranscript
from utils import from_bytes, log_2, is_power_of_two
from unipolynomial import UniPolynomial
from mmcs import MMCS
from hashlib import sha256
from fri import FRI

class BatchFRI:
    security_level = 128

    @classmethod
    def batch_commit(cls, evals, rate, domains, one=1, debug=False):
        if debug: print("evals:", evals)
        MMCS.configure(lambda x: sha256(str(x).encode('ascii')).digest(), lambda x: sha256(sha256(x[0]).digest() + sha256(x[1]).digest()).digest(), b'default_digest')
        sorted_evals = sorted(evals, key=lambda x: len(x), reverse=True)

        coeffs = [UniPolynomial.ntt_coeffs_from_evals(sorted_evals[i], log_2(len(sorted_evals[i])), domains[i][1] ** rate, one) for i in range(len(sorted_evals))]
        if debug: print("coeffs:", coeffs, ", domains:", domains)

        codes = [UniPolynomial.ntt_evals_from_coeffs(coeffs[i] + [0] * (len(sorted_evals[i]) * rate - len(coeffs[i])), log_2(len(sorted_evals[i]) * rate), domains[i][1]) for i in range(len(sorted_evals))]
        if debug: print("codes:", codes)
        if debug: assert evals == [codes[i][:len(evals[i])] for i in range(len(evals))], f"evals: {evals}, codes: {codes}"
        return MMCS.commit(codes, debug=False), codes

    @classmethod
    def batch_prove(cls, codes, code_tree, vals, point, domains, rate, degree_bound, gen, transcript, one=1, debug=False):
        assert len(domains[0]) == degree_bound * rate, f"domain: {domains[0]}, degree_bound: {degree_bound}, rate: {rate}"
        assert len(vals) == len(codes), f"len(vals): {len(vals)}, len(codes): {len(codes)}"
        assert isinstance(transcript, MerlinTranscript), f"transcript: {transcript}"

        quotients = []
        for i in range(len(codes)):
            tmp = []
            for j in range(len(codes[i])):
                # print("codes[i][j]:", codes[i][j], "vals[i]:", vals[i], "domains[i][j]:", domains[i][j], "point:", point)
                tmp.append((codes[i][j] - vals[i]) / (domains[i][j] - point))
            quotients.append(tmp)

        num_verifier_queries = cls.security_level // log_2(rate)
        if cls.security_level % log_2(rate) != 0:
            num_verifier_queries += 1

        low_degree_proof = cls.prove_low_degree(codes, code_tree, quotients, rate, degree_bound, gen, num_verifier_queries, transcript, one, debug)

        return {
            'low_degree_proof': low_degree_proof,
            'code_commitment': code_tree['layers'][-1][0],
            'degree_bound': degree_bound,
        }
    
    @classmethod
    def batch_verify(cls, degree_bound, rate, proof, point, vals, gen, one, transcript, debug=False):
        assert degree_bound >= proof['degree_bound']
        degree_bound = proof['degree_bound']

        assert isinstance(transcript, MerlinTranscript), f"transcript: {transcript}"

        low_degree_proof = proof['low_degree_proof']

        num_verifier_queries = cls.security_level // log_2(rate)
        if cls.security_level % log_2(rate) != 0:
            num_verifier_queries += 1

        cls.verify_low_degree(degree_bound, rate, low_degree_proof, gen, num_verifier_queries, point, vals, one, transcript, debug)

    @classmethod
    def prove_low_degree(cls, codes, code_tree, quotients, rate, degree_bound, gen, num_verifier_queries, transcript, one=1, debug=False):
        assert is_power_of_two(degree_bound)
        assert len(quotients[0]) == degree_bound * rate, f"evals[0]: {quotients[0]}, degree_bound: {degree_bound}, rate: {rate}"
        assert isinstance(transcript, MerlinTranscript), f"transcript: {transcript}"

        folded = [one - one] * len(quotients[0])
        if debug:
            coeffs = UniPolynomial.compute_coeffs_from_evals_fast(folded, [gen ** i for i in range(len(folded))])
            for i in range(len(coeffs), len(folded) // rate):
                assert coeffs[i] == one - one, f"coeffs: {coeffs}, folded: {folded}, rate: {rate}"
        first_tree = code_tree

        trees = []
        tree_evals = []
        for i in range(log_2(degree_bound) - 1):

            lambda_ = one * from_bytes(transcript.challenge_bytes(b"lambda", 4))

            alpha = transcript.challenge_bytes(b"alpha", 4)
            alpha = from_bytes(alpha)

            if debug: print("folded:", folded)
            if debug: print("alpha:", alpha)
            if debug: print("generator:", gen)
            if debug: print("domain:", [gen ** i for i in range(len(folded) // 2)])
            if debug: print("evals[i + 1]:", quotients[i + 1])
            folded = [x + (one + lambda_ * gen ** i) * y for x, y in zip(folded, quotients[i])]
            tree = MerkleTree(folded)
            trees.append(tree)
            tree_evals.append(folded)
            folded = cls.fold(folded, alpha, gen)
            if debug:
                coeffs1 = UniPolynomial.compute_coeffs_from_evals_fast(folded, [gen ** (2 * i) for i in range(len(folded))])
                coeffs2 = UniPolynomial.compute_coeffs_from_evals_fast(quotients[i + 1], [gen ** (2 * i) for i in range(len(quotients[i + 1]))])
                for j in range(len(coeffs1), len(folded) // rate):
                    assert coeffs1[j] == one - one, f"i: {i}, coeffs1: {coeffs1}, folded: {folded}, rate: {rate}"
                for j in range(len(coeffs2), len(quotients[i + 1]) // rate):
                    assert coeffs2[j] == one - one, f"i: {i}, coeffs2: {coeffs2}, evals[i + 1]: {quotients[i + 1]}, rate: {rate}"
            assert len(folded) == len(quotients[i + 1]), f"len(folded): {len(folded)}, len(evals[i + 1]): {len(quotients[i + 1])}"

            transcript.append_message(b"oracle", tree.root.encode('ascii'))

            gen *= gen

        if debug:
            assert len(folded) == rate - 1, f"folded: {folded}, rate: {rate}"
            for i in range(len(folded)):
                if i != 0:
                    assert folded[i] == folded[0], f"folded: {folded}"

        # query phase
        # assert len(evals_copy) == degree_bound * rate, f"evals_copy: {evals_copy}, degree_bound: {degree_bound}, rate: {rate}"
        query_paths, merkle_paths, first_merkle_paths = cls.query_phase(transcript, first_tree, codes, trees, tree_evals, degree_bound * rate, num_verifier_queries, debug)

        return {
            'query_paths': query_paths,
            'merkle_paths': merkle_paths,
            'first_merkle_paths': first_merkle_paths,
            'intermediate_oracles': [tree.root for tree in trees],
            'degree_bound': degree_bound,
            'final_value': folded[0],
            'first_oracle': first_tree['layers'][-1][0],
        }
    
    @classmethod
    def verify_low_degree(cls, degree_bound, rate, proof, gen, num_verifier_queries, point, vals, one, transcript, debug=False):
        log_degree_bound = log_2(degree_bound)
        log_evals = log_2(degree_bound * rate)
        T = [[(gen**(2 ** j)) ** i for i in range(2 ** (log_evals - j - 1))] for j in range(0, log_evals)]
        if debug: print("T:", T)
        cls.verify_queries(proof, log_degree_bound, degree_bound * rate, num_verifier_queries, T, point, vals, one, transcript, debug)

    @classmethod
    def query_phase(cls, transcript: MerlinTranscript, first_tree, codes: list, quotients: list, trees: list, oracles: list, num_vars, num_verifier_queries, debug=False):
        num_vars = len(codes[0])
        queries = [from_bytes(transcript.challenge_bytes(b"queries", 4)) % (num_vars // 2) for _ in range(num_verifier_queries)]
        if debug: print("queries:", queries)

        query_paths = []
        # query paths
        for q in queries:
            num_vars_copy = num_vars
            cur_path = []
            indices = []
            reduced_openings = []

            for i in range(len(oracles)):
                next_q = min(q, q ^ (num_vars_copy // 2))
                if debug: print("oracle:", oracles[i])
                assert next_q < len(oracles[i]), f"q: {q}, oracle: {oracles[i]}, num_vars_copy: {num_vars_copy}"
                assert num_vars_copy == len(codes[i]), f"num_vars_copy: {num_vars_copy}, len(codes[i]): {len(codes[i])}"
                cur_path.append(oracles[i][next_q])
                reduced_openings.append(codes[i][q])
                indices.append(next_q)
                q = next_q
                num_vars_copy >>= 1

            reduced_openings.append(codes[-2][q])
            
            query_paths.append((cur_path, indices, reduced_openings))

        # merkle paths
        merkle_paths = []
        first_merkle_paths = []
        for q, (cur_path, indices, reduced_openings) in zip(queries, query_paths):
            mmcs_proof = MMCS.open(q, first_tree, debug)
            first_merkle_paths.append(mmcs_proof[1])
            if debug:
                num_vars_copy = num_vars
                openings = []
                idx = q
                for i in range(len(codes) - 1):
                    assert idx < len(codes[i]), f"idx: {idx}, len(codes[i]): {len(codes[i])}"
                    assert num_vars_copy == len(codes[i]), f"num_vars_copy: {num_vars_copy}, len(codes[i]): {len(codes[i])}"
                    openings.append((codes[i][idx]))
                    idx = min(idx, idx ^ (num_vars_copy // 2))
                    num_vars_copy >>= 1
                assert openings == reduced_openings, f"openings: {openings}, reduced_openings: {reduced_openings}"
                assert mmcs_proof[0] == reduced_openings + [codes[-1][0]], f"mmcs_proof[0]: {mmcs_proof[0]}, openings: {openings}, codes[-1][0]: {codes[-1][0]}"
                assert mmcs_proof[2] == first_tree['layers'][-1][0], f"mmcs_proof[2]: {mmcs_proof[2]}, first_tree['layers'][-1][0]: {first_tree['layers'][-1][0]}"
                print("prover MMCS.verify:", q, reduced_openings + [codes[-1][0]], mmcs_proof[1], first_tree['layers'][-1][0])
                MMCS.verify(q, reduced_openings + [codes[-1][0]], mmcs_proof[1], first_tree['layers'][-1][0], debug)

        for _, indices, _ in query_paths:
            cur_query_paths = []
            for i, idx in enumerate(indices):
                cur_tree = trees[i]
                assert isinstance(cur_tree, MerkleTree)
                cur_query_paths.append(cur_tree.get_authentication_path(idx))
                verify_decommitment(idx, oracles[i][idx], cur_query_paths[-1], cur_tree.root)
                # print("prover verify_decommitment:", idx, oracles[i][idx], cur_query_paths[-1], cur_tree.root)
                if debug: print("mp:", cur_query_paths[-1])
                if debug: print("commit:", cur_tree.root)
                if debug: print("idx:", idx)
            merkle_paths.append(cur_query_paths)

        return query_paths, merkle_paths, first_merkle_paths
    
    @classmethod
    def verify_queries(cls, proof, k, num_vars, num_verifier_queries, T, point, vals, one, transcript, debug=False):
        first_oracle = proof['first_oracle']
        intermediate_oracles = proof['intermediate_oracles']
        query_paths = proof['query_paths']
        merkle_paths = proof['merkle_paths']
        first_merkle_paths = proof['first_merkle_paths']

        lambda_ = one * from_bytes(transcript.challenge_bytes(b"lambda", 4))

        fold_challenges = []
        if debug: print("intermediate_oracles:", intermediate_oracles)
        if debug: print("k:", k)
        for i in range(k-1):
            fold_challenges.append(from_bytes(transcript.challenge_bytes(b"alpha", 4)))
            transcript.append_message(bytes(f'oracle', 'ascii'), bytes(intermediate_oracles[i], 'ascii'))

        queries = [from_bytes(transcript.challenge_bytes(b"queries", 4)) % num_vars for _ in range(num_verifier_queries)]

        # query loop
        for q, (cur_path, indices, ros), mps, fmp in zip(queries, query_paths, merkle_paths, first_merkle_paths):
            if debug: print("cur_path:", cur_path)
            num_vars_copy = num_vars // 2
            folded = 0

            q = min(q, q ^ num_vars_copy)
            MMCS.verify(q, ros + [vals[-1]], fmp, first_oracle, debug)

            # fold loop
            for i in range(k-1):
                if debug: print("q:", q)
                if debug: print("num_vars_copy:", num_vars_copy)
                if debug: print("ros[i]:", ros[i])
                if debug: assert indices[i] == q, f"indices: {indices}, q: {q}"
                # print("ros[i]:", ros[i], "vals[i]:", vals[i], "T[i][q]:", T[i][q], "point:", point)
                cur_quotient = (one + lambda_ * T[i][q]) * (ros[i] - vals[i]) / (T[i][q] - point)
                folded += cur_quotient

                table = T[i]
                sibling = q ^ (num_vars_copy // 2)
                idx = min(q, sibling)

                alpha = fold_challenges[i]
                evals = [cur_path[i]] * 2
                evals[q // (num_vars_copy // 2)] = folded
                folded = (evals[0] + evals[1])/2 + alpha * (evals[0] - evals[1])/(2 * table[idx])
                assert verify_decommitment(q, folded, mps[i], intermediate_oracles[i]), f"failed to verify decommitment at level {i}, folded: {folded}, mp: {mps[i]}, intermediate_oracles[i - 1]: {intermediate_oracles[i - 1]}"

                num_vars_copy >>= 1
                q = idx

            assert proof['final_value'] == folded, f"failed to verify batch fri, final_value: {proof['final_value']}, folded: {folded}"

    # f(x) = f0(x^2) + x * f1(x^2)
    # and half degree interpolation is
    # f'(x^2) = f0(x^2) + alpha * f1(x^2), and it can be achieved by just adding up two adjustent (adjustment?)
    # coefficients in the monomial form
    # if we would want to try to get the same result, one can observe that
    # f0(x^2) = (f(x) + f(-x)) / 2
    # f1(x^2) = (f(x) - f(-x)) / 2x
    @classmethod
    def fold(cls, evals, alpha, g, debug=False):
        assert len(evals) % 2 == 0

        half = len(evals) // 2
        f0_evals = [(evals[i] + evals[half + i]) / 2 for i in range(half)]
        f1_evals = [(evals[i] - evals[half + i]) / (2 * g ** i) for i in range(half)]

        if debug:
            x = g ** 5
            f_x = UniPolynomial.uni_eval_from_evals(evals, x, [g ** i for i in range(len(evals))])
            f0_x = UniPolynomial.uni_eval_from_evals(f0_evals, x ** 2, [(g ** 2) ** i for i in range(len(f0_evals))])
            f1_x = UniPolynomial.uni_eval_from_evals(f1_evals, x ** 2, [(g ** 2) ** i for i in range(len(f1_evals))])
            assert f_x == f0_x + x * f1_x, f"failed to fold, f_x: {f_x}, f0_x: {f0_x}, f1_x: {f1_x}, alpha: {alpha}"

        return [x + alpha * y for x, y in zip(f0_evals, f1_evals)]

    @staticmethod
    def rs_encode_single(m, alpha, c):
        k0 = len(m)
        code = [None] * (k0 * c)
        for i in range(k0 * c):
            # Compute f_m(alpha[i])
            code[i] = sum(m[j] * (alpha[i] ** j) for j in range(k0))
        return code

