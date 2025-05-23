import random
from typing import List

def convert_int_to_goldilocks(func):
    def wrapper(self, other):
        if isinstance(other, int):
            other = Goldilocks(other)
        return func(self, other)
    return wrapper

class Goldilocks:
    # The Goldilocks prime: 2^64 - 2^32 + 1
    P = (1 << 64) - (1 << 32) + 1
    
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

    def __repr__(self):
        return f"Goldilocks({self.value})"

    def __eq__(self, other):
        if isinstance(other, Goldilocks):
            return self.value == other.value
        return False

    @convert_int_to_goldilocks
    def __add__(self, other):
        return Goldilocks(self.add(self.value, other.value))

    @convert_int_to_goldilocks
    def __sub__(self, other):
        return Goldilocks(self.sub(self.value, other.value))

    @convert_int_to_goldilocks
    def __mul__(self, other):
        return Goldilocks(self.mul(self.value, other.value))

    def __neg__(self):
        return Goldilocks(self.P - self.value)

    def inv(self):
        # From Fermat's little theorem, in a prime field F_p, the inverse of a is a^(p-2)
        return self.pow(self.P - 2)

    def pow(self, n: int):
        result = Goldilocks.one()
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

    @convert_int_to_goldilocks
    def __truediv__(self, other):
        return self * other.inv()

    def __radd__(self, other):
        return Goldilocks(other) + self

    def __rsub__(self, other):
        return Goldilocks(other) - self

    def __rmul__(self, other):
        return Goldilocks(other) * self

    def __rtruediv__(self, other):
        return Goldilocks(other) / self

    @classmethod
    def new_array(cls, values):
        """Helper method for creating arrays of field elements"""
        return [cls(v) for v in values]

    @classmethod
    def new_2d_array(cls, values):
        """Helper method for creating 2D arrays of field elements"""
        return [[cls(v) for v in row] for row in values]


class GoldilocksExtElem2:
    W: Goldilocks = Goldilocks(7)  # The parameter for the quadratic extension

    def __init__(self, elems: List[Goldilocks]):
        assert len(elems) == 2, "ExtElem2 must have 2 elements"
        self.elems = elems

    @classmethod
    def zero(cls):
        return cls([Goldilocks.zero()] * 2)

    @classmethod
    def one(cls):
        return cls([Goldilocks.one()] + [Goldilocks.zero()])

    @classmethod
    def random(cls):
        return cls([Goldilocks.random() for _ in range(2)])

    def __repr__(self):
        return f"GoldilocksExtElem2({self.elems})"

    def __eq__(self, other):
        if isinstance(other, GoldilocksExtElem2):
            return self.elems == other.elems
        return False

    def __add__(self, other):
        if isinstance(other, GoldilocksExtElem2):
            return GoldilocksExtElem2([a + b for a, b in zip(self.elems, other.elems)])
        raise TypeError("Unsupported operand type for +")

    def __sub__(self, other):
        if isinstance(other, GoldilocksExtElem2):
            return GoldilocksExtElem2([a - b for a, b in zip(self.elems, other.elems)])
        raise TypeError("Unsupported operand type for -")

    def __mul__(self, other):
        if isinstance(other, GoldilocksExtElem2):
            # Implement multiplication using the binomial representation
            # For quadratic extension F[x]/(x^2 - W) where W = 7
            a = self.elems
            b = other.elems
            
            # (a0 + a1*x)(b0 + b1*x) = (a0*b0 + W*a1*b1) + (a0*b1 + a1*b0)*x
            c0 = a[0] * b[0] + self.W * (a[1] * b[1])
            c1 = a[0] * b[1] + a[1] * b[0]
            
            return GoldilocksExtElem2([c0, c1])
        elif isinstance(other, Goldilocks):
            return GoldilocksExtElem2([elem * other for elem in self.elems])
        raise TypeError("Unsupported operand type for *")

    def __neg__(self):
        return GoldilocksExtElem2([-elem for elem in self.elems])

    def inv(self):
        a = self.elems
        # For quadratic extension F[x]/(x^2 - W)
        # The inverse of a0 + a1*x is (a0 - a1*x)/(a0^2 - W*a1^2)
        denom = a[0] * a[0] - self.W * (a[1] * a[1])
        denom_inv = denom.inv()
        return GoldilocksExtElem2([
            a[0] * denom_inv,
            -a[1] * denom_inv
        ])

    def pow(self, n: int):
        result = GoldilocksExtElem2.one()
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
        if isinstance(other, GoldilocksExtElem2):
            return self * other.inv()
        elif isinstance(other, Goldilocks):
            return self * GoldilocksExtElem2([other.inv()] + [Goldilocks.zero()])
        raise TypeError("Unsupported operand type for /")


class GoldilocksExtElem5:
    W: Goldilocks = Goldilocks(3)  # The parameter for the 5th extension (x^5 - 3)

    def __init__(self, elems: List[Goldilocks]):
        assert len(elems) == 5, "ExtElem5 must have 5 elements"
        self.elems = elems

    @classmethod
    def zero(cls):
        return cls([Goldilocks.zero()] * 5)

    @classmethod
    def one(cls):
        return cls([Goldilocks.one()] + [Goldilocks.zero()] * 4)

    @classmethod
    def random(cls):
        return cls([Goldilocks.random() for _ in range(5)])

    def __repr__(self):
        return f"GoldilocksExtElem5({self.elems})"

    def __eq__(self, other):
        if isinstance(other, GoldilocksExtElem5):
            return self.elems == other.elems
        return False

    def __add__(self, other):
        if isinstance(other, GoldilocksExtElem5):
            return GoldilocksExtElem5([a + b for a, b in zip(self.elems, other.elems)])
        raise TypeError("Unsupported operand type for +")

    def __sub__(self, other):
        if isinstance(other, GoldilocksExtElem5):
            return GoldilocksExtElem5([a - b for a, b in zip(self.elems, other.elems)])
        raise TypeError("Unsupported operand type for -")

    def __mul__(self, other):
        if isinstance(other, GoldilocksExtElem5):
            # Implement multiplication using the polynomial representation
            # For 5th extension F[x]/(x^5 - W) where W = 3
            a = self.elems
            b = other.elems
            
            # First compute the full polynomial multiplication
            # (a0 + a1*x + a2*x^2 + a3*x^3 + a4*x^4)(b0 + b1*x + b2*x^2 + b3*x^3 + b4*x^4)
            # Then reduce modulo x^5 - W
            c = [Goldilocks.zero()] * 9  # Temporary array for polynomial multiplication
            
            # Compute the full polynomial multiplication
            for i in range(5):
                for j in range(5):
                    c[i + j] += a[i] * b[j]
            
            # Reduce modulo x^5 - W
            # For each term x^k where k >= 5, replace x^k with W * x^(k-5)
            for i in range(8, 4, -1):
                c[i - 5] += self.W * c[i]
            
            return GoldilocksExtElem5(c[:5])
        elif isinstance(other, Goldilocks):
            return GoldilocksExtElem5([elem * other for elem in self.elems])
        raise TypeError("Unsupported operand type for *")

    def __neg__(self):
        return GoldilocksExtElem5([-elem for elem in self.elems])

    def frobenius(self):
        """
        Computes the Frobenius automorphism a -> a^P.
        For a(X) = sum c_i X^i in F_P[X]/(X^5-W), this is sum c_i (phi X)^i,
        where phi = W^((P-1)/5).
        The new coefficients are c_i * phi^i.
        """
        # P = Goldilocks.P
        # k = (P - 1) // 5
        # phi = self.W.pow(k) # self.W is Goldilocks(3)
        
        # (P-1) = (1<<64) - (1<<32)
        # k = ((1 << 64) - (1 << 32)) // 5
        # Integer literal for k to avoid large number arithmetic during class loading if P is complex
        # (18446744073709551616 - 4294967296) // 5 = 18446744069414584320 // 5 = 3689348813882916864
        k = 3689348813882916864 
        
        phi = self.W.pow(k)
        
        new_elems = [Goldilocks.zero()] * 5
        current_phi_power = Goldilocks.one()
        for i in range(5):
            new_elems[i] = self.elems[i] * current_phi_power
            current_phi_power *= phi
            
        return GoldilocksExtElem5(new_elems)

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
        # prod_conj = a^P * a^(P^2) * a^(P^3) * a^(P^4)
        # Norm(a) = a * prod_conj
        
        a = self

        # Calculate a^P, a^(P^2), a^(P^3), a^(P^4)
        # These are sigma(a), sigma^2(a), sigma^3(a), sigma^4(a)
        a_p = a.frobenius()
        a_p2 = a_p.frobenius() # More efficient than a.repeated_frobenius(2) if building up
        a_p3 = a_p2.frobenius()
        a_p4 = a_p3.frobenius()

        # prod_conj_parts = [a_p, a_p2, a_p3, a_p4]
        # prod_conj = GoldilocksExtElem5.one()
        # for p in prod_conj_parts:
        #    prod_conj *= p
        # More direct from Rust code:
        # a_exp_q = a.frobenius() -> a_p
        # term_a_mul_a_exp_q = a * a_exp_q  (a * a^P)
        # a_exp_q_plus_q_sq = term_a_mul_a_exp_q.frobenius() ( (a * a^P)^P = a^P * a^(P^2) )
        
        a_exp_q_plus_q_sq = a_p * a_p2 # This is a^P * a^(P^2)

        # term_repeated_frob_arg = a_exp_q_plus_q_sq
        # a_exp_q3_plus_q4 = term_repeated_frob_arg.repeated_frobenius(2) -> ( (a^P * a^(P^2)) ^ (P^2) ) = a^(P^3) * a^(P^4)
        # For (X)^(P^2), this means applying frobenius twice to X in the expression
        # (a^P * a^(P^2)) applied with frob twice is (a^P)^P^2 * (a^P^2)^P^2 = a^(P^3) * a^(P^4)
        
        a_exp_q3_plus_q4 = a_p3 * a_p4 # This is a^(P^3) * a^(P^4)
        
        prod_conj = a_exp_q_plus_q_sq * a_exp_q3_plus_q4 # (a^P * a^(P^2)) * (a^(P^3) * a^(P^4))

        # Calculate norm_val_scalar = Norm(a)
        # Norm(a) is the constant term of a * prod_conj, reduced by X^5 = W.
        # If C(X) = a(X) * prod_conj(X) = sum c_k X^k, then
        # constant term of C(X) mod (X^5 - W) is
        # c_0 + c_5*W + c_6*W*X + ... no, this is if C(X) is the direct product.
        # The product a * prod_conj should result in a scalar (elem[0] non-zero, rest zero)
        # norm_full_product = a * prod_conj
        # assert all(e == Goldilocks.zero() for e in norm_full_product.elems[1:]), "Norm is not scalar"
        # norm_val_scalar = norm_full_product.elems[0]

        # Direct calculation of norm's constant term:
        # Norm_a = a_0 * pc_0 + W * (a_1*pc_4 + a_2*pc_3 + a_3*pc_2 + a_4*pc_1)
        pc_elems = prod_conj.elems
        a_elems = self.elems
        
        # w_coeff = a_1*pc_4 + a_2*pc_3 + a_3*pc_2 + a_4*pc_1
        w_coeff = Goldilocks.zero()
        for i in range(1, 5):
            w_coeff += a_elems[i] * pc_elems[5-i]
            
        norm_val_scalar = a_elems[0] * pc_elems[0] + self.W * w_coeff
        
        norm_inv_scalar = norm_val_scalar.inv()
        
        # Result is prod_conj * norm_inv_scalar
        return prod_conj * norm_inv_scalar

    def pow(self, n: int):
        result = GoldilocksExtElem5.one()
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
        if isinstance(other, GoldilocksExtElem5):
            return self * other.inv()
        elif isinstance(other, Goldilocks):
            return self * GoldilocksExtElem5([other.inv()] + [Goldilocks.zero()] * 4)
        raise TypeError("Unsupported operand type for /")


# Example usage:
if __name__ == "__main__":
    a = Goldilocks(2882343476)
    b = Goldilocks(0xfedcba0987654321)
    print(f"a = {a}")
    print(f"b = {b}")
    print(f"a + b = {a + b}")
    print(f"a * b = {a * b}")
    print(f"a.inv() = {a.inv()}")
    print(f"a.inv() * a = {a.inv() * a}")  # Should be 1

    # Test 2nd extension
    print("\nTesting 2nd extension:")
    x2 = GoldilocksExtElem2([Goldilocks(1), Goldilocks(2)])
    print(f"x2 = {x2}")
    print(f"x2.inv() = {x2.inv()}")
    x2_inv = x2.inv()
    print(f"x2 * x2_inv = {x2 * x2_inv}")  # Should be 1
    y2 = GoldilocksExtElem2.random()
    print(f"y2 = {y2}")
    print(f"x2 + y2 = {x2 + y2}")
    print(f"x2 * y2 = {x2 * y2}")

    # Test 5th extension
    x5 = GoldilocksExtElem5([Goldilocks(1), Goldilocks(2),
                            Goldilocks(3), Goldilocks(4),
                            Goldilocks(5)])
    print(f"\nTesting 5th extension:")
    print(f"x5 = {x5}")
    print(f"x5.inv() = {x5.inv()}")
    x5_inv = x5.inv()
    print(f"x5 * x5_inv = {x5 * x5_inv}")  # Should be 1
    y5 = GoldilocksExtElem5.random()
    print(f"y5 = {y5}")
    print(f"x5 + y5 = {x5 + y5}")
    print(f"x5 * y5 = {x5 * y5}")
