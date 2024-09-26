
def bits_le_with_width(i, width):
    if i >= 2**width:
        return "Failed"
    bits = []
    while width:
        bits.append(i % 2)
        i //= 2
        width -= 1
    return bits
    

def pow_2(n):
    return 1 << n

def is_power_of_two(n):
    d = n
    k = 0
    while d > 0:
        d >>= 1
        k += 1
    if n == 2**(k-1):
        return True
    else:
        return False

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
