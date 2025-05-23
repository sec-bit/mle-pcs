import random
from typing import List, ClassVar

def convert_int_to_babybear(func):
    def wrapper(self, other):
        if isinstance(other, int):
            other = BabyBear(other)
        return func(self, other)
    return wrapper

class BabyBear:
    P = 15 * (1 << 27) + 1
    TWO_ADICITY = 27
    MULTIPLICATIVE_GENERATOR: ClassVar['BabyBear']
    ROOT_OF_UNITY: ClassVar['BabyBear'] # Declare type for linter

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

        # cls.ROOT_OF_UNITY is assumed to be a primitive (2^TWO_ADICITY)-th root of unity.
        # To get a primitive n-th root of unity (where n is a power of 2),
        # we compute (cls.ROOT_OF_UNITY) ^ ((2^TWO_ADICITY) / n).
        exponent = (1 << cls.TWO_ADICITY) // n
        return cls.ROOT_OF_UNITY.pow(exponent)

    def __repr__(self):
        return f"BabyBear({self.value})"

    def __eq__(self, other):
        if isinstance(other, BabyBear):
            return self.value == other.value
        return False

    @convert_int_to_babybear
    def __add__(self, other):
        return BabyBear(self.add(self.value, other.value))

    @convert_int_to_babybear
    def __sub__(self, other):
        return BabyBear(self.sub(self.value, other.value))

    @convert_int_to_babybear
    def __mul__(self, other):
        return BabyBear(self.mul(self.value, other.value))

    def __neg__(self):
        return BabyBear(self.P - self.value)

    def inv(self):
        return self.pow(self.P - 2)

    def pow(self, n: int):
        result = BabyBear.one()
        base = self
        while n > 0:
            if n & 1:
                result *= base
            base *= base
            n >>= 1
        return result

    @classmethod
    def add(cls, lhs: int, rhs: int) -> int:
        x = (lhs + rhs) % cls.P
        return x

    @classmethod
    def sub(cls, lhs: int, rhs: int) -> int:
        x = (lhs - rhs) % cls.P
        return x

    @classmethod
    def mul(cls, lhs: int, rhs: int) -> int:
        return (lhs * rhs) % cls.P

    def __pow__(self, n: int):
        return self.pow(n)

    @convert_int_to_babybear
    def __truediv__(self, other):
        return self * other.inv()

    def __radd__(self, other):
        return BabyBear(other) + self

    def __rsub__(self, other):
        return BabyBear(other) - self

    def __rmul__(self, other):
        return BabyBear(other) * self

    def __rtruediv__(self, other):
        return BabyBear(other) / self

BabyBear.ROOT_OF_UNITY = BabyBear(0x1a427a41)
BabyBear.MULTIPLICATIVE_GENERATOR = BabyBear(31)

class BabyBearExtElem:
    TWO_ADICITY = 29
    MULTIPLICATIVE_GENERATOR: ClassVar['BabyBearExtElem']
    ROOT_OF_UNITY: ClassVar['BabyBearExtElem']
    BETA = BabyBear(11)
    NBETA = BabyBear(BabyBear.P - 11)

    def __init__(self, elems: List[BabyBear]):
        assert len(elems) == 4, "ExtElem must have 4 elements"
        self.elems = elems

    @classmethod
    def zero(cls):
        return cls([BabyBear.zero()] * 4)

    @classmethod
    def one(cls):
        return cls([BabyBear.one()] + [BabyBear.zero()] * 3)

    @classmethod
    def random(cls):
        return cls([BabyBear.random() for _ in range(4)])

    @classmethod
    def nth_root_of_unity(cls, n: int):
        if not (n > 0 and (n & (n - 1)) == 0): # Check if n is a power of 2
            raise ValueError("n must be a positive power of 2 for nth_root_of_unity.")
        
        if n > (1 << cls.TWO_ADICITY): # n = 2^m, so m <= TWO_ADICITY
            raise ValueError(f"n (a power of 2) cannot exceed 2^{cls.TWO_ADICITY} for nth_root_of_unity.")

        exponent = (1 << cls.TWO_ADICITY) // n
        return cls.ROOT_OF_UNITY.pow(exponent)

    def __repr__(self):
        return f"BabyBearExtElem({self.elems})"

    def __eq__(self, other):
        if isinstance(other, BabyBearExtElem):
            return self.elems == other.elems
        return False

    def __add__(self, other):
        if isinstance(other, BabyBearExtElem):
            return BabyBearExtElem([a + b for a, b in zip(self.elems, other.elems)])
        raise TypeError("Unsupported operand type for +")

    def __sub__(self, other):
        if isinstance(other, BabyBearExtElem):
            return BabyBearExtElem([a - b for a, b in zip(self.elems, other.elems)])
        raise TypeError("Unsupported operand type for -")

    def __mul__(self, other):
        if isinstance(other, BabyBearExtElem):
            a, b = self.elems, other.elems
            return BabyBearExtElem([
                a[0] * b[0] + self.NBETA * (a[1] * b[3] + a[2] * b[2] + a[3] * b[1]),
                a[0] * b[1] + a[1] * b[0] + self.NBETA * (a[2] * b[3] + a[3] * b[2]),
                a[0] * b[2] + a[1] * b[1] + a[2] * b[0] + self.NBETA * (a[3] * b[3]),
                a[0] * b[3] + a[1] * b[2] + a[2] * b[1] + a[3] * b[0]
            ])
        elif isinstance(other, BabyBear):
            return BabyBearExtElem([elem * other for elem in self.elems])
        raise TypeError("Unsupported operand type for *")

    def __neg__(self):
        return BabyBearExtElem([-elem for elem in self.elems])

    def inv(self):
        a = self.elems
        b0 = a[0] * a[0] + self.BETA * (a[1] * (a[3] + a[3]) - a[2] * a[2])
        b2 = a[0] * (a[2] + a[2]) - a[1] * a[1] + self.BETA * (a[3] * a[3])
        c = b0 * b0 + self.BETA * b2 * b2
        c_inv = c.inv()
        b0, b2 = b0 * c_inv, b2 * c_inv
        return BabyBearExtElem([
            a[0] * b0 + self.BETA * a[2] * b2,
            -a[1] * b0 + self.NBETA * a[3] * b2,
            -a[0] * b2 + a[2] * b0,
            a[1] * b2 - a[3] * b0
        ])

    def pow(self, n: int):
        result = BabyBearExtElem.one()
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
        if isinstance(other, BabyBearExtElem):
            return self * other.inv()
        elif isinstance(other, BabyBear):
            return self * BabyBearExtElem([other.inv()] + [BabyBear.zero()] * 3)
        raise TypeError("Unsupported operand type for /")

BabyBearExtElem.MULTIPLICATIVE_GENERATOR = BabyBearExtElem([BabyBear(8), BabyBear(1), BabyBear(0), BabyBear(0)])
BabyBearExtElem.ROOT_OF_UNITY = BabyBearExtElem([BabyBear(0), BabyBear(0), BabyBear(0), BabyBear(124907976)])

class BabyBearExtElem5:
    '''
    const W: BabyBear = BabyBear::new(2);
    const DTH_ROOT: BabyBear = BabyBear::new(815036133);
    const EXT_GENERATOR: [BabyBear; 5] = BabyBear::new_array([8, 1, 0, 0, 0]);
    const EXT_TWO_ADICITY: usize = 27;
    '''
    TWO_ADICITY = 27
    MULTIPLICATIVE_GENERATOR: ClassVar['BabyBearExtElem5']
    ROOT_OF_UNITY: ClassVar['BabyBearExtElem5']
    BETA = BabyBear(2)
    NBETA = BabyBear(BabyBear.P - 2)
    
    def __init__(self, elems: List[BabyBear]):
        assert len(elems) == 5, "BabyBearExtElem5 must have 5 elements"
        self.elems = elems

    @classmethod
    def zero(cls):
        return cls([BabyBear.zero()] * 5)

    @classmethod
    def one(cls):
        return cls([BabyBear.one()] + [BabyBear.zero()] * 4)

    @classmethod
    def random(cls):
        return cls([BabyBear.random() for _ in range(5)])

    @classmethod
    def nth_root_of_unity(cls, n: int):
        if not (n > 0 and (n & (n - 1)) == 0):  # Check if n is a power of 2
            raise ValueError("n must be a positive power of 2 for nth_root_of_unity.")
        
        if n > (1 << cls.TWO_ADICITY):  # n = 2^m, so m <= TWO_ADICITY
            raise ValueError(f"n (a power of 2) cannot exceed 2^{cls.TWO_ADICITY} for nth_root_of_unity.")

        exponent = (1 << cls.TWO_ADICITY) // n
        return cls.ROOT_OF_UNITY.pow(exponent)

    def __repr__(self):
        return f"BabyBearExtElem5({self.elems})"

    def __eq__(self, other):
        if isinstance(other, BabyBearExtElem5):
            return self.elems == other.elems
        return False

    def __add__(self, other):
        if isinstance(other, BabyBearExtElem5):
            return BabyBearExtElem5([a + b for a, b in zip(self.elems, other.elems)])
        raise TypeError("Unsupported operand type for +")

    def __sub__(self, other):
        if isinstance(other, BabyBearExtElem5):
            return BabyBearExtElem5([a - b for a, b in zip(self.elems, other.elems)])
        raise TypeError("Unsupported operand type for -")

    def __mul__(self, other):
        if isinstance(other, BabyBearExtElem5):
            a, b = self.elems, other.elems
            # Multiplication for quintic extension field
            # Using the irreducible polynomial x^5 - BETA
            c = [BabyBear.zero() for _ in range(5)]
            
            # Multiply as polynomials
            for i in range(5):
                for j in range(5):
                    if i + j < 5:
                        c[i + j] += a[i] * b[j]
                    else:
                        # Reduce modulo x^5 - BETA
                        # If x^n where n >= 5, replace with BETA * x^(n-5)
                        c[(i + j) % 5] += self.BETA * a[i] * b[j]
            
            return BabyBearExtElem5(c)
        elif isinstance(other, BabyBear):
            return BabyBearExtElem5([elem * other for elem in self.elems])
        raise TypeError("Unsupported operand type for *")

    def __neg__(self):
        return BabyBearExtElem5([-elem for elem in self.elems])

    def frobenius(self):
        """
        Computes the Frobenius automorphism a -> a^P.
        For a(X) = sum c_i X^i in F_P[X]/(X^5-BETA), this is sum c_i (phi X)^i,
        where phi = BETA^((P-1)/5).
        The new coefficients are c_i * phi^i.
        """
        # P = BabyBear.P
        # k = (P - 1) // 5
        # phi = self.BETA.pow(k)
        
        # Integer literal for k to avoid large number arithmetic during class loading
        # P = 15 * (1 << 27) + 1
        # (P - 1) // 5 = (15 * (1 << 27)) // 5 = 3 * (1 << 27)
        k = 3 * (1 << 27)
        
        phi = self.BETA.pow(k)
        
        new_elems = [BabyBear.zero()] * 5
        current_phi_power = BabyBear.one()
        for i in range(5):
            new_elems[i] = self.elems[i] * current_phi_power
            current_phi_power *= phi
            
        return BabyBearExtElem5(new_elems)

    def repeated_frobenius(self, count: int):
        """
        Computes the Frobenius automorphism count times.
        sigma^count(a).
        """
        res = self
        for _ in range(count):
            res = res.frobenius()
        return res

    def inv(self):
        # Based on 
        #   Norm(a) = a^(P^0) * a^(P^1) * a^(P^2) * a^(P^3) * a^(P^4)
        #   a.inv() = a^(P^4 + P^3 + P^2 + P) / Norm(a)
        
        # Calculate a^P, a^(P^2), a^(P^3), a^(P^4)
        a_p = self.frobenius()
        a_p2 = a_p.frobenius()
        a_p3 = a_p2.frobenius()
        a_p4 = a_p3.frobenius()

        # Calculate product of conjugates (a^P * a^(P^2) * a^(P^3) * a^(P^4))
        a_exp_q_plus_q_sq = a_p * a_p2  # a^P * a^(P^2)
        a_exp_q3_plus_q4 = a_p3 * a_p4  # a^(P^3) * a^(P^4)
        prod_conj = a_exp_q_plus_q_sq * a_exp_q3_plus_q4
        
        # Calculate norm value scalar
        pc_elems = prod_conj.elems
        a_elems = self.elems
        
        # Calculate the constant term of the norm
        w_coeff = BabyBear.zero()
        for i in range(1, 5):
            w_coeff += a_elems[i] * pc_elems[5-i]
            
        norm_val_scalar = a_elems[0] * pc_elems[0] + self.BETA * w_coeff
        
        # Inverse of the norm
        norm_inv_scalar = norm_val_scalar.inv()
        
        # Result is prod_conj * norm_inv_scalar
        return prod_conj * norm_inv_scalar

    def pow(self, n: int):
        result = BabyBearExtElem5.one()
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
        if isinstance(other, BabyBearExtElem5):
            return self * other.inv()
        elif isinstance(other, BabyBear):
            return self * BabyBearExtElem5([other.inv()] + [BabyBear.zero()] * 4)
        raise TypeError("Unsupported operand type for /")

# Initialize class variables after the class definition
BabyBearExtElem5.MULTIPLICATIVE_GENERATOR = BabyBearExtElem5([BabyBear(8), BabyBear(1), BabyBear(0), BabyBear(0), BabyBear(0)])
BabyBearExtElem5.ROOT_OF_UNITY = BabyBearExtElem5([BabyBear(0x1a427a41), BabyBear(0), BabyBear(0), BabyBear(0), BabyBear(0)])

# Example usage:
if __name__ == "__main__":
    a = BabyBear(5)
    b = BabyBear(7)
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
    print(f"a.inv() = {a.inv()}")
    print(f"a.pow(3) = {a.pow(3)}")
    # a.inv*a
    print(f"a.inv() * a = {a.inv() * a}")  # Should be 1

    x = BabyBearExtElem.random()
    y = BabyBearExtElem.random()
    print(f"x = {x}")
    print(f"y = {y}")
    print(f"x + y = {x + y}")
    print(f"x - y = {x - y}")
    print(f"x * y = {x * y}")
    print(f"x.inv() = {x.inv()}")
    print(f"x.pow(3) = {x.pow(3)}")
    print(f"x * x.inv() = {x * x.inv()}")  # Should be 1
    print(f"x_neg = {-x}, x + x_neg = {x+(-x)}")

    # Test new operators
    print(f"a ** 3 = {a ** 3}")  # Should be same as a.pow(3)
    print(f"a / b = {a / b}")    # Should be same as a * b.inv()
    print(f"x ** 3 = {x ** 3}")  # Should be same as x.pow(3)
    print(f"x / y = {x / y}")    # Should be same as x * y.inv()

    primitive_root_of_unity = BabyBear.ROOT_OF_UNITY
    for i in range(0, BabyBear.TWO_ADICITY + 1):
        print(f"2^{i}-th root of unity = {hex(BabyBear.nth_root_of_unity(2**i).value)}")
    '''
    same as baby_bear.rs in plonky3
    const TWO_ADIC_GENERATORS: Self::ArrayLike = &BabyBear::new_array([
            0x1, 0x78000000, 0x67055c21, 0x5ee99486, 0xbb4c4e4, 0x2d4cc4da, 0x669d6090, 0x17b56c64,
            0x67456167, 0x688442f9, 0x145e952d, 0x4fe61226, 0x4c734715, 0x11c33e2a, 0x62c3d2b1,
            0x77cad399, 0x54c131f4, 0x4cabd6a6, 0x5cf5713f, 0x3e9430e8, 0xba067a3, 0x18adc27d,
            0x21fd55bc, 0x4b859b3d, 0x3bd57996, 0x4483d85a, 0x3a26eef8, 0x1a427a41,
        ]);
    '''

    for i in range(BabyBear.TWO_ADICITY, BabyBearExtElem.TWO_ADICITY + 1):
        print(f"2^{i}-th root of unity = {BabyBearExtElem.nth_root_of_unity(2**i).elems}")

    '''
    2^28-th root of unity = [BabyBear(0), BabyBear(0), BabyBear(17094607), BabyBear(0)]
    17094607 is negative of 1996171314 in plonky3's code [0, 0, 1996171314, 0]
    '''

    for i in range(0, BabyBearExtElem5.TWO_ADICITY + 1):
        print(f"2^{i}-th root of unity = {BabyBearExtElem5.nth_root_of_unity(2**i).elems}")

    # Test BabyBearExtElem5
    x = BabyBearExtElem5.random()
    y = BabyBearExtElem5.random()
    print(f"x = {x}")
    print(f"y = {y}")
    print(f"x + y = {x + y}")
    print(f"x - y = {x - y}")
    print(f"x * y = {x * y}")
    print(f"x.inv() = {x.inv()}")
    print(f"x.pow(3) = {x.pow(3)}")
    print(f"x * x.inv() = {x * x.inv()}")  # Should be 1
    print(f"x_neg = {-x}, x + x_neg = {x+(-x)}")
    