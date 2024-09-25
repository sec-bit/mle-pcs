from sage.all import product, GF

Fp = GF(193)

# Eq Polynomials

def bits_le_with_width(i, width):
    if i >= 2**width:
        return "Failed"
    bits = []
    while width:
        bits.append(i % 2)
        i //= 2
        width -= 1
    return bits

def eqs_over_hypercube(rs):
    k = len(rs)
    n = 1 << k
    evals = [1] * n
    half = 1
    for i in range(k):
        for j in range(half):
            evals[j+half] = Fp(evals[j] * rs[i])
            evals[j] = Fp(evals[j] - evals[j+half])
        half *= 2
    return evals

def eq_poly_vec(k, indeterminates):
    if k > 5:
        raise ValueError("k>5 isn't supported")
    xs = indeterminates[:k]
    n = 1 << k
    eqs = [1] * n
    for i in range(n):
        bs = bits_le_with_width(i, k)
        eqs[i] = product([(1 - xs[j]) * (1 - bs[j]) + xs[j] * bs[j] for j in range(k)])
    return eqs

def bits_le_with_width(i, width):
    if i >= 2**width:
        return "Failed"
    bits = []
    while width:
        bits.append(i % 2)
        i //= 2
        width -= 1
    return bits

def eqs_over_hypercube_slow(rs):
    k = len(rs)
    n = 1 << k
    evals = [0] * n
    for i in range(n):
        bs = bits_le_with_width(i, k)
        evals[i] = Fp(product([(1 - rs[j]) * (1 - bs[j]) + rs[j] * bs[j] for j in range(k)]))
    return evals

# mle evaluate from coefficients

def mle_eval_from_coeffs(f_coeffs, point):
    k = len(point)
    n = len(f_coeffs)
    assert len(f_coeffs) == 1 << k, "len(f_coeffs) != 1 << k"

    monomials = [Fp(1)]
    for i in range(k):
        right = [monomials[j] * point[j] for j in range(len(monomials))]
        monomials += right

    return [f_coeffs[j] * monomials[j] for j in range(n)]

# mle_eval_from_evals

def mle_eval_from_evals(evals, point):
    k = len(point)
    f = evals[:]
    half = len(f) >> 1
    for z in point:
        even = f[::2]
        odd = f[1::2]
        f = [even[i] + z * (odd[i] - even[i]) for i in range(half)]
        half >>= 1
    return f[0]

def mle_eval_from_evals_2(evals, point):
    k = len(point)
    half = len(evals) >> 1
    vec = evals[:]
    for i in range(k):
        u = point[k-i-1]

        # folding vec=(low, high) by u
        vec = [(1-u) * vec[j] + u * vec[j+half] for j in range(half)]
        half >>= 1
    return vec[0]

# barycentric interpolation

def barycentric_weights(D):
    n = len(D)
    weights = [Fp(1)] * n
    for i in range(n):
        # weights[i] = product([(D[i] - D[j]) if i !=j else Fp(1) for j in range(n)])
        for j in range(n):
            if i==j:
                weights[i] *= 1
                continue
            weights[i] *= (D[i] - D[j])
        weights[i] = 1/weights[i]
    return weights

def uni_eval_from_evals(evals, z, D):
    n = len(evals)
    if n != len(D):
        raise ValueError("Domain size should be equal to the length of evaluations")
    if z in D:
        return evals[D.index(z)]
    weights = barycentric_weights(D)
    # print("weights={}".format(weights))
    e_vec = [weights[i] / (z - D[i]) for i in range(n)]
    numerator = sum([e_vec[i] * evals[i] for i in range(n)])
    denominator = sum([e_vec[i] for i in range(n)])
    return (numerator / denominator)

def uni_eval_from_coeffs(coeffs, z):
    t = Fp(1)
    eval = Fp(0)
    for i in range(0, len(coeffs)):
        eval += coeffs[i] * t
        t *= z
    return eval

def uni_evals_from_coeffs(coeffs, D):
    evals = []
    for z in D:
        evals += [uni_eval_from_coeffs(coeffs, z)]
    return evals
