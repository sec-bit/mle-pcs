#!/usr/bin/env python3


class Scalar:
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return f"Scalar({self.value})"
    
    def __str__(self):
        return f"Scalar({self.value})"
    
def inner_product(a, b, z):
    assert len(a) == len(b), "a and b must have the same length"
    return sum([a[i] * b[i] for i in range(len(a))], z)

## NOTE: Copy from py_ecc.utils
def prime_field_inv(a, n):
    """
    Extended euclidean algorithm to find modular inverses for integers
    """
    # To address a == n edge case.
    # https://tools.ietf.org/html/draft-irtf-cfrg-hash-to-curve-09#section-4
    # inv0(x): This function returns the multiplicative inverse of x in
    # F, extended to all of F by fixing inv0(0) == 0.
    a %= n

    if a == 0:
        return 0
    lm, hm = 1, 0
    low, high = a % n, n
    while low > 1:
        r = high // low
        nm, new = hm - lm * r, high - low * r
        lm, low, hm, high = nm, new, lm, low
    return lm % n

def bits_be(int):
    bits = []
    while int:
        bits.insert(0, int % 2)
        int //= 2
    return bits

def bits_le_with_width(i, width):
    if i >= 2**width:
        return "Failed"
    bits = []
    while width:
        bits.append(i % 2)
        i //= 2
        width -= 1
    return bits

def bits_le_to_int(bits):
    return int("".join(map(str, bits[::-1])), 2)

def bit_reverse(x: int, width: int) -> int:
    bits = bits_le_with_width(x, width)
    return int("".join(map(str, bits)), 2)

def pow_2(n):
    return 1 << n

def is_power_of_two(n):
    return (n & (n - 1) == 0)

def next_power_of_two(n):
    assert n >= 0, "No negative integer"
    if is_power_of_two(n):
        return n
    d = n
    k = 1
    while d > 0:
        d >>= 1
        k <<= 1
    return k

def log_2_ceiling(i):
    if i < 1:
        raise ValueError("Error: i < 1")
    c = 0
    j = i-1
    while j != 0:
        j = j >> 1
        c += 1
    return c

def log_2(x):
    """
    Compute the integer part of the logarithm base 2 of x.

    Args:
        x (int): The number to compute the logarithm of. Must be a positive integer.

    Returns:
        int: The floor of the logarithm base 2 of x.

    Raises:
        ValueError: If x is not a positive integer.
    """
    if x <= 0:
        raise ValueError(f"x must be a positive integer, x={x},type(x)={type(x)}")
    
    result = 0
    while x > 1:
        x >>= 1  # Bit shift right (equivalent to integer division by 2)
        result += 1
    return result

def from_bytes(bytes):
    res = 0
    for b in bytes:
        res = (res << 8) + b
    return res

def bit_reverse_inplace(f, k):
    if len(f) > 2**k:
        raise ValueError("length of f should be less than 2^k")
    n = 2**k
    for i in range(0, n):
        i_bits = bits_le_with_width(i, k)
        i_bits.reverse()
        i_rev = bits_le_to_int(i_bits)
        if i < i_rev:
            tmp = f[i]
            f[i] = f[i_rev]
            f[i_rev] = tmp

def reverse_bits(n: int, bit_length: int) -> int:
    """
    Reverse the bits of an integer.

    Args:
        n (int): The input integer.
        bit_length (int): The number of bits to consider.

    Returns:
        int: The integer with its bits reversed.
    """
    result = 0
    for i in range(bit_length):
        result = (result << 1) | (n & 1)
        n >>= 1
    return result

def test_log_2():
    x = 1
    print(log_2(x))

def delta_uni_decoding(rho):
    return (1 - rho) / 2

def delta_johnson_bound(rho):
    from math import sqrt
    return 1 - sqrt(rho)

def delta_list_decoding(rho):
    return 1 - rho

def query_num(blowup_factor, security_bits, delta_func):
    from math import log2
    assert blowup_factor > 1, "blowup_factor must be greater than 1"
    delta = delta_func(1 / blowup_factor)
    return int(security_bits / (-log2(1 - delta))) + 1

if __name__ == "__main__":
    import random
    k = random.randint(0, 15)
    bits = bits_le_with_width(k, 4)
    print(bits)
    bits.reverse()
    k_rev = bits_le_to_int(bits)
    print(f"k: {k}, k_rev: {k_rev}")
    assert k == bit_reverse(k_rev, 4)
    print(f"test passed")

    test_log_2()