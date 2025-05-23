import random
from typing import List, ClassVar

def convert_int_to_koalabear(func):
    def wrapper(self, other):
        if isinstance(other, int):
            other = KoalaBear(other)
        return func(self, other)
    return wrapper

class KoalaBear:
    # The KoalaBear prime: 2^31 - 2^24 + 1
    P = (1 << 31) - (1 << 24) + 1
    TWO_ADICITY = 24
    MULTIPLICATIVE_GENERATOR: ClassVar['KoalaBear']
    ROOT_OF_UNITY: ClassVar['KoalaBear']
    
    def __init__(self, value: int):
        self.value = value % self.P

    @classmethod
    def field_order(cls):
        return cls.P

    @classmethod
    def zero(cls):
        return cls(0)

    @classmethod
    def one(cls):
        return cls(1)

    @classmethod
    def random(cls):
        return cls(random.randint(0, cls.P - 1))

    @classmethod
    def neg_one(cls):
        return cls(cls.P - 1)

    @classmethod
    def nth_root_of_unity(cls, n: int):
        if not (n > 0 and (n & (n - 1)) == 0): # Check if n is a power of 2
            raise ValueError("n must be a positive power of 2 for nth_root_of_unity.")
        
        if n > (1 << cls.TWO_ADICITY): # n = 2^m, so m <= TWO_ADICITY
            raise ValueError(f"n (a power of 2) cannot exceed 2^{cls.TWO_ADICITY} for nth_root_of_unity.")

        exponent = (1 << cls.TWO_ADICITY) // n
        return cls.ROOT_OF_UNITY.pow(exponent)

    def __repr__(self):
        return f"KoalaBear({self.value})"

    def __eq__(self, other):
        if isinstance(other, KoalaBear):
            return self.value == other.value
        return False

    @convert_int_to_koalabear
    def __add__(self, other):
        return KoalaBear(self.add(self.value, other.value))

    @convert_int_to_koalabear
    def __sub__(self, other):
        return KoalaBear(self.sub(self.value, other.value))

    @convert_int_to_koalabear
    def __mul__(self, other):
        return KoalaBear(self.mul(self.value, other.value))

    def __neg__(self):
        return KoalaBear(self.P - self.value)

    def inv(self):
        # From Fermat's little theorem, in a prime field F_p, the inverse of a is a^(p-2)
        # Here p-2 = 2^31 - 2^24 - 1 = 2130706431
        return self.pow(self.P - 2)

    def pow(self, n: int):
        result = KoalaBear.one()
        base = self
        while n > 0:
            if n & 1:
                result *= base
            base *= base
            n >>= 1
        return result

    @classmethod
    def add(cls, lhs: int, rhs: int) -> int:
        return (lhs + rhs) % cls.P

    @classmethod
    def sub(cls, lhs: int, rhs: int) -> int:
        return (lhs - rhs) % cls.P

    @classmethod
    def mul(cls, lhs: int, rhs: int) -> int:
        return (lhs * rhs) % cls.P

    def __pow__(self, n: int):
        return self.pow(n)

    @convert_int_to_koalabear
    def __truediv__(self, other):
        return self * other.inv()

    def __radd__(self, other):
        return KoalaBear(other) + self

    def __rsub__(self, other):
        return KoalaBear(other) - self

    def __rmul__(self, other):
        return KoalaBear(other) * self

    def __rtruediv__(self, other):
        return KoalaBear(other) / self

    @classmethod
    def new_array(cls, values):
        """Helper method for creating arrays of field elements"""
        return [cls(v) for v in values]

    @classmethod
    def new_2d_array(cls, values):
        """Helper method for creating 2D arrays of field elements"""
        return [[cls(v) for v in row] for row in values]

KoalaBear.ROOT_OF_UNITY = KoalaBear(0x6ac49f88)
KoalaBear.MULTIPLICATIVE_GENERATOR = KoalaBear(value=3)


class KoalaBearExtElem:
    W: KoalaBear = KoalaBear(KoalaBear.P - 3)  # The parameter for the binomial extension
    NW: KoalaBear = KoalaBear(3)

    TWO_ADICITY = 26
    MULTIPLICATIVE_GENERATOR: ClassVar['KoalaBearExtElem']
    ROOT_OF_UNITY: ClassVar['KoalaBearExtElem']

    def __init__(self, elems: List[KoalaBear]):
        assert len(elems) == 4, "ExtElem must have 4 elements"
        self.elems = elems

    @classmethod
    def zero(cls):
        return cls([KoalaBear.zero()] * 4)

    @classmethod
    def one(cls):
        return cls([KoalaBear.one()] + [KoalaBear.zero()] * 3)

    @classmethod
    def random(cls):
        return cls([KoalaBear.random() for _ in range(4)])

    def __repr__(self):
        return f"KoalaBearExtElem({self.elems})"

    def __eq__(self, other):
        if isinstance(other, KoalaBearExtElem):
            return self.elems == other.elems
        return False

    @classmethod
    def neg_one(cls):
        return cls([KoalaBear.neg_one()] + [KoalaBear.zero()] * 3)

    @classmethod
    def nth_root_of_unity(cls, n: int):
        if not (n > 0 and (n & (n - 1)) == 0): # Check if n is a power of 2
            raise ValueError("n must be a positive power of 2 for nth_root_of_unity.")
        
        if n > (1 << cls.TWO_ADICITY): # n = 2^m, so m <= TWO_ADICITY
            raise ValueError(f"n (a power of 2) cannot exceed 2^{cls.TWO_ADICITY} for nth_root_of_unity.")

        exponent = (1 << cls.TWO_ADICITY) // n
        return cls.ROOT_OF_UNITY.pow(exponent)

    def __add__(self, other):
        if isinstance(other, KoalaBearExtElem):
            return KoalaBearExtElem([a + b for a, b in zip(self.elems, other.elems)])
        raise TypeError("Unsupported operand type for +")

    def __sub__(self, other):
        if isinstance(other, KoalaBearExtElem):
            return KoalaBearExtElem([a - b for a, b in zip(self.elems, other.elems)])
        raise TypeError("Unsupported operand type for -")

    def __mul__(self, other):
        if isinstance(other, KoalaBearExtElem):
            # Implement multiplication using the binomial representation
            # For quartic extension F[x]/(x^4 - W) where W = 3
            a = self.elems
            b = other.elems
            
            # Karatsuba-like multiplication for F[x]/(x^4 - W)
            c0 = a[0] * b[0] + self.NW * (a[1] * b[3] + a[2] * b[2] + a[3] * b[1])
            c1 = a[0] * b[1] + a[1] * b[0] + self.NW * (a[2] * b[3] + a[3] * b[2])
            c2 = a[0] * b[2] + a[1] * b[1] + a[2] * b[0] + self.NW * (a[3] * b[3])
            c3 = a[0] * b[3] + a[1] * b[2] + a[2] * b[1] + a[3] * b[0]
            
            return KoalaBearExtElem([c0, c1, c2, c3])
        elif isinstance(other, KoalaBear):
            return KoalaBearExtElem([elem * other for elem in self.elems])
        raise TypeError("Unsupported operand type for *")

    def __neg__(self):
        return KoalaBearExtElem([-elem for elem in self.elems])

    def inv(self):
        a = self.elems
        b0 = a[0] * a[0] + self.W * (a[1] * (a[3] + a[3]) - a[2] * a[2])
        b2 = a[0] * (a[2] + a[2]) - a[1] * a[1] + self.W * (a[3] * a[3])
        c = b0 * b0 + self.W * b2 * b2
        c_inv = c.inv()
        b0, b2 = b0 * c_inv, b2 * c_inv
        return KoalaBearExtElem([
            a[0] * b0 + self.W * a[2] * b2,
            -a[1] * b0 + self.NW * a[3] * b2,
            -a[0] * b2 + a[2] * b0,
            a[1] * b2 - a[3] * b0
        ])
        

    def pow(self, n: int):
        result = KoalaBearExtElem.one()
        base = self
        while n > 0:
            if n & 1:
                result *= base
            base *= base
            n >>= 1
        return result

    def __pow__(self, n: int):
        return self.pow(n)

    def __truediv__(self, other):
        if isinstance(other, KoalaBearExtElem):
            return self * other.inv()
        elif isinstance(other, KoalaBear):
            return self * KoalaBearExtElem([other.inv()] + [KoalaBear.zero()] * 3)
        raise TypeError("Unsupported operand type for /")

KoalaBearExtElem.ROOT_OF_UNITY = KoalaBearExtElem([KoalaBear(0), KoalaBear(0), KoalaBear(0), KoalaBear(777715144)])
KoalaBearExtElem.MULTIPLICATIVE_GENERATOR = KoalaBearExtElem([KoalaBear(2), KoalaBear(1), KoalaBear(0), KoalaBear(0)])

# Example usage:
if __name__ == "__main__":
    a = KoalaBear(0x34167c58) # from plonky3 koala_bear.rs
    b = KoalaBear(0x61f3207b) # from plonky3 koala_bear.rs
    R = KoalaBear(1<<32)
    print(f"a = {a}")
    print(f"b = {b}")
    print(f"a + b = {a + b}")
    print(f"a + 42 = {a + 42}")
    print(f"42 + a = {42 + a}")
    print(f"42 - a = {42 - a}")
    print(f"-a + 42 = {-a + 42}")
    print(f"42 * a = {42 * a}")
    print(f"a * 42 = {a * 42}")
    print(f"42 / a * a = {42 / a * a}")
    print(f"a / 42 * 42 = {a / 42 * 42}")
    print(f"a - b = {a - b}")
    print(f"a * b = {a * b}")
    assert a * b == KoalaBear(0x54b46b81) # from plonky3 koala_bear.rs
    print(f"a.inv() = {a.inv()}")
    print(f"a.pow(3) = {a.pow(3)}")
    print(f"a.inv() * a = {a.inv() * a}")  # Should be 1

    x = x = KoalaBearExtElem([KoalaBear(1419529559), KoalaBear(720734439), KoalaBear(512458410), KoalaBear(996902383)])
    print(f"x = {x}")
    print(f"x in montgomery form = {[i*R for i in x.elems]}")
    print(f"x.inv() = {x.inv()}")
    x_inv = x.inv()
    print(f"x.inv() in montgomery form = {[i*R for i in x_inv.elems]}")
    print(f"x.pow(3) = {x.pow(3)}")
    assert x * x_inv == KoalaBearExtElem.one()
    y = KoalaBearExtElem.random()
    print(f"y = {y}")
    print(f"x + y = {x + y}")
    print(f"x - y = {x - y}")
    print(f"x * y = {x * y}")
    print(f"x_neg = {-x}, x + x_neg = {x+(-x)}")

    # [0,0,0,777715144] ** 2
    last_root_of_unity = KoalaBearExtElem([KoalaBear(0), KoalaBear(0), KoalaBear(0), KoalaBear(777715144)])
    print(f"last_root_of_unity = {last_root_of_unity}")
    print(f"last_root_of_unity ** 2 = {last_root_of_unity ** 2}")
    
    for i in range(0, KoalaBear.TWO_ADICITY + 1):
        print(f"2^{i}-th root of unity = {hex(KoalaBear.nth_root_of_unity(2**i).value)}")

    '''
    same as plonky3's koala_bear.rs
    const TWO_ADIC_GENERATORS: Self::ArrayLike = &KoalaBear::new_array([
        0x1, 0x7f000000, 0x7e010002, 0x6832fe4a, 0x8dbd69c, 0xa28f031, 0x5c4a5b99, 0x29b75a80,
        0x17668b8a, 0x27ad539b, 0x334d48c7, 0x7744959c, 0x768fc6fa, 0x303964b2, 0x3e687d4d,
        0x45a60e61, 0x6e2f4d7a, 0x163bd499, 0x6c4a8a45, 0x143ef899, 0x514ddcad, 0x484ef19b,
        0x205d63c3, 0x68e7dd49, 0x6ac49f88,
    ]);
    '''
    for i in range(KoalaBear.TWO_ADICITY, KoalaBearExtElem.TWO_ADICITY + 1):
        print(f"2^{i}-th root of unity = {KoalaBearExtElem.nth_root_of_unity(2**i).elems}")
    '''
    same as plonky3's koala_bear.rs
    [0, 0, 1759267465, 0], [0, 0, 0, 777715144]
    '''