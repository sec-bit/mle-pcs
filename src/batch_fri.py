from merkle import MerkleTree, verify_decommitment
from merlin.merlin_transcript import MerlinTranscript
from utils import from_bytes, log_2, is_power_of_two
from unipolynomial import UniPolynomial
from mmcs import MMCS
from hashlib import sha256

class BatchFRI:
    security_level = 128

    @classmethod
    def batch_commit(cls, evals, rate, domains, debug=False):
        if debug: print("evals:", evals)
        MMCS.configure(lambda x: sha256(str(x).encode('ascii')).digest(), lambda x: sha256(sha256(x[0]).digest() + sha256(x[1]).digest()).digest(), b'default_digest')
        sorted_evals = sorted(evals, key=lambda x: len(x), reverse=True)
        coeffs = [UniPolynomial.compute_coeffs_from_evals_fast(sorted_evals[i], domains[i][:len(sorted_evals[i])]) for i in range(len(sorted_evals))]
        print("coeffs:", coeffs, ", domains:", domains)
        codes = [cls.rs_encode_single(coeffs[i], domains[i], rate) for i in range(len(coeffs))]
        if debug: print("codes:", codes)
        if debug: assert evals == [codes[i][:len(evals[i])] for i in range(len(evals))], f"evals: {evals}, codes: {codes}"
        return MMCS.commit(codes, debug=False), codes

    @classmethod
    def batch_prove(cls, codes, code_tree, vals, point, domains, rate, degree_bound, gen, transcript, debug=False):
        assert len(domains[0]) == degree_bound * rate, f"domain: {domains[0]}, degree_bound: {degree_bound}, rate: {rate}"
        assert len(vals) == len(codes), f"len(vals): {len(vals)}, len(codes): {len(codes)}"
        assert isinstance(transcript, MerlinTranscript), f"transcript: {transcript}"

        # quotients = [[(codes[j][i] - vals[j]) / (domains[j][i] - point) for i in range(len(codes[j]))] for j in range(len(codes))]
        quotients = []
        for j in range(len(codes)):
            quotients.append([])
            for i in range(len(codes[j])):
                if debug: print("codes[j][i]:", codes[j][i], "vals[j]:", vals[j], "domains[j][i]:", domains[j][i], "point:", point, "quotient:", (codes[j][i] - vals[j]) / (domains[j][i] - point))
                quotients[-1].append((codes[j][i] - vals[j]) / (domains[j][i] - point))

        if debug:
            # print("point:", point)
            # for i in range(len(quotients)):
            #     FRI.prove_low_degree(quotients[i], rate, degree_bound >> i, gen ** (1 << i), 1, MerlinTranscript(b'test'), debug=False)
            #     print("codes:", codes[i])
            #     print("vals:", vals[i])
            #     print("domains:", domains[i])
            #     print("quotients:", quotients[i])

            coeffs = UniPolynomial.compute_coeffs_from_evals_fast(quotients[0], domains[0]) + [0]
            print("domain:", domains[0])
            print("coeffs:", coeffs)
            print("quotients[0]:", quotients[0])
            encoded = cls.rs_encode_single(coeffs[:len(quotients[0]) // rate], domains[0], rate)
            assert encoded == quotients[0], f"failed to rs encode, encoded: {encoded}, quotients[0]: {quotients[0]}"

        quotients_commitment = MMCS.commit(quotients, debug=False)
        layers = quotients_commitment['layers']
        transcript.append_message(b"quotient", layers[-1][0])
        for i in range(len(vals)):
            transcript.append_message(b"value at z", str(vals[i]).encode('ascii'))

        z = from_bytes(transcript.challenge_bytes(b"z", 4))
        code_at_z, commit_proof, commit_root = MMCS.open(z, code_tree, debug=debug)
        quotient_at_z_proof = MMCS.open(z, quotients_commitment, debug=False)

        if debug: print("prover")
        if debug: print("z:", z)
        if debug: print("code_at_z:", code_at_z)
        if debug: print("commit_proof:", commit_proof)
        if debug: print("commit_root:", commit_root)
        if debug: MMCS.verify(z, code_at_z, commit_proof, commit_root, debug=False)

        num_verifier_queries = cls.security_level // log_2(rate)
        if cls.security_level % log_2(rate) != 0:
            num_verifier_queries += 1

        low_degree_proof = cls.prove_low_degree(quotients, rate, degree_bound, gen, num_verifier_queries, transcript, debug)

        return {
            'low_degree_proof': low_degree_proof,
            'code_commitment': commit_root,
            'code_at_z_proof': commit_proof,
            'quotient_at_z_proof': quotient_at_z_proof,
            'code_at_z': code_at_z,
            'degree_bound': degree_bound,
        }
    
    @classmethod
    def batch_verify(cls, degree_bound, rate, proof, vals, domains, gen, shift, transcript, debug=False):
        assert degree_bound >= proof['degree_bound']
        degree_bound = proof['degree_bound']

        assert isinstance(transcript, MerlinTranscript), f"transcript: {transcript}"

        low_degree_proof = proof['low_degree_proof']
        code_commitment = proof['code_commitment']
        code_at_z_proof = proof['code_at_z_proof']
        quotient_at_z_proof = proof['quotient_at_z_proof']
        quotient_at_z = quotient_at_z_proof[0]
        quotient_proof = quotient_at_z_proof[1]
        quotient_commitment = quotient_at_z_proof[2]
        code_at_z = proof['code_at_z']

        transcript.append_message(b"code", code_commitment)
        point = int.from_bytes(transcript.challenge_bytes(b"point", 4), 'big')
        point = gen ** point * shift
        transcript.append_message(b"quotient", quotient_commitment)

        for v in vals:
            transcript.append_message(b"value at z", str(v).encode('ascii'))

        z = from_bytes(transcript.challenge_bytes(b"z", 4))
        
        if debug: print("verifier")
        if debug: print("z:", z)
        if debug: print("code_at_z:", code_at_z)
        if debug: print("code_at_z_proof:", code_at_z_proof)
        if debug: print("code_commitment:", code_commitment)
        if debug: print("quotient_at_z:", quotient_at_z)
        if debug: print("quotient_at_z_openings:", quotient_at_z)
        if debug: print("quotient_at_z_proof:", quotient_proof)
        if debug: print("quotient_commitment:", quotient_commitment)
        MMCS.verify(z, code_at_z, code_at_z_proof, code_commitment, debug=False)
        MMCS.verify(z, quotient_at_z, quotient_proof, quotient_commitment, debug=False)

        for i, (c, q, v) in enumerate(zip(code_at_z, quotient_at_z, vals)):
            assert c - v == q * (domains[i][z >> (32 - log_2(degree_bound * rate) + i)] - point), f"failed to verify batch fri, z: {z >> (32 - log_2(degree_bound * rate) - i)}, c: {c}, v: {v}, q: {q}, point: {point}, domain[z]: {domains[i][z >> (32 - log_2(degree_bound * rate) - i)]}"

        num_verifier_queries = cls.security_level // log_2(rate)
        if cls.security_level % log_2(rate) != 0:
            num_verifier_queries += 1

        cls.verify_low_degree(degree_bound, rate, low_degree_proof, gen, num_verifier_queries, transcript, debug)

    @classmethod
    def prove_low_degree(cls, evals, rate, degree_bound, gen, num_verifier_queries, transcript, debug=False):
        assert is_power_of_two(degree_bound)
        assert len(evals[0]) == degree_bound * rate, f"evals[0]: {evals[0]}, degree_bound: {degree_bound}, rate: {rate}"
        assert isinstance(transcript, MerlinTranscript), f"transcript: {transcript}"

        evals_copy = evals

        folded = evals[0]
        first_tree = MerkleTree(folded)
        transcript.append_message(b"first_oracle", first_tree.root.encode('ascii'))

        alpha = transcript.challenge_bytes(b"alpha", 4)
        alpha = from_bytes(alpha)

        trees = []
        tree_evals = []
        for i in range(log_2(degree_bound)):
            if debug: print("folded:", folded)
            if debug: print("alpha:", alpha)
            if debug: print("generator:", gen)
            if debug: print("domain:", [gen ** i for i in range(len(folded) // 2)])
            if debug: print("evals[i + 1]:", evals[i + 1])
            folded = cls.fold(folded, alpha, gen)
            assert len(folded) == len(evals[i + 1]), f"len(folded): {len(folded)}, len(evals[i + 1]): {len(evals[i + 1])}"
            folded = [x + y for x, y in zip(folded, evals[i + 1])]
            if i != log_2(degree_bound) - 1:
                tree = MerkleTree(folded)
                trees.append(tree)
                tree_evals.append(folded)

                transcript.append_message(b"oracle", tree.root.encode('ascii'))
                alpha = transcript.challenge_bytes(b"alpha", 4)
                alpha = from_bytes(alpha)

            gen *= gen

        if debug:
            assert len(folded) == rate, f"folded: {folded}, rate: {rate}"
            for i in range(len(folded)):
                if i != 0:
                    assert folded[i] == folded[0], f"folded: {folded}"

        # query phase
        # assert len(evals_copy) == degree_bound * rate, f"evals_copy: {evals_copy}, degree_bound: {degree_bound}, rate: {rate}"
        query_paths, merkle_paths = cls.query_phase(transcript, first_tree, evals_copy, trees, tree_evals, degree_bound * rate, num_verifier_queries, debug)

        return {
            'query_paths': query_paths,
            'merkle_paths': merkle_paths,
            'first_oracle': first_tree.root,
            'intermediate_oracles': [tree.root for tree in trees],
            'degree_bound': degree_bound,
            'final_value': folded[0],
        }
    
    @classmethod
    def verify_low_degree(cls, degree_bound, rate, proof, gen, num_verifier_queries, transcript, debug=False):
        log_degree_bound = log_2(degree_bound)
        log_evals = log_2(degree_bound * rate)
        T = [[(gen**(2 ** j)) ** i for i in range(2 ** (log_evals - j - 1))] for j in range(0, log_evals)]
        if debug: print("T:", T)
        cls.verify_queries(proof, log_degree_bound, degree_bound * rate, num_verifier_queries, T, transcript, debug)

    @classmethod
    def query_phase(cls, transcript: MerlinTranscript, first_tree: MerkleTree, evals: list, trees: list, oracles: list, num_vars, num_verifier_queries, debug=False):
        queries = [from_bytes(transcript.challenge_bytes(b"queries", 4)) % num_vars for _ in range(num_verifier_queries)]
        if debug: print("queries:", queries)

        query_paths = []
        # query paths
        for q in queries:
            num_vars_copy = num_vars
            cur_path = []
            indices = []
            reduced_openings = []

            if debug: print("first_oracle:", evals[0])
            cur_path.append(evals[0][q ^ (num_vars_copy // 2)])
            reduced_openings.append(evals[0][q])
            indices.append(q)
            q = min(q, q ^ (num_vars_copy // 2))
            num_vars_copy >>= 1

            for i, oracle in enumerate(oracles):
                if debug: print("oracle:", oracle)
                cur_path.append(oracle[q ^ (num_vars_copy // 2)])
                reduced_openings.append(evals[i+1][q])
                indices.append(q)
                q = min(q, q ^ (num_vars_copy // 2))
                num_vars_copy >>= 1
            
            reduced_openings.append(evals[-1][q])
            
            query_paths.append((cur_path, indices, reduced_openings))

        # merkle paths
        merkle_paths = []
        for _, indices, _ in query_paths:
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
                    if debug: print("commit:", cur_tree.root)
                    if debug: print("idx:", idx)
            merkle_paths.append(cur_query_paths)

        return query_paths, merkle_paths
    
    @classmethod
    def verify_queries(cls, proof, k, num_vars, num_verifier_queries, T, transcript, debug=False):
        first_oracle = proof['first_oracle']
        intermediate_oracles = proof['intermediate_oracles']
        query_paths = proof['query_paths']
        merkle_paths = proof['merkle_paths']

        transcript.append_message(b"first_oracle", bytes(first_oracle, 'ascii'))
        alpha = transcript.challenge_bytes(b"alpha", 4)
        alpha = from_bytes(alpha)

        fold_challenges = [alpha]
        if debug: print("intermediate_oracles:", intermediate_oracles)
        if debug: print("k:", k)
        for i in range(k-1):
            transcript.append_message(bytes(f'oracle', 'ascii'), bytes(intermediate_oracles[i], 'ascii'))
            fold_challenges.append(from_bytes(transcript.challenge_bytes(b"alpha", 4)))

        queries = [from_bytes(transcript.challenge_bytes(b"queries", 4)) % num_vars for _ in range(num_verifier_queries)]

        # query loop
        for q, (cur_path, indices, ros), mps in zip(queries, query_paths, merkle_paths):
            if debug: print("cur_path:", cur_path)
            num_vars_copy = num_vars
            folded = 0

            # fold loop
            for i in range(k):
                if debug: print("q:", q)
                if debug: print("num_vars_copy:", num_vars_copy)
                if debug: print("ros[i]:", ros[i])
                if debug: assert indices[i] == q, f"indices: {indices}, q: {q}"
                folded += ros[i]

                if i == 0:
                    assert verify_decommitment(q, folded, mps[i], first_oracle), "failed to verify decommitment at first level"
                else:
                    assert verify_decommitment(q, folded, mps[i], intermediate_oracles[i - 1]), f"failed to verify decommitment at level {i}, folded: {folded}, mp: {mps[i]}, intermediate_oracles[i - 1]: {intermediate_oracles[i - 1]}"

                table = T[i]
                sibling = q ^ (num_vars_copy // 2)
                idx = min(q, sibling)

                alpha = fold_challenges[i]
                evals = [cur_path[i]] * 2
                evals[q // (num_vars_copy // 2)] = folded
                if debug: print("evals[0]:", evals[0], "evals[1]:", evals[1], "alpha:", alpha, "table[idx]:", table[idx])
                folded = (evals[0] + evals[1])/2 + alpha * (evals[0] - evals[1])/(2 * table[idx])

                num_vars_copy >>= 1
                q = idx

            assert proof['final_value'] == folded + ros[-1], f"failed to verify batch fri, final_value: {proof['final_value']}, folded: {folded}"

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

