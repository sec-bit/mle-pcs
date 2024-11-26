from merkle import MerkleTree, verify_decommitment
from merlin.merlin_transcript import MerlinTranscript
from utils import from_bytes, log_2, is_power_of_two
from unipolynomial import UniPolynomial

class FRI:
    security_level = 128

    @classmethod
    def commit(cls, evals, rate, domain, debug=False):
        if debug: print("evals:", evals)
        N = len(evals)
        assert is_power_of_two(N)
        degree_bound = N
        if debug: print("degree_bound:", degree_bound)
        coeffs = UniPolynomial.compute_coeffs_from_evals_fast(evals, domain[:N])
        if debug: print("coeffs:", coeffs)
        code = cls.rs_encode_single(coeffs, domain, rate)
        if debug: print("code:", code)
        assert len(code) == N * rate, f"code: {code}, degree_bound: {degree_bound}, rate: {rate}"
        
        return MerkleTree(code), code

    @classmethod
    def prove(cls, code, code_tree, val, point, domain, rate, degree_bound, gen, transcript, debug=False):
        if debug: print("val:", val)
        assert len(domain) == degree_bound * rate, f"domain: {domain}, degree_bound: {degree_bound}, rate: {rate}"
        assert isinstance(transcript, MerlinTranscript), f"transcript: {transcript}"
        
        quotient = [(code[i] - val) / (domain[i] - point) for i in range(len(code))]
        
        quotient_tree = MerkleTree(quotient)
        transcript.append_message(b"quotient", quotient_tree.root.encode('ascii'))
        transcript.append_message(b"value at z", str(val).encode('ascii'))

        z = from_bytes(transcript.challenge_bytes(b"z", 4)) % len(code)
        code_at_z_proof = code_tree.get_authentication_path(z)
        quotient_at_z_proof = quotient_tree.get_authentication_path(z)

        if debug:
            print('z:', z)
            print('code[z]:', code[z])
            print('quotient[z]:', quotient[z])
            print('domain[z]:', domain[z])
            print('point:', point)
            print('value:', val)
            assert code[z] - val == quotient[z] * (domain[z] - point), \
                "failed to generate quotient, code: {}, quotient: {}, val: {}, z: {}, point: {}"\
                    .format(code, quotient, val, z, point)

        num_verifier_queries = cls.security_level // log_2(rate)
        if cls.security_level % log_2(rate) != 0:
            num_verifier_queries += 1

        low_degree_proof = cls.prove_low_degree(quotient, rate, degree_bound, gen, num_verifier_queries, transcript, debug)

        return {
            'low_degree_proof': low_degree_proof,
            'code_commitment': code_tree.root,
            'quotient_commitment': quotient_tree.root,
            'code_at_z_proof': code_at_z_proof,
            'quotient_at_z_proof': quotient_at_z_proof,
            'code_at_z': code[z],
            'quotient_at_z': quotient[z],
            'degree_bound': degree_bound,
        }

    @classmethod
    def verify(cls, degree_bound, rate, proof, point, value, domain, gen, transcript, debug=False):

        assert degree_bound >= proof['degree_bound']
        degree_bound = proof['degree_bound']

        assert isinstance(transcript, MerlinTranscript), f"transcript: {transcript}"

        code_commitment = proof['code_commitment']
        quotient_commitment = proof['quotient_commitment']

        transcript.append_message(b"code", code_commitment.encode('ascii'))
        transcript.append_message(b"quotient", quotient_commitment.encode('ascii'))
        transcript.append_message(b"value at z", str(value).encode('ascii'))

        z = from_bytes(transcript.challenge_bytes(b"z", 4)) % (degree_bound * rate)
        code_at_z_proof = proof['code_at_z_proof']
        quotient_at_z_proof = proof['quotient_at_z_proof']

        if debug:
            print('z: ', z)
            print('code_at_z: ', proof['code_at_z'])
            print('quotient_at_z: ', proof['quotient_at_z'])
            print('point:', point)
            print('value:', value)

        assert verify_decommitment(z, proof['code_at_z'], code_at_z_proof, code_commitment), f"failed to check decommitment at code_at_z, z: {z}, code_at_z: {proof['code_at_z']}, code_commitment: {code_commitment}"
        assert verify_decommitment(z, proof['quotient_at_z'], quotient_at_z_proof, quotient_commitment), f"failed to check decommitment at quotient_at_z, z: {z}, quotient_at_z: {proof['quotient_at_z']}, quotient_commitment: {quotient_commitment}"

        assert proof['code_at_z'] - value == proof['quotient_at_z'] * (domain[z] - point)

        num_verifier_queries = cls.security_level // log_2(rate)
        if cls.security_level % log_2(rate) != 0:
            num_verifier_queries += 1
        
        cls.verify_low_degree(degree_bound, rate, proof['low_degree_proof'], gen, num_verifier_queries, transcript, debug)

    @staticmethod
    def prove_low_degree(evals, rate, degree_bound, gen, num_verifier_queries, transcript, debug=False):
        assert is_power_of_two(degree_bound)

        first_tree = MerkleTree(evals)
        evals_copy = evals
        transcript.append_message(b"first_oracle", first_tree.root.encode('ascii'))

        alpha = transcript.challenge_bytes(b"alpha", 4)
        alpha = from_bytes(alpha)

        trees = []
        tree_evals = []
        for _ in range(log_2(degree_bound)):
            if debug: print("evals:", evals)
            if debug: print("alpha:", alpha)
            if debug: print("generator:", gen)
            evals = FRI.fold(evals, alpha, gen)
            tree = MerkleTree(evals)
            trees.append(tree)
            tree_evals.append(evals)

            transcript.append_message(b"oracle", tree.root.encode('ascii'))
            alpha = transcript.challenge_bytes(b"alpha", 4)
            alpha = from_bytes(alpha)

            gen *= gen

        if debug:
            assert len(evals) == rate, f"evals: {evals}, rate: {rate}"
            for i in range(len(evals)):
                if i != 0:
                    assert evals[i] == evals[0], f"evals: {evals}"

        # query phase
        assert len(evals_copy) == degree_bound * rate, f"evals_copy: {evals_copy}, degree_bound: {degree_bound}, rate: {rate}"
        query_paths, merkle_paths = FRI.query_phase(transcript, first_tree, evals_copy, trees, tree_evals, degree_bound * rate, num_verifier_queries, debug)

        return {
            'query_paths': query_paths,
            'merkle_paths': merkle_paths,
            'first_oracle': first_tree.root,
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
    def fold(evals, alpha, g, debug=False):
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
    def verify_low_degree(degree_bound, rate, proof, gen, num_verifier_queries, transcript, debug=False):
        log_degree_bound = log_2(degree_bound)
        log_evals = log_2(degree_bound * rate)
        T = [[(gen**(2 ** j)) ** i for i in range(2 ** (log_evals - j - 1))] for j in range(0, log_evals)]
        if debug: print("T:", T)
        FRI.verify_queries(proof, log_degree_bound, degree_bound * rate, num_verifier_queries, T, transcript, debug)

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
    def verify_queries(proof, k, num_vars, num_verifier_queries, T, transcript, debug=False):
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

                table = T[i]
                if debug: print("table:", table)
                if i != len(mps) - 1:
                    f_code_folded = cur_path[i + 1][0 if x0 < num_vars_copy / 4 else 1]
                    alpha = fold_challenges[i]
                    if debug: assert x0 < len(table), f"x0: {x0}, table: {table}"
                    if debug: print("f_code_folded:", f_code_folded)
                    if debug: print("expected:", ((code_left + code_right)/2 + alpha * (code_left - code_right)/(2*table[x0])))
                    if debug: print("code_left:", code_left)
                    if debug: print("code_right:", code_right)
                    if debug: print("alpha:", alpha)
                    assert f_code_folded == (code_left + code_right)/2 + alpha * (code_left - code_right)/(2*table[x0]), f"failed to check fri, i: {i}, x0: {x0}, x1: {x1}, code_left: {code_left}, code_right: {code_right}, alpha: {alpha}, generator: {table}"
                else:
                    assert proof["final_value"] == (code_left + code_right)/2 + alpha * (code_left - code_right)/(2*table[x0]), f"failed to check fri, i: {i}, x0: {x0}, x1: {x1}, code_left: {code_left}, code_right: {code_right}, alpha: {alpha}, generator: {table}, final_value: {proof['final_value']}"

                if i == 0:
                    assert verify_decommitment(x0, code_left, mp, proof['first_oracle']), "failed to check decommitment at first level"
                else:
                    assert verify_decommitment(x0, code_left, mp, proof['intermediate_oracles'][i - 1]), "failed to check decommitment at level " + str(i)

                num_vars_copy >>= 1
                q = x0

    @staticmethod
    def rs_encode_single(m, alpha, c):
        k0 = len(m)
        code = [None] * (k0 * c)
        for i in range(k0 * c):
            # Compute f_m(alpha[i])
            code[i] = sum(m[j] * (alpha[i] ** j) for j in range(k0))
        return code

