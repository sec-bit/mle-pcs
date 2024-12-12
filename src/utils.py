#!/usr/bin/env python3


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
    if not isinstance(x, int) or x <= 0:
        raise ValueError("x must be a positive integer")
    
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