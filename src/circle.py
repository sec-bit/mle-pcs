from sage.all import *
import sys

sys.path.append("src")
sys.path.append("../src")

from utils import log_2
from merkle import MerkleTree, verify_decommitment
from merlin.merlin_transcript import MerlinTranscript

# Base field is the prime field of p = 31
F31 = GF(31)
R = PolynomialRing(F31, ['X'])
R.inject_variables()
X, = R.gens()

# Extension field is the field of p = 31^2
C31 = R.extension(X ** 2 + 1, 'i')
C31.inject_variables()
I, = C31.gens()

# This function is to test if a given element is a generator
# of the size 32 multiplicative subgroup of the extension field
# Inputs:
#   x: integer in range [0,30] representing real part
#   y: integer in range [0,30] representing imaginary part
# Returns:
#   bool: True if x + y*I is a generator, False otherwise
def test_generator(x, y):
    # Input validation
    if not isinstance(x, int):
        raise TypeError(f"x must be an integer, got {type(x)}")
    if not isinstance(y, int):
        raise TypeError(f"y must be an integer, got {type(y)}")
    if not (0 <= x < 31 and 0 <= y < 31):
        raise ValueError(f"x and y must be in range [0,30], got x={x}, y={y}")
        
    g = x + y * I
    g_30 = g**30
    for i in range(1, 32):
        if g_30**i == 1:
            return False
    return True

g = 0

# Try to find the generator by brute force
for x in range(31):
    for y in range(31):
        if test_generator(x, y):
            g = x + y * I
            break

g_30 = g**30

# Check that the generator's order is 32
assert g_30**32 == 1

# This is a function to compute the next domain
# by squaring the previous domain
# Inputs:
#   D: list of domain elements
# Returns:
#   list: new domain with squared elements
def sq(D):
    # Input validation
    if not isinstance(D, list):
        raise TypeError(f"D must be a list, got {type(D)}")
    if len(D) == 0:
        raise ValueError("D cannot be empty")
    if len(D) % 2 != 0:
        raise ValueError(f"Length of D must be even, got {len(D)}")

    rs = []
    for t in D[:len(D)//2]:
        # x' == 2 * x^2 - 1
        rs += [t**2]
    return rs

# G5 is a multiplicative group of size 32
G5 = [g_30**k for k in range(32)]
# G is a list of domains
G = [G5]
# tmp is the last domain in G
tmp = G[-1]
# Compute the next domain by squaring the previous domain
for i in range(5):
    tmp = sq(tmp)
    G = [tmp] + G

# standard_position_cosets are cosets of G_n
# that shifted by G_(n+1)'s first element
standard_position_cosets = [[G[i + 1][1] * p for p in G[i]] for i in range(5)]

# Define inverse operation on the group
def group_inv(g1):
    assert g1 in C31, f'g1 must be an element of C31, got {type(g1)}'
    x1, y1 = g1
    return x1 - y1 * I

# Define multiplication operation on the group
def group_mul(g1, g2):
    assert g1 in C31, f'g1 must be an element of C31, got {type(g1)}'
    assert g2 in C31, f'g2 must be an element of C31, got {type(g2)}'
    x1, y1 = g1
    x2, y2 = g2
    return (x1 * x2 - y1 * y2) + (x1 * y2 + y1 * x2) * I

# Define pie mapping of elements on the group
# This function is only applied to the x coordinate of a point
# Inputs:
#   t: field element representing x coordinate
# Returns:
#   field element: mapped x coordinate
def pie(t):
    assert t in F31, f't must be an element of F31, got {type(t)}'
    # x^2 - y^2 == 2 * x^2 - 1 (x^2 + y^2 = 1)
    return F31(2 * t**2 - 1)

# Define pie mapping of elements on the group
# This function is only applied to the x coordinate of points
# Inputs:
#   D: list of domain elements
# Returns:
#   list: new domain with mapped x coordinates
def pie_group(D):
    # Input validation
    if not isinstance(D, list):
        raise TypeError(f"D must be a list, got {type(D)}")
    if len(D) == 0:
        raise ValueError("D cannot be empty")
    if len(D) % 2 != 0:
        raise ValueError(f"Length of D must be even, got {len(D)}")

    D_new = []
    for x in D:
        x_new = pie(x)
        if x_new not in D_new:
            D_new.append(x_new)

    # Check that the new domain is exactly half size of the old domain
    assert len(D_new) * 2 == len(D), "len(D_new) * 2 != len(D), {} * 2 != {}, D_new={}, D={}".format(len(D_new), len(D), D_new, D)
    
    return D_new

# This function is to generate the vanishing polynomial of degree n
def v_n(x, log_n):
    # Input validation
    if not x in F31:
        raise TypeError(f"x must be an element of F31, got {type(x)}")
    if not isinstance(log_n, int):
        raise TypeError(f"log_n must be an integer, got {type(log_n)}")
    if log_n < 1:
        raise ValueError(f"log_n must be positive, got {log_n}")

    for _ in range(log_n - 1):
        x = 2 * x**2 - 1
    return x

# NOT TESTED
def zeroifier(at, shift, log_n):
    return v_n(at, log_n) - v_n(shift, log_n)

# This function is to compute the vanishing polynomial of degree n - 1
def v_n_prod(x, log_n):
    output = x
    for _ in range(log_n - 2):
        x = 2 * x ** 2 - 1
        output *= x
    return output

# NOT TESTED
def s_p_at_p(at, log_n, debug=False):
    x, y = at
    if debug:
        print('v_n_prod(x):', v_n_prod(x, log_n), 'y:', y)
    return -v_n_prod(x, log_n) * (2 ** (2 * log_n - 1)) * y

# This function is to compute the multiplicative inverse of a list of elements
# Inputs:
#   x: list of field elements
# Returns:
#   list: multiplicative inverses of input elements
def batch_multiplicative_inverse(x, result=None):
    if result is None:
        result = [1 for _ in range(len(x))]

    # Input validation
    if not isinstance(x, (list, tuple)):
        raise TypeError(f"x must be a list or tuple, got {type(x)}")
    if len(x) == 0:
        return result
    for val in x:
        if val == 0:
            raise ValueError("Cannot compute multiplicative inverse of 0")
        if not val in F31:
            raise TypeError(f"All elements must be in F31, got element {val} of type {type(val)}")

    n = len(x)
    assert len(result) == n, "len(result) != len(x), {} != {}, result={}, x={}".format(len(result), len(x), result, x)

    for i in range(1, n):
        result[i] = result[i - 1] * x[i - 1]

    product = result[-1] * x[-1]
    inv = 1 / product
    for i in range(n - 1, -1, -1):
        result[i] *= inv
        inv *= x[i]

    return result

def batch_multiplicative_inverse_raw(x):
    # Input validation
    if not isinstance(x, list):
        raise TypeError(f"x must be a list, got {type(x)}")
    if len(x) == 0:
        raise ValueError("x cannot be empty")
    for val in x:
        if val == 0:
            raise ValueError(f"Cannot compute multiplicative inverse of 0, x={x}")
        if not val in F31:
            raise TypeError(f"All elements must be in F31, got element {val} of type {type(val)}")

    return [1 / x_i for x_i in x]

# NOT TESTED
def compute_lagrange_den_batched(points, at, log_n, debug=False):

    assert at in C31, f'at must be an element of C31, got {type(at)}'

    numer = []
    denom = []
    for pt in points:
        assert pt in C31, f'pt must be an element of C31, got {type(pt)}'
        diff = at - pt
        x, y = diff
        numer.append(x + 1)
        if debug:
            print('y:', y, 'pt:', pt, 's_p_at_p:', s_p_at_p(pt, log_n))
        denom.append(y * s_p_at_p(pt, log_n, debug=False))
    
    inv_d = batch_multiplicative_inverse(denom)

    return [numer[i] * inv_d[i] for i in range(len(numer))]

# This function is to evaluate the polynomial at a given point
# NOT TESTED
def evaluate_at_point(evals, domain, point, debug=False):
    assert len(evals) == len(domain), "len(evals) != len(domain), {} != {}, evals={}, domain={}".format(len(evals), len(domain), evals, domain)
    x, _ = point
    log_n = log_2(len(evals))
    shift = g_30 ** (5 - log_n)
    lagrange_num = zeroifier(x, shift, log_n)
    lagrange_den = compute_lagrange_den_batched(domain, point, log_n, debug)

    return sum([lagrange_den[i] * evals[i] for i in range(len(evals))]) * lagrange_num

# Helper function for eval_at_point_raw
def eval_at_p_recursive(evals, twiddle, debug=False):
    assert twiddle in F31, f'twiddle must be an element of F31, got {type(twiddle)}'

    if len(evals) == 1:
        return evals[0]
    else:
        f0 = eval_at_p_recursive(evals[:len(evals)//2], pie(twiddle), debug)
        f1 = eval_at_p_recursive(evals[len(evals)//2:], pie(twiddle), debug)
        return f0 + f1 * twiddle

# Evaluate polynomial at a given point with O(n*log(n))
def eval_at_point_raw(evals, domain, point, debug=False):

    assert point in C31, f'point must be an element of C31, got {type(point)}'
    assert len(evals) == len(domain), "len(evals) != len(domain), {} != {}, evals={}, domain={}".format(len(evals), len(domain), evals, domain)

    x, y = point
    coeffs = CFFT.ifft_list(evals)

    left, right = coeffs[:len(coeffs)//2], coeffs[len(coeffs)//2:]
    left_eval = eval_at_p_recursive(left, x)
    right_eval = eval_at_p_recursive(right, x)

    return left_eval + right_eval * y

# Compute vanishing polynomial of zeta at x
# v_p is single point vanishing polynomial, v_p(x, y) = (1 - x, -y)
# x and y are real and imaginary parts of diff = group_mul(p, group_inv(at)) (diff = p - at)
def deep_quotient_vanishing_part(x, zeta, alpha_pow_width, debug=False):
    assert x in C31, f'x must be an element of C31, got {type(x)}'
    assert zeta in C31, f'zeta must be an element of C31, got {type(zeta)}'
    assert alpha_pow_width in F31, f'alpha_pow_width must be an element of F31, got {type(alpha_pow_width)}'

    v_p = lambda p, at: (1 - group_mul(p, group_inv(at))[0], -group_mul(p, group_inv(at))[1])
    # real part and imaginary part
    re_v_zeta, im_v_zeta = v_p(x, zeta)
    # This step is to rationalize the denominator of complex number
    # with first return value as numerator and second return value as denominator
    # and use alpha_pow_width to replace 'i'
    return (re_v_zeta - im_v_zeta * alpha_pow_width, re_v_zeta ** 2 + im_v_zeta ** 2)

# Compute the deep quotient polynomial of evals at zeta
def deep_quotient_reduce(evals, domain, alpha, zeta, p_at_zeta, debug=False):
    assert alpha in F31, f'alpha must be an element of F31, got {type(alpha)}'
    assert len(evals) == len(domain), "len(evals) != len(domain), {} != {}, evals={}, domain={}".format(len(evals), len(domain), evals, domain)
    assert zeta in C31, f'zeta must be an element of C31, got {type(zeta)}'
    assert p_at_zeta in F31, f'p_at_zeta must be an element of F31, got {type(p_at_zeta)}'

    vp_nums, vp_demons = zip(*[(deep_quotient_vanishing_part(x, zeta, alpha, debug)) for x in domain])
    vp_denom_invs = batch_multiplicative_inverse(vp_demons)
    if debug: print('vp_nums:', vp_nums, 'vp_denom_invs:', vp_denom_invs, 'p_at_zeta:', p_at_zeta, 'evals:', evals)

    return [vp_denom_invs[i] * vp_nums[i] * (evals[i] - p_at_zeta) for i in range(len(evals))]

# This function is the same as deep_quotient_reduce but only for one point
def deep_quotient_reduce_row(alpha, x, zeta, ps_at_x, ps_at_zeta, debug=False):
    assert alpha in F31, f'alpha must be an element of F31, got {type(alpha)}'
    assert x in C31, f'x must be an element of C31, got {type(x)}'
    assert zeta in C31, f'zeta must be an element of C31, got {type(zeta)}'
    assert ps_at_x in F31, f'ps_at_x must be an element of F31, got {type(ps_at_x)}'
    assert ps_at_zeta in F31, f'ps_at_zeta must be an element of F31, got {type(ps_at_zeta)}'

    vp_num, vp_denom = deep_quotient_vanishing_part(x, zeta, alpha)
    if debug: print('vp_num:', vp_num, 'vp_denom:', vp_denom, 'ps_at_x:', ps_at_x, 'ps_at_zeta:', ps_at_zeta)
    return vp_num * (ps_at_x - ps_at_zeta) / vp_denom

# Simplify deep_quotient_reduce by using deep_quotient_reduce_row
def deep_quotient_reduce_raw(evals, domain, alpha, zeta, p_at_zeta, debug=False):
    assert len(evals) == len(domain), "len(evals) != len(domain), {} != {}, evals={}, domain={}".format(len(evals), len(domain), evals, domain)
    assert alpha in F31, f'alpha must be an element of F31, got {type(alpha)}'
    assert zeta in C31, f'zeta must be an element of C31, got {type(zeta)}'
    assert p_at_zeta in F31, f'p_at_zeta must be an element of F31, got {type(p_at_zeta)}'

    res = []
    for ps_at_x, x in zip(evals, domain):
        res.append(deep_quotient_reduce_row(alpha, x, zeta, ps_at_x, p_at_zeta, debug))
    return res

# Extract lambda from lde to fix the dimension gap
# In this step, lde reduces a term which is the vanishing polynomial of degree N/2
# Inputs:
#   lde: list of field elements representing polynomial evaluations
#   log_blowup: integer representing log2 of blowup factor
#   debug: bool for debug printing
# Returns:
#   tuple: (new lde values, extracted lambda value)
def extract_lambda(lde, log_blowup, debug=False):
    assert len(lde) > 0, "lde is empty"
    assert lde[0] in F31, f'lde\'s element must be an element of F31, got {type(lde[0])}'

    if debug:
        assert isinstance(lde, list), f'lde is not of type list: {lde}'
    log_lde_size = log_2(len(lde))

    # v_n is constant on cosets of the same size as orig_domain, so we only have
    # as many unique values as we have cosets.
    if debug: print('log_lde_size:', log_lde_size, ', log_blowup:', log_blowup)
    if debug: print('CirclePCS.domains[log_lde_size][:1 << log_blowup]:', CirclePCS.domains[log_lde_size][:1 << log_blowup])
    v_d_init = [v_n(p[0], log_lde_size - log_blowup) for p in CirclePCS.domains[log_lde_size][:1 << log_blowup]]

    # The unique values are repeated over the rest of the domain like
    # 0 1 2 .. n-1 n n n-1 .. 1 0 0 1 ..
    v_d = v_d_init + v_d_init[::-1]
    while (len(v_d) < len(lde)):
        v_d += v_d
    
    # < v_d, v_d >
    # This formula was determined experimentally...
    v_d_2 = F31(2) ** (log_lde_size - 1)
    
    if debug: print('lde:', lde)
    if debug: print('v_d:', v_d)
    lambda_ = sum([lde[i] * v_d[i] for i in range(len(lde))]) * (1 / v_d_2)
    if debug: print('lambda_:', lambda_)

    new_lde = []
    for y, v_x in zip(lde, v_d):
        new_lde.append(y - lambda_ * v_x)

    return new_lde, lambda_

# Divide a standard position coset of size n * size into n twin cosets
# Inputs:
#   n: number of cosets to divide into
#   size: size of each coset
# Returns:
#   list: n twin cosets
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

# Pop an element from a list
# Inputs:
#   v: list with at least one element
# Returns:
#   tuple: (first element, remaining list)
def pop(v):
    assert len(v) > 0, "v is empty"
    return v[0], v[1:]

# Reunite the twin cosets order list into standard position coset order
# Inputs:
#   cosets: cosets order list
# Returns:
#   list: combined cosets in standard position order
def combine(cosets):
    cosets = cosets[:]
    n = len(cosets)
    res = []
    while len(cosets[0]) > 0:
        for i in range(n):
            t, cosets[i] = pop(cosets[i])
            res.append(t)
        for i in range(n):
            t, cosets[n - 1 - i] = pop(cosets[n - 1 - i])
            res.append(t)
    return res

# This class is to perform FFT and IFFT on the polynomial
class CFFT:
    # The first step, interpolate y
    # Inputs:
    #   f: dict mapping domain points to field elements
    # Returns:
    #   tuple: (f0, f1) where f0,f1 are dicts mapping x-coordinates to field elements
    @classmethod
    def _ifft_first_step(cls, f):
        assert isinstance(f, dict), f'f is not of type dict: {f}'
        f0 = {}
        f1 = {}
        for t in f:
            assert t in C31, f't must be an element of C31, got {type(t)}'
            x, y = t

            f0[x] = (f[t] + f[group_inv(t)]) / F31(2)
            f1[x] = (f[t] - f[group_inv(t)]) / (F31(2) * y)

            # Check that f is divided into 2 parts correctly
            assert f[t] == f0[x] + y * f1[x]

        return f0, f1

    # The first step, interpolate y
    # Inputs:
    #   f: list of polynomial evals
    # Returns:
    #   tuple: (f0, f1) where f0,f1 are lists of coefficients
    @classmethod
    def _ifft_first_step_list(cls, f, domain=None):
        assert isinstance(f, list), f'f is not of type list: {f}'
        assert len(f) % 2 == 0, "len(f) must be even, len(f)={}".format(len(f))

        if domain is None:
            domain = standard_position_cosets[log_2(len(f))]

        f0 = [None for _ in range(len(f) // 2)]
        f1 = [None for _ in range(len(f) // 2)]
        for i in range(len(f) // 2):
            i_sibling = len(f) - 1 - i
            f0[i] = (f[i] + f[i_sibling]) / F31(2)
            f1[i] = (f[i] - f[i_sibling]) / (F31(2) * domain[i][1])
            
            # Check that f is divided into 2 parts correctly
            assert f[i] == f0[i] + domain[i][1] * f1[i]
            assert f[i_sibling] == f0[i] - domain[i][1] * f1[i]

        return f0, f1
    
    # The rest steps, interpolate V(x)
    # Inputs:
    #   f: dict mapping x-coordinates to field elements
    # Returns:
    #   list: coefficients of interpolated polynomial
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
            f0[pie(x)] = (f[x] + f[-x]) / F31(2)
            f1[pie(x)] = (f[x] - f[-x]) / (F31(2) * x)

            # Check that f is divided into 2 parts correctly
            assert f[x] == f0[pie(x)] + x * f1[pie(x)]
            assert f[-x] == f0[pie(x)] - x * f1[pie(x)]

        return cls._ifft_normal_step(f0) + cls._ifft_normal_step(f1)

    # The rest steps, interpolate V(x)
    # Inputs:
    #   f: list of polynomial coefficients
    # Returns:
    #   list: coefficients of interpolated polynomial
    @classmethod
    def _ifft_normal_step_list(cls, f, domain=None):
        assert isinstance(f, list), f'f is not of type list: {f}'

        if len(f) == 1:
            return f
        
        assert len(f) % 2 == 0, "len(f) must be even, len(f)={}".format(len(f))
        
        # +1 due to y folded
        next_domain = None
        if domain is None:
            domain = standard_position_cosets[log_2(len(f)) + 1]
            next_domain = standard_position_cosets[log_2(len(f))]

        f0 = [None for _ in range(len(f) // 2)]
        f1 = [None for _ in range(len(f) // 2)]
        for i in range(len(f) // 2):
            i_sibling = len(f) - 1 - i
            f0[i] = (f[i] + f[i_sibling]) / F31(2)
            f1[i] = (f[i] - f[i_sibling]) / (F31(2) * domain[i][0])
        
        return cls._ifft_normal_step_list(f0, next_domain) + cls._ifft_normal_step_list(f1, next_domain)
    
    # IFFT
    # Inputs:
    #   f: dict mapping domain points to field elements
    # Returns:
    #   list: coefficients of interpolated polynomial
    @classmethod
    def ifft(cls, f):
        f0, f1 = cls._ifft_first_step(f)
        f0 = cls._ifft_normal_step(f0)
        f1 = cls._ifft_normal_step(f1)

        return f0 + f1

    # IFFT
    # Inputs:
    #   f: list of polynomial coefficients
    # Returns:
    #   list: coefficients of interpolated polynomial
    @classmethod
    def ifft_list(cls, f, domain=None):
        if domain is None:
            domain = standard_position_cosets[log_2(len(f))]

        f0, f1 = cls._ifft_first_step_list(f, domain)
        f0 = cls._ifft_normal_step_list(f0, domain)
        f1 = cls._ifft_normal_step_list(f1, domain)

        return f0 + f1
    
    # The first step, fold y
    # Inputs:
    #   f: list of polynomial coefficients
    #   D: list of domain points
    # Returns:
    #   tuple: (f0, f1, D_new) where f0,f1 are lists of coefficients and D_new is the new domain
    @classmethod
    def _fft_first_step(cls, f, D):
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
    
    # The rest steps, fold V(x)
    # Inputs:
    #   f: list of polynomial coefficients
    #   D: list of domain points
    # Returns:
    #   dict: mapping from domain points to field elements
    @classmethod
    def _fft_normal_step(cls, f, D):
        if len(f) == 1:
            return {D[0]: f[0]}
        
        next_domain = pie_group(D)

        # Check that the new domain is exactly half size of the old domain
        assert len(next_domain) * 2 == len(D), "len(next_domain) * 2 != len(D), {} * 2 != {}, next_domain={}, D={}".format(len(next_domain), len(D), next_domain, D)
        # Check that the polynomial and the domain have the same length
        assert len(f) == len(D), "len(f) != len(D), {} != {}, f={}, D={}".format(len(f), len(D), f, D)

        f0 = cls._fft_normal_step(f[:len(f)//2], next_domain)
        f1 = cls._fft_normal_step(f[len(f)//2:], next_domain)

        f_new = {}
        for x in D:
            f_new[x] = f0[pie(x)] + f1[pie(x)] * x

        # Check that f is divided into 2 parts correctly
        for x in D:
            if x != 0:
                assert f0[pie(x)] == (f_new[x] + f_new[-x]) / C31(2), "f0[pi(x)] = {}".format(f0[pie(x)])
                assert f1[pie(x)] == (f_new[x] - f_new[-x]) / (C31(2) * x), "f1[pi(x)] = {}".format(f1[pie(x)])
            else:
                assert f0[pie(x)] == f_new[x], "f0[pi(x)] = {}".format(f0[pie(x)])

        # Check that the polynomial and the domain have the same length
        assert len(f) == len(f_new), "len(f) != len(f_new), {} != {}, f={}, f_new={}, D={}".format(len(f), len(f_new), f, f_new, D)

        # Check that ifft and fft are correct inverse operations
        assert cls._ifft_normal_step(f_new) == f, "ifft(f_new) != f, {} != {}".format(cls._ifft_normal_step(f_new), f)
            
        return f_new
    
    # The rest steps, fold V(x)
    # Inputs:
    #   f: list of polynomial coefficients
    # Returns:
    #   list: coefficients of folded polynomial
    @classmethod
    def _fft_normal_step_list(cls, f, domain=None):
        if len(f) == 1:
            return f
        
        next_domain = None
        if domain is None:
            domain = standard_position_cosets[log_2(len(f)) + 1]
            next_domain = standard_position_cosets[log_2(len(f))]

        assert len(f) * 2 == len(domain), "len(f) * 2 != len(domain), {} * 2 != {}, f={}, domain={}".format(len(f), len(domain), f, domain)

        f0 = cls._fft_normal_step_list(f[:len(f)//2], next_domain)
        f1 = cls._fft_normal_step_list(f[len(f)//2:], next_domain)
        new_f = [None for _ in range(len(f))]

        for i in range(len(f) // 2):
            i_sibling = len(f) - 1 - i
            new_f[i] = f0[i] + f1[i] * domain[i][0]
            new_f[i_sibling] = f0[i] - f1[i] * domain[i][0]

        for i in range(len(f) // 2):
            i_sibling = len(f) - 1 - i
            assert f0[i] == (new_f[i] + new_f[i_sibling]) / F31(2)
            assert f1[i] == (new_f[i] - new_f[i_sibling]) / (F31(2) * domain[i][0])

        assert cls._ifft_normal_step_list(new_f, domain) == f, "ifft(f) != f, {} != {}".format(cls._ifft_normal_step_list(new_f, domain), f)

        return new_f
    
    # FFT
    # Inputs:
    #   f: list of polynomial coefficients
    #   D: list of domain points
    # Returns:
    #   dict: mapping from domain points to field elements
    @classmethod
    def fft(cls, f, D):
        # Check that the polynomial and the domain have the same length
        assert len(f) == len(D), "len(f) != len(D), {} != {}, f={}, D={}".format(len(f), len(D), f, D)

        D_copy = D[:]
        f0, f1, D = cls._fft_first_step(f, D)

        # Check that the polynomial and the domain have the same length
        assert len(f0) == len(D), "len(f0) != len(D), {} != {}, f0={}, D={}".format(len(f0), len(D), f0, D)
        assert len(f1) == len(D), "len(f1) != len(D), {} != {}, f1={}, D={}".format(len(f1), len(D), f1, D)

        f0 = cls._fft_normal_step(f0, D)
        f1 = cls._fft_normal_step(f1, D)

        f = {}
        # supply y to the polynomial
        for t in D_copy:
            x, y = t
            f[t] = f0[x] + f1[x] * y

        return f

    # FFT
    # Inputs:
    #   f: list of polynomial coefficients
    # Returns:
    #   list: coefficients of folded polynomial
    @classmethod
    def fft_list(cls, f, domain=None):
        if domain is None:
            domain = standard_position_cosets[log_2(len(f))]

        assert len(f) == len(domain), "len(f) != len(domain), {} != {}, f={}, domain={}".format(len(f), len(domain), f, domain)

        f0, f1 = f[:len(f)//2], f[len(f)//2:]
        f0 = cls._fft_normal_step_list(f0, domain)
        f1 = cls._fft_normal_step_list(f1, domain)
        new_f = [None for _ in range(len(f))]

        for i in range(len(f) // 2):
            i_sibling = len(f) - 1 - i
            new_f[i] = f0[i] + f1[i] * domain[i][1]
            new_f[i_sibling] = f0[i] - f1[i] * domain[i][1]

            assert f0[i] == (new_f[i] + new_f[i_sibling]) / F31(2)
            assert f1[i] == (new_f[i] - new_f[i_sibling]) / (F31(2) * domain[i][1])

        assert cls.ifft_list(new_f, domain) == f, "ifft(f) != f, {} != {}".format(cls.ifft_list(new_f, domain), f)

        return new_f
    
    # Convert a vector to the required type by FFT
    # Inputs:
    #   vec: list of field elements
    #   domain: list of domain points
    # Returns:
    #   dict: mapping from domain points to field elements
    @classmethod
    def vec_2_poly(cls, vec, domain):
        f = {}
        for i, t in enumerate(domain):
            f[t] = vec[i]
        return f
    
    # Convert the type of polynomial produced by IFFT to vector
    # Inputs:
    #   poly: dict mapping domain points to field elements
    #   domain: list of domain points
    # Returns:
    #   list: field elements in domain order
    @classmethod
    def poly_2_vec(cls, poly, domain):
        return [poly[t] for t in domain]
    
    # Extrapolate the polynomial into a larger domain
    # Inputs:
    #   evals: list of field elements
    #   domain: list of domain points
    #   blowup_factor: blowup factor
    # Returns:
    #   list: field elements evaluated at expanded domain
    @classmethod
    def extrapolate(cls, evals, blowup_factor):
        coeffs = cls.ifft_list(evals)
        cosets = twin_cosets(blowup_factor, len(evals))
        res = []
        for coset in cosets:
            res += [cls.fft_list(coeffs, coset)]
        return combine(res)
    
class FRI:
    # Fold y of evals
    # Inputs:
    #   evals: list of field elements
    #   domain: list of domain points
    #   beta: field element for random linear combination
    #   debug: bool for debug printing
    # Returns:
    #   list: folded field elements
    @classmethod
    def fold_y(cls, evals, domain, beta, debug=False):
        # first step (J mapping)
        # for f in natural order, we just divide f into 2 parts from the middle
        N = len(evals)
        assert N % 2 == 0, "N must be even, N={}".format(N)
        assert len(evals) == len(domain), "len(evals) != len(domain), {} != {}, evals={}, domain={}".format(len(evals), len(domain), evals, domain)
        assert beta in F31, "beta must be in F31, beta={}".format(beta)

        left = evals[:N//2]
        right = evals[:N//2-1:-1]
        assert len(left) == len(right), "len(left) != len(right), {} != {}, left={}, right={}".format(len(left), len(right), left, right)
        evals = [None for _ in range(N//2)]
        for i, (_, y) in enumerate(domain[:N//2]):
            f0 = (left[i] + right[i]) / 2
            f1 = (left[i] - right[i]) / (2 * y)
            evals[i] = f0 + f1 * beta
            if debug: print('fold y')
            if debug: print(f"f0 = (({left[i]}) + ({right[i]}))/2 = {f0}")
            if debug: print(f"f1 = (({left[i]}) - ({right[i]}))/(2 * {y}) = {f1}")
            if debug: print(f"f0 + ({beta}) * f1 = ({f0}) + ({beta}) * ({f1}) = {f0 + beta * f1}")

        return evals
    
    # Fold y of a single row
    # Inputs:
    #   y: field element representing y coordinate
    #   beta: field element for random linear combination
    #   left: field element on left side
    #   right: field element on right side
    #   debug: bool for debug printing
    # Returns:
    #   field element: folded value
    @classmethod
    def fold_y_row(cls, y, beta, left, right, debug=False):
        assert beta in F31, "beta must be in F31, beta={}".format(beta)
        assert y in F31, "y must be in F31, y={}".format(y)
        assert left in F31, "left must be in F31, left={}".format(left)
        assert right in F31, "right must be in F31, right={}".format(right)

        f0 = (left + right) / 2
        f1 = (left - right) / (2 * y)
        if debug: print('fold y row')
        if debug: print(f"f0 = (({left}) + ({right}))/2 = {f0}")
        if debug: print(f"f1 = (({left}) - ({right}))/(2 * {y}) = {f1}")
        if debug: print(f"f0 + ({beta}) * f1 = ({f0}) + ({beta}) * ({f1}) = {f0 + beta * f1}")
        return f0 + beta * f1
    
    # Fold x of evals
    # Inputs:
    #   f: list of field elements to be folded
    #   D: list of domain points
    #   r: field element for random linear combination
    #   debug: bool for debug printing
    # Returns:
    #   tuple: (folded polynomial, new domain)
    @classmethod
    def fold_x(cls, f, D, r, debug=False):
        assert len(f) == len(D), "len(f) != len(D), {} != {}, f={}, D={}".format(len(f), len(D), f, D)
        assert r in F31, "r must be in F31, r={}".format(r)

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
            if debug: print(f"f[{i}] = {f[i]} = (({left[i]}) + ({right[i]}))/2 + {r} * (({left[i]}) - ({right[i]}))/(2 * {x})")
            f[i] = f0 + r * f1
            # if debug: print(f"{f[i]} = ({left[i]} + {right[i]})/2 + {r} * ({left[i]} - {right[i]})/(2 * {x})")
            # reuse f[N//2:] to store new domain
            f[N//2 + i] = 2 * x ** 2 - 1

        # return the folded polynomial and the new domain
        return f[:N//2], f[N//2:]
    
    # Commit phase of FRI
    # Inputs:
    #   input: polynomial to be committed
    #   blowup_factor: blowup factor
    #   domain: list of domain points
    #   transcript: transcript for challenges
    #   debug: bool for debug printing
    # Returns:
    #   dict: containing commits, trees, oracles and final polynomial
    @classmethod
    def commit_phase(cls, input, blowup_factor, domain, transcript, debug=False):
        assert isinstance(transcript, MerlinTranscript), "transcript should be a MerlinTranscript"
        assert len(input) == len(domain), "len(input) != len(domain), {} != {}, input={}, domain={}".format(len(input), len(domain), input, domain)

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
    
    # Answer query phase of FRI
    # Inputs:
    #   trees: trees of committed polynomials
    #   oracles: original polynomials
    #   index: index to query
    #   debug: bool for debug printing
    # Returns:
    #   zip: iterator of opening proofs and sibling values
    @classmethod
    def answer_query(cls, trees, oracles, index, debug=False):
        assert len(trees) == len(oracles), "len(trees) != len(oracles), {} != {}, trees={}, oracles={}".format(len(trees), len(oracles), trees, oracles)

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

    # FRI prove of single variate
    # Inputs:
    #   input: polynomial to be committed
    #   blowup_factor: blowup factor
    #   domain: domain points
    #   transcript: transcript for challenges
    #   open_input: function to open input at first layer
    #   num_queries: number of queries
    #   debug: bool for debug printing
    # Returns:
    #   dict: proof containing commit phase commits, query proofs and final polynomial
    @classmethod
    def prove(cls, input, blowup_factor, domain, transcript, open_input, num_queries, debug=False):
        assert isinstance(transcript, MerlinTranscript), "transcript should be a MerlinTranscript"
        assert len(input) == len(domain), "len(input) != len(domain), {} != {}, input={}, domain={}".format(len(input), len(domain), input, domain)
        assert blowup_factor > 0, "blowup_factor must be positive, blowup_factor={}".format(blowup_factor)

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
            # Index for y folding
            index = query >> (32 - log_2(degree) - 1)
            # This is a little different from the original FRI due to circle domain
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

    # Verify query phase of FRI
    # Inputs:
    #   index: index to verify
    #   steps: list of tuples (beta, commit, opening)
    #   reduced_opening: field element of reduced opening
    #   log_max_height: log of max height
    #   debug: bool for debug printing
    # Returns:
    #   field element: folded evaluation
    @classmethod
    def verify_query(cls, index, steps, reduced_opening, log_max_height, log_blowup, debug=False):
        assert reduced_opening in F31, "reduced_opening must be in F31, reduced_opening={}".format(reduced_opening)
        assert log_max_height - log_blowup == len(list(steps)), "log_max_height != len(steps), {} != {}, log_max_height={}, steps={}".format(log_max_height, len(list(steps)), log_max_height, steps)

        if debug: print('verify_query')
        if debug: print('index:', index)
        if debug: print('log_max_height:', log_max_height)
        if debug: print('steps:', steps)
        folded_eval = reduced_opening
        for log_folded_height, (beta, comm, opening) in zip(range(log_max_height, log_blowup, -1), steps):
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

    # FRI verify of single variate
    # Inputs:
    #   proof: proof containing commit phase commits, query proofs and final polynomial
    #   blowup_factor: blowup factor
    #   transcript: transcript for challenges
    #   open_input: function to open input at first layer
    #   debug: bool for debug printing
    # Returns:
    #   None, raises AssertionError if verification fails
    @classmethod
    def verify(cls, proof, blowup_factor, transcript, open_input, debug=False):
        assert isinstance(transcript, MerlinTranscript), "transcript should be a MerlinTranscript"
        assert blowup_factor > 0, "blowup_factor must be positive, blowup_factor={}".format(blowup_factor)

        betas = []
        for commit in proof["commit_phase_commits"]:
            transcript.append_message(b"tree", bytes(commit, 'ascii'))
            beta = int.from_bytes(transcript.challenge_bytes(b"beta", 4), "big")
            if debug: print('beta:', beta)
            betas.append(beta)
        transcript.append_message(b"final_poly", bytes(str(proof["final_poly"]), 'ascii'))

        folded_eval = 0
        log_max_height = len(proof["commit_phase_commits"]) + log_2(blowup_factor)
        for qp in proof["query_proofs"]:
            index = int.from_bytes(transcript.challenge_bytes(b"query", 4), "big")
            if debug: print('query:', index)

            # Index for y folding
            index >>= (32 - log_max_height - 1)
            # This is a little different from the original FRI due to circle domain
            index_sibling = (1 << log_max_height) * 2 - 1 - index
            if debug: print('log_max_height:', log_max_height, ', index:', index, ', index_sibling:', index_sibling)

            ro = open_input(index, qp["input_proof"])
            if debug: print('betas:', betas, ', proof["commit_phase_commits"]:', proof["commit_phase_commits"], ', qp["commit_phase_openings"]:', qp["commit_phase_openings"])
            folded_eval = cls.verify_query(min(index, index_sibling), list(zip(betas, proof["commit_phase_commits"], qp["commit_phase_openings"])), ro, log_max_height, log_2(blowup_factor), debug)

            if debug: print('folded_eval:', folded_eval)

        assert folded_eval == proof["final_poly"], "folded_eval != proof['final_poly'], {} != {}".format(folded_eval, proof["final_poly"])

class CirclePCS:
    domains = [standard_position_cosets[i] for i in range(5)]

    # Get the standard position coset of given degree
    # Inputs:
    #   degree: degree of polynomial
    # Returns:
    #   list: domain points for given degree
    @classmethod
    def natural_domain_for_degree(cls, degree):
        log_degree = log_2(degree)
        assert log_degree >= 0, "log_degree must be non-negative, log_degree={}".format(log_degree)
        assert log_degree <= 4, "log_degree must be less than or equal to 4, log_degree={}".format(log_degree)
        
        return cls.domains[log_degree]
    
    # Commit phase of PCS
    # Inputs:
    #   eval: list of field elements representing polynomial evaluations
    #   domain: domain points
    #   blowup_factor: blowup factor
    # Returns:
    #   tuple: (MerkleTree commitment, list of extrapolated evaluations)
    @classmethod
    def commit(cls, eval, domain, blowup_factor):
        # Input validation
        assert len(eval) > 0, "eval cannot be empty"
        assert len(eval) == len(domain), f"eval and domain must have same length, got {len(eval)} and {len(domain)}"
        assert blowup_factor > 0, f"blowup_factor must be positive, got {blowup_factor}"

        log_n = log_2(len(eval))
        if log_n + log_2(blowup_factor) > 4:
            raise ValueError("Eval too long")
        
        lde = CFFT.extrapolate(eval, blowup_factor)
        return MerkleTree(lde), lde
    
    # Open phase of PCS
    # Inputs:
    #   evals: list of field elements representing polynomial evaluations
    #   evals_commit: MerkleTree commitment of evaluations
    #   zeta: evaluation point
    #   log_blowup: log of blowup factor
    #   transcript: transcript for challenges
    #   num_queries: number of queries
    #   debug: bool for debug printing
    # Returns:
    #   dict: proof containing first layer commitment, lambda value and FRI proof
    @classmethod
    def open(cls, evals, evals_commit, zeta, log_blowup, transcript, num_queries, debug=False):
        if debug: print('evals:', evals)
        assert isinstance(transcript, MerlinTranscript), "transcript should be a MerlinTranscript"
        alpha = int.from_bytes(transcript.challenge_bytes(b"alpha", 4), "big")
        if debug: print('alpha:', alpha)

        # evaluate the polynomial at the point zeta
        domain = cls.natural_domain_for_degree(len(evals))
        p_at_zeta = eval_at_point_raw(evals, domain, zeta, debug)
        if debug: print('p_at_zeta:', p_at_zeta)

        # deep quotient
        reduced_opening = deep_quotient_reduce_raw(evals, domain, alpha, zeta, p_at_zeta, debug)
        if debug: print('reduced_opening:', reduced_opening)
        # extract lambda
        first_layer, lambda_ = extract_lambda(reduced_opening, log_blowup, debug)
        if debug: print('first_layer:', first_layer, ', lambda_:', lambda_)

        # commit first layer
        first_layer_tree = MerkleTree(first_layer)
        transcript.append_message(b"first_layer_root", bytes(first_layer_tree.root, 'ascii'))
        bivariate_beta = int.from_bytes(transcript.challenge_bytes(b"bivariate_beta x", 4), "big")
        if debug: print('bivariate_beta:', bivariate_beta)
        # fold first layer
        # a little modified compared to code in p3
        fri_input = FRI.fold_y(first_layer, domain, F31(bivariate_beta), debug)
        domain = [t[0] for t in domain[:len(domain)//2]]
        if debug:
            print('fri_input:', fri_input)
            print('domain:', domain)

        # Handle the first layer
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

    # Verify phase of PCS
    # Inputs:
    #   commitment: MerkleTree root commitment
    #   domain: domain points
    #   log_blowup: log of blowup factor
    #   point: evaluation point
    #   value: claimed evaluation value
    #   proof: proof containing first layer commitment, lambda value and FRI proof
    #   transcript: transcript for challenges
    #   debug: bool for debug printing
    # Returns:
    #   None, raises AssertionError if verification fails
    @classmethod
    def verify(cls, commitment, domain, log_blowup, point, value, proof, transcript, debug=False):
        assert isinstance(transcript, MerlinTranscript), "transcript should be a MerlinTranscript"
        alpha = int.from_bytes(transcript.challenge_bytes(b"alpha", 4), "big")
        if debug: print('alpha:', alpha)
        transcript.append_message(b"first_layer_root", bytes(proof["first_layer_commitment"], 'ascii'))
        bivariate_beta = int.from_bytes(transcript.challenge_bytes(b"bivariate_beta x", 4), "big")
        if debug: print('bivariate_beta:', bivariate_beta)

        # Handle the first layer
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
            if debug: print('domain:', domain, ', log_2(len(domain)) - log_blowup:', log_2(len(domain)) - log_blowup, ', v_n(domain[index_shifted], log_2(len(domain)) - log_blowup):', v_n(domain[index_shifted][0], log_2(len(domain)) - log_blowup))
            if debug: print('reduced_opening:', reduced_opening, ', proof["lambda"]:', proof["lambda"])
            lambda_corrected = reduced_opening - proof["lambda"] * v_n(domain[index_shifted][0], log_2(len(domain)) - log_blowup)
            if debug: print('lambda_corrected:', lambda_corrected)

            left = lambda_corrected if index_shifted < len(domain) // 2 else first_layer_sibling_value
            right = first_layer_sibling_value if index_shifted < len(domain) // 2 else lambda_corrected
            index_sibling = len(domain) - 1 - index_shifted
            _, y = domain[min(index_shifted, index_sibling)]
            fri_input = FRI.fold_y_row(y, bivariate_beta, left, right, debug)
            if debug: print('fri_input:', fri_input)

            if debug: print('index_shifted:', index_shifted, ', lambda_corrected:', lambda_corrected, ', first_layer_proof[0]:', first_layer_proof[0], ', commitment:', proof['first_layer_commitment'])
            assert verify_decommitment(index_shifted, lambda_corrected, first_layer_proof[0], proof['first_layer_commitment'])
            if debug: print('len(domain) - 1 - index_shifted:', len(domain) - 1 - index_shifted, ', first_layer_sibling_value:', first_layer_sibling_value, ', first_layer_proof[1]:', first_layer_proof[1], ', commitment:', proof['first_layer_commitment'])
            assert verify_decommitment(len(domain) - 1 - index_shifted, first_layer_sibling_value, first_layer_proof[1], proof['first_layer_commitment'])

            return fri_input

        FRI.verify(proof["fri_proof"], 1 << log_blowup, transcript, open_input, debug)

if __name__ == "__main__":
    from random import randint
    evals = [F31(randint(0, 31)) for _ in range(4)]
    domain = CirclePCS.natural_domain_for_degree(len(evals))
    log_blowup = 1

    commitment, lde = CirclePCS.commit(evals, domain, 1 << log_blowup)

    transcript = MerlinTranscript(b'circle pcs')
    transcript.append_message(b'commitment', bytes(str(commitment.root), 'ascii'))

    query_num = 4

    domain = CirclePCS.natural_domain_for_degree(len(lde))
    point = G5[5]
    proof = CirclePCS.open(lde, commitment, point, log_blowup, transcript, query_num, True)

    transcript = MerlinTranscript(b'circle pcs')
    transcript.append_message(b'commitment', bytes(str(commitment.root), 'ascii'))
    CirclePCS.verify(commitment.root, domain, log_blowup, point, eval_at_point_raw(evals, CirclePCS.natural_domain_for_degree(len(evals)), point), proof, transcript, True)
