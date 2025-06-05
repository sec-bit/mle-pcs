import field
from random import randint
from mle2 import MLEPolynomial
from unipolynomial import UniPolynomial
from merkle import MerkleTree, verify_decommitment
from merlin.merlin_transcript import MerlinTranscript
from sage.all import *

Fp = GF(193)
var_names = ['X' + str(i) for i in range(2 ** 6)] + ['A' + str(i) for i in range(2 ** 8)]
R = PolynomialRing(Fp, var_names)
R.inject_variables()
variables = R.gens()
Xs = variables[: 2 ** 6]
As = variables[2 ** 6 :]
Fp = field.magic(Fp)

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
    assert len(m) % k0 == 0, "len(m): %d is not a multiple of k0: %d" % (len(m), k0)
    code = []
    for i in range(0, c*len(m), k0):
        for j in range(0, c):
            code += m[i:i+k0]
    return code

def rs_encode_single(m, alpha, c):
    """
    Perform Reed-Solomon encoding on a single chunk of the message.

    This function encodes a single polynomial (represented by its coefficients)
    by evaluating it at multiple points. It's a key component of the Reed-Solomon
    error correction scheme.

    Args:
        m (list): A list of coefficients representing the message polynomial f(x).
                  The length of this list is k0, where k0 is the degree of the 
                  polynomial plus one.
        alpha (list): A list of evaluation points where the polynomial f(x) will 
                      be evaluated. The length of this list is k0 * c.
        c (int): A scaling factor that determines the number of evaluation points 
                 per message coefficient. It should be an integer greater than 1.

    Returns:
        list: A list of length k0 * c containing the Reed-Solomon encoded values.
              Each element is the result of evaluating f(x) at a point in alpha.

    Example:
        >>> m = [1, 2, 3]  # represents f(x) = 1 + 2x + 3x^2
        >>> alpha = [0, 1, 2, 3, 4, 5]
        >>> c = 2
        >>> rs_encode_single(m, alpha, c)
        [1, 6, 17, 34, 57, 86]  # f(0) = 1, f(1) = 6, f(2) = 17, f(3) = 34, f(4) = 57, f(5) = 86
    """
    k0 = len(m)
    code = [None] * (k0 * c)
    for i in range(k0 * c): 
        # Compute f_m(alpha[i])
        code[i] = sum(m[j] * (alpha[i] ** j) for j in range(k0))
    return code

def rs_encode(m, k0, c):
    """
    Apply Reed-Solomon encoding to the entire message.

    This function divides the input message into chunks of size k0 and applies
    Reed-Solomon encoding to each chunk. It's used to create an error-correcting
    code for the entire message.

    Args:
        m (list): The entire message to be encoded, represented as a list of 
                  coefficients. The length of m must be a multiple of k0.
        k0 (int): The size of each message chunk (i.e., the number of coefficients 
                  per chunk). This determines the degree of the polynomials used 
                  for encoding.
        c (int): A scaling factor that determines the number of evaluation points 
                 per chunk.

    Returns:
        list: A list containing the Reed-Solomon encoded message. The length of 
              this list is len(m) * c.

    Raises:
        AssertionError: If the length of m is not a multiple of k0.

    Example:
        >>> m = [1, 2, 3, 4]
        >>> k0 = 2
        >>> c = 2
        >>> rs_encode(m, k0, c)
        [1, 3, 5, 7, 3, 7, 11, 15]
        # This represents two encoded chunks:
        # [1, 3, 5, 7] for [1, 2] and [3, 7, 11, 15] for [3, 4]
    """
    assert len(m) % k0 == 0, "len(m): %d is not a multiple of k0: %d" % (len(m), k0)
    code = []
    alpha = list(range(k0 * c)) # alpha = [0, 1, 2, ... , k0*c - 1]
    for i in range(0, c*len(m), k0):
        code += rs_encode_single(m[i:i+k0], alpha, c)
    return code

def basefold_encode(m, k0, depth, c, T, G0=rep_encode, debug=False):
    """
    Perform basefold encoding on the input message.

    This function encodes the input message `m` using the basefold encoding scheme with
    specified parameters. It divides `m` into chunks, applies an encoding function `G0`
    (default is repetition encoding), and iteratively combines chunks using transformation
    tables `T` over a given depth.

    Args:
        m (list): The input message to be encoded. Must have a length of `k0 * 2**depth`.
        k0 (int): The base chunk size for encoding.
        depth (int): The number of encoding rounds or the depth of the encoding process.
        c (int): The blowup factor determining the expansion of the code.
        T (list of lists): Transformation tables for each encoding depth. Each table
            must have a length equal to the current chunk size.
        G0 (callable, optional): The encoding function to apply to each chunk.
            Defaults to `rep_encode`.
        debug (bool, optional): If `True`, prints debug information during encoding.
            Defaults to `False`.

    Returns:
        list: The basefold encoded code as a list.

    Raises:
        AssertionError: If the length of `m` does not equal `k0 * 2**depth`.
        AssertionError: If the length of `T` does not equal `depth`.
        AssertionError: If the length of a transformation table does not match the current
            chunk size during encoding.
    """
    if debug: print(">>> basefold_encode: m={}, k0={}, d={}, blowup_factor={}, T={}".format(m, k0, depth, c, T))
    kd = k0 * 2 ** depth
    blowup_factor = c
    assert len(m) == kd, "len(m): %d != kd: %d" % (len(m), kd)
    assert len(T) == depth, "len(T): %d != depth: %d" % (len(T), depth)
     
    chunk_size = k0
    chunk_num = 2 ** depth
    
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
        table = T[i]
        assert len(table) == chunk_size, "table[{}] != chunk_size, len(table)={}, chunk_size={})".format(i, len(table), chunk_size)
        if debug: print(">>> basefold_encode: table=", table)
        for c in range(0, chunk_num, 2):
            left  = code[    c*chunk_size : (c+1)*chunk_size]
            right = code[(c+1)*chunk_size : (c+2)*chunk_size]
            if debug: print(">>> basefold_encode: left={}, right={}".format(left, right))

            for j in range(0, chunk_size):
                if debug: print(">>> basefold_encode: i={}, c={}, j={}".format(i, c, j))
                rhs = right[j] * table[j]
                lhs = left[j]
                code[(c)*chunk_size + j] = lhs + rhs
                code[(c+1)*chunk_size + j] = lhs - rhs
        chunk_size = chunk_size * 2
        chunk_num = chunk_num // 2
    return code

def query_phase(transcript: MerlinTranscript, first_tree: MerkleTree, first_oracle, trees: list, oracles: list, num_vars, num_verifier_queries, debug=False):
    queries = [transcript.challenge_bytes(b"queries", 1)[0] % num_vars for _ in range(num_verifier_queries)]

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
        indices.append(x0)
        q = x0
        num_vars_copy >>= 1

        for oracle in oracles:
            x0 = int(q)
            x1 = int(q - num_vars_copy / 2 if q >= num_vars_copy / 2 else q + num_vars_copy / 2)
            if x1 < x0:
                x0, x1 = x1, x0
            
            cur_path.append((oracle[x0], oracle[x1]))
            if debug: print("x0:", x0, "x1:", x1, "num_vars:", num_vars_copy)
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

def prove_basefold_evaluation_arg_multilinear_basis(f_code, f_evals, us, v, k, k0, T, blowup_factor, commit, num_verifier_queries, transcript: MerlinTranscript, debug=False):
    # TODO: check if the length of f is a power of 2
    
    n = len(f_evals)
    half = n >> 1
    assert len(T) == k, "wrong table size, k={}, len(T)={}".format(k, len(T))
    f_code_copy = f_code[:]
    f = f_evals[:]
    MLEPolynomial.set_field_type(Fp)
    eq = MLEPolynomial.eqs_over_hypercube(us)

    challenge_vec = []
    sumcheck_sum = v
    h_poly_vec = []
    f_code_vec = []
    f_code_trees = []
    for i in range(k):
        if debug: print("sumcheck round {}".format(i))
        f_low = f[:half]
        f_high = f[half:]
        eq_low = eq[:half]
        eq_high = eq[half:]
        
        # print("low={}, high={}".format(low, high))

        h_eval_at_0 = sum([f_low[j] * eq_low[j] for j in range(half)])
        h_eval_at_1 = sum([f_high[j] * eq_high[j] for j in range(half)])
        h_eval_at_2 = sum([ (2 * f_high[j] - f_low[j]) * (2 * eq_high[j] - eq_low[j]) for j in range(half)])
        h_poly_vec.append([h_eval_at_0, h_eval_at_1, h_eval_at_2])
        
        if debug: print("> sumcheck: h=[{},{},{}]".format(h_eval_at_0, h_eval_at_1, h_eval_at_2))
        if debug: print("> sumcheck: {} ?= {}".format(h_eval_at_0 + h_eval_at_1, sumcheck_sum))
        
        assert h_eval_at_0 + h_eval_at_1 == sumcheck_sum, "{} + {} != {}".format(h_eval_at_0, h_eval_at_1, sumcheck_sum)

        # Receive a random number from the verifier
        alpha = As[transcript.challenge_bytes(b"alpha", 1)[0]]
        
        challenge_vec.append(alpha)

        # fold(low, high, alpha)
        f = [(1 - alpha) * f_low[i] + alpha * f_high[i] for i in range(half)]
        eq = [(1 - alpha) * eq_low[i] + alpha * eq_high[i] for i in range(half)]
        if debug: print("> sumcheck: f_folded = {}".format(f))
        if debug: print("> sumcheck: eq_folded = {}".format(eq))

        # compute the new sum = h(alpha)
        sumcheck_sum = UniPolynomial.uni_eval_from_evals([h_eval_at_0, h_eval_at_1, h_eval_at_2], alpha, [Fp(0),Fp(1),Fp(2)])
        if debug: print("> sumcheck: sumcheck_sum = {}".format(sumcheck_sum))

        if debug: print("fri round {}".format(i))

        # # Basefold fri
        f_code = basefold_fri_multilinear_basis(f_code, T[k-i-1], alpha, debug=debug)
        if debug: print("> fri: f_code_folded=", f_code)
        f_code_vec.append(f_code)
        f_code_trees.append(MerkleTree(f_code))

        # DEBUG: consistency check (invariant)
        # Enc(fold(message)) = fold(Enc(message)) 
        if len(f) > k0:
            if debug: print(f"len(f): {len(f)}")
            debug_f_folded_code = basefold_encode(m=f, k0=k0, depth=k-i-1, c=blowup_factor, G0=rs_encode, T=T[:k-i-1], debug=debug)
            if debug: print("> fri: enc({})={}".format(f, debug_f_folded_code))
            assert f_code == debug_f_folded_code, "Enc(fold(message)) != fold(Enc(message))"

        for i, e in enumerate([h_eval_at_0, h_eval_at_1, h_eval_at_2]):
            transcript.append_message(f'h_eval_at_{i}'.encode('ascii'), str(e).encode('ascii'))
        for i, e in enumerate(f_code):
            transcript.append_message(f'f_code_of_{i}'.encode('ascii'), str(e).encode('ascii'))
        
        half = half >> 1

    # DEBUG:
    if k0 == 1:
        f_eval_at_random = sumcheck_sum/eq[0]
        assert rs_encode([f_eval_at_random], k0=1, c=blowup_factor) == f_code, "❌: Encode(f(rs)) != f_code_0"
        if debug: print("end: f_code={}, sum={}, sum/eq={}".format(f_code, sumcheck_sum, sumcheck_sum/eq[0]))
        if debug: print("🙈: fold(f_code) == encode(fold(f_eq)/fold(eq(us)))")

    query_paths, merkle_paths = query_phase(transcript, commit, f_code_copy, f_code_trees, f_code_vec, len(f_code_copy), num_verifier_queries, debug)

    # return (h_poly_vec, challenge_vec, f_code_vec)
    return {
        'h_poly_vec': h_poly_vec,
        'f_code_vec': f_code_vec,
        'challenge_vec': challenge_vec,
        'f_code_trees': f_code_trees,
        'query_paths': query_paths,
        'merkle_paths': merkle_paths
    }

def verify_queries(commit, proof, k, num_vars, num_verifier_queries, T, debug=False):
    transcript = MerlinTranscript(b"verify queries")
    transcript.append_message(b"commit.root", bytes(commit.root, 'ascii'))

    fold_challenges = []
    for i in range(k):
        fold_challenges.append(As[transcript.challenge_bytes(b"alpha", 1)[0]])
        for j, e in enumerate(proof['h_poly_vec'][i]):
            transcript.append_message(bytes(f'h_eval_at_{j}', 'ascii'), str(e).encode('ascii'))
        for j, e in enumerate(proof['f_code_vec'][i]):
            transcript.append_message(bytes(f'f_code_of_{j}', 'ascii'), str(e).encode('ascii'))

    queries = [transcript.challenge_bytes(b"queries", 1)[0] % num_vars for _ in range(num_verifier_queries)]
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

            if i != len(mps) - 1:
                table = T[k-i-1]
                if debug: print("table:", table)
                if debug: print("x0:", x0)
                if debug: print("x1:", x1)
                f_code_folded = cur_path[i + 1][0 if x0 < num_vars_copy / 4 else 1]
                alpha = fold_challenges[i]
                if debug: print("f_code_folded:", f_code_folded)
                if debug: print("expected:", ((1 - alpha) * (code_left + code_right)/2 + (alpha) * (code_left - code_right)/(2*table[x0])))
                if debug: print("code_left:", code_left)
                if debug: print("code_right:", code_right)
                if debug: print("alpha:", alpha)
                assert f_code_folded == ((1 - alpha) * (code_left + code_right)/2 + (alpha) * (code_left - code_right)/(2*table[x0])), "failed to check multilinear base fri"

            if i == 0:
                assert verify_decommitment(x0, code_left, mp, commit.root)
            else:
                assert verify_decommitment(x0, code_left, mp, proof['f_code_trees'][i - 1].root)

            num_vars_copy >>= 1
            q = x0

def verify_basefold_evaluation_arg_multilinear_basis(N, commit, proof, us, v, d, k, T, blowup_factor, num_verifier_queries, debug=False):
    # TODO: check if the length of f is a power of 2
    
    assert k == len(us), "k != len(us), k = %d, len(us) = %d" % (k, len(us))
    n = 1 << k
    assert N == n * blowup_factor, "N != n * blowup_factor, N = %d, n = %d, blowup_factor = %d" % (N, n, blowup_factor)
    
    h_poly_vec = proof['h_poly_vec']
    challenge_vec = proof['challenge_vec']
    f_code_vec = proof['f_code_vec']
    sumcheck_sum = v
    half = n >> 1
    eq_evals = MLEPolynomial.eqs_over_hypercube(us)
    
    for i in range(k):
        if debug: print("sumcheck round {}".format(i))
        h_evals = h_poly_vec[i]
        assert d+1 == len(h_evals), "d+1 != len(h_evals), d+1 = %d, len(h_evals) = %d" % (d+1, len(h_evals))

        assert sumcheck_sum == h_evals[0] + h_evals[1], "sumcheck_sum != h_evals[0] + h_evals[1], sumcheck_sum = %d, h_evals[0] = %d, h_evals[1] = %d" % (sumcheck_sum, h_evals[0], h_evals[1])
        # print("low={}, high={}".format(low, high))

        alpha = challenge_vec[i]

        sumcheck_sum = UniPolynomial.uni_eval_from_evals(h_evals, alpha, [Fp(0),Fp(1),Fp(2)])

        eq_low = eq_evals[:half]
        eq_high = eq_evals[half:]
        if debug: print("eq_low={}, eq_high={}".format(eq_low, eq_high))
        eq_evals = [(1-alpha) * eq_low[i] + alpha * eq_high[i] for i in range(half)]

        if debug: print("fri round {}".format(i))

        f_code_folded = f_code_vec[i]
        assert len(f_code_folded) == half * blowup_factor, "len(f_code_folded) != half * blowup_factor, len(f_code_folded) = %d, half = %d, blowup_factor = %d" % (len(f_code_folded), half, blowup_factor)
        half = half >> 1

    verify_queries(commit, proof, k, N, num_verifier_queries, T, debug)
        
    # check the final code
    final_code = f_code_vec[i]
    assert len(final_code) == blowup_factor, "len(final_code) != blowup_factor, len(final_code) = %d, blowup_factor = %d" % (len(final_code), blowup_factor)
    for i in range(len(final_code)):
        assert final_code[0] == final_code[i], "final_code is not a repetition code"
    # check f(alpha_vec)
    f_eval_at_random = sumcheck_sum/eq_evals[0]
    if debug: print("f_eval_at_random={}".format(f_eval_at_random))
    if debug: print("rs_encode([f_eval_at_random], k0=1, c=blowup_factor)=", rs_encode([f_eval_at_random], k0=1, c=blowup_factor))
    assert rs_encode([f_eval_at_random], k0=1, c=blowup_factor) == f_code_folded, "❌: Encode(f(rs)) != f_code_0"
    if debug: print("✅: Verified! fold({}) == encode(fold(f_eq)/fold(eq(us)))".format(commit))

    return True

def basefold_fri_monomial_basis(vs, table, alpha, debug=False):
    assert len(table) == len(vs)//2, "len(table) is not double len(vs), len(table) = %d, len(vs) = %d" % (len(table), len(vs))
    n = len(vs)
    half = n // 2
    new_vs = []
    left = vs[:half]
    right = vs[half:]

    for i in range(0, half):
        if debug: print("(left[i] + right[i])/2=", (left[i] + right[i])/2)
        new_vs.append((left[i] + right[i])/2 + (alpha) * (left[i] - right[i])/(2*table[i]))
    return new_vs

def basefold_fri_multilinear_basis(vs, table, c, debug=False):
    assert len(table) == len(vs)/2, "len(table) is not double len(vs), len(table) = %d, len(vs) = %d" % (len(table), len(vs))
    n = len(vs)
    half = int(n / 2)
    new_vs = []
    left = vs[:half]
    right = vs[half:]

    for i in range(0, half):
        if debug: print("(left[i] + right[i])/2=", (left[i] + right[i])/2)
        new_vs.append((1 - c) * (left[i] + right[i])/2 + (c) * (left[i] - right[i])/(2*table[i]))
    return new_vs


if __name__ == '__main__':
    for i in range(100):
        log_n = 2 ** randint(0, 2)
        blowup_factor = 2 ** randint(0, 2)
        log_k0 = 0
        ff = [Fp(randint(0, 100)) for _ in range(2 ** log_n)]
        T = []
        cnt = 0
        for i in range(log_n - log_k0):
            T.append([Xs[cnt + j] for j in range(2 ** log_k0 * blowup_factor * 2 ** i)])
            cnt += len(T[-1])
        ff_code = basefold_encode(m=ff, k0=2 ** log_k0, depth=log_n - log_k0, c=blowup_factor, G0=rs_encode, T=T)
        commit = MerkleTree(ff_code)
        point = [randint(0, 100) for _ in range(log_n)]
        eval = MLEPolynomial.evaluate_from_evals(ff, point)

        transcript = MerlinTranscript(b"verify queries")
        transcript.append_message(b"commit.root", bytes(commit.root, 'ascii'))
        proof = prove_basefold_evaluation_arg_multilinear_basis(f_code=ff_code, f_evals=ff, us=point, v=eval, k=log_n - log_k0, k0=2**log_k0, T=T, blowup_factor=blowup_factor, commit=commit, num_verifier_queries=4, transcript=transcript); proof
        verify_basefold_evaluation_arg_multilinear_basis(len(ff_code), commit=commit, proof=proof, us=point, v=eval, d=2, k=log_n - log_k0, T=T, blowup_factor=blowup_factor, num_verifier_queries=4)

        print("Operations:", field.Field.get_operation_count())
        field.Field.reset_operation_count()
