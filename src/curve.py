from typing import NewType, Generic, TypeVar, Optional
from random import randint, seed, Random
# from galois import GF

from py_ecc.fields.field_elements import FQ
import py_ecc.bn128 as bn128
from py_ecc.utils import (
    prime_field_inv,
)

from utils import is_power_of_two, log_2

# primitive_root = 5

# G1Point = NewType("G1Point", tuple[b.FQ, b.FQ])
G2Point = NewType("G2Point", tuple[bn128.FQ2, bn128.FQ2])

BN128_CURVE_ORDER = bn128.curve_order

class Fr(FQ):
    field_modulus = bn128.curve_order

    ROOT_OF_UNITY = 19103219067921713944291392827692070036145651957329286315305642004821462161904
    MULTIPLICATIVE_GENERATOR = 5
    TWO_ADICITY = 28

    @classmethod
    def rand(cls, rndg: Optional[Random] = None) -> "Fr":
        if rndg is None:
            return cls(randint(1, cls.field_modulus - 1))
        return cls(rndg.randint(1, cls.field_modulus - 1))
    
    @classmethod
    def random(cls) -> "Fr":
        return cls.rand()
    
    @classmethod
    def rands(cls, rndg: Random, n: int) -> list["Fr"]:
        return [cls(rndg.randint(1, cls.field_modulus - 1)) for _ in range(n)]
    
    @classmethod
    def from_bytes(cls, b: bytes) -> "Fr":
        i = int.from_bytes(b, "big")
        return cls(i)
    
    def inv(self) -> "Fr":
        return Fr(prime_field_inv(self.n, self.field_modulus))
    
    def repr(self) -> str:
        k = self.field_modulus // 2
        if self.n < k:
            return f"{self.n}"
        else:
            return f"-{self.field_modulus - self.n}"
        
    def __str__(self) -> str:
        return self.repr()
        
    def __repr__(self) -> str:
        return self.repr()
    # Override the default (inefficient) __pow__ function in py_ecc.fields.field_elements.FQ
    def __pow__(self: "Fr", other: int) -> "Fr":
        return type(self)(pow(self.n, other, self.field_modulus))
        
    def __int__(self) -> int:
        return self.n
    
    def exp(self: "Fr", other: int) -> "Fr":
        return type(self)(pow(self.n, other, self.field_modulus))
    
    @classmethod
    def compute_root_of_unity(cls) -> "Fr":
        return cls(pow(cls.MULTIPLICATIVE_GENERATOR, ((cls.field_modulus - 1) // 2 ** cls.TWO_ADICITY), cls.field_modulus))
    
    @classmethod
    def root_of_unity(cls) -> "Fr":
        return cls(cls.ROOT_OF_UNITY)
    
    @classmethod
    def multiplicative_generator(cls) -> "Fr":
        return cls(cls.MULTIPLICATIVE_GENERATOR)

    @classmethod
    def nth_root_of_unity(cls, n: int) -> "Fr":
        assert is_power_of_two(n), "n must be a power of two"
        return cls(pow(cls.ROOT_OF_UNITY, 2**(cls.TWO_ADICITY - log_2(n)), cls.field_modulus))

Fp = NewType("Fp", bn128.FQ)

class G1Point:
    def __init__(self, x: Fp, y: Fp, is_zero: bool = False):
        self.x = x
        self.y = y
        self.is_zero = is_zero
    
    @classmethod
    def ec_gen(cls) -> "G1Point":
        return cls(bn128.G1[0], bn128.G1[1])

    def __eq__(self, other: "G1Point") -> bool:
        if self.is_zero and other.is_zero:
            return True
        elif not self.is_zero and not other.is_zero:
            return self.x == other.x and self.y == other.y
        return False

    def __add__(self, other: "G1Point") -> "G1Point":
        if self.is_zero:
            return other
        if other.is_zero:
            return self
        result = bn128.add((self.x, self.y), (other.x, other.y))
        return G1Point(result[0], result[1])

    def __sub__(self, other: "G1Point") -> "G1Point":
        if self == G1Point.zero():
            return other
        if other == G1Point.zero():
            return self
        result = bn128.add((self.x, self.y), bn128.neg((other.x, other.y)))
        return G1Point(result[0], result[1])
    
    def __neg__(self) -> "G1Point":
        g = bn128.neg((self.x, self.y))
        return G1Point(g[0], g[1])
    
    def ec_mul(self, coeff: Fr) -> "G1Point":
        if self.is_zero:
            return G1Point.zero()
        if coeff == Fr.zero():
            return G1Point.zero()
        h = bn128.multiply((self.x, self.y), coeff.n)
        return G1Point(h[0], h[1])
    
    # def __mul__(self, other: Fr) -> "G1Point":
    #     return ec_mul(self, other)

    # def __rmul__(self, other: Fr) -> "G1Point":
    #     return ec_mul(self, other)

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"
    
    def __repr__(self) -> str:
        return f"G1Point({self.x}, {self.y})"
    
    def __hash__(self) -> int:
        return hash((self.x, self.y))
    
    def zero() -> "G1Point":
        return G1Point(bn128.Z1, bn128.Z1, is_zero=True)


def ec_mul(pt: G1Point, coeff: Fr) -> G1Point:
    assert isinstance(pt, G1Point), f"pt is not a G1Point"

    if pt.is_zero:
        return G1Point.zero()
    if coeff == Fr.zero():
        return G1Point.zero()
    h = bn128.multiply((pt.x, pt.y), coeff.n)
    return G1Point(h[0], h[1])

Fp2 = NewType("Fp2", bn128.FQ2)

class G2Point:
    def __init__(self, x: Fp2, y: Fp2, is_zero: bool = False):
        self.x = x
        self.y = y
        self.is_zero = is_zero
    
    @classmethod
    def ec_gen(cls) -> "G2Point":
        return cls(bn128.G2[0], bn128.G2[1])

    def __eq__(self, other: "G2Point") -> bool:
        if self.is_zero and other.is_zero:
            return True
        elif not self.is_zero and not other.is_zero:
            return self.x == other.x and self.y == other.y
        return False

    def __add__(self, other: "G2Point") -> "G2Point":
        if self.is_zero:
            return other
        if other.is_zero:
            return self
        result = bn128.add((self.x, self.y), (other.x, other.y))
        return G2Point(result[0], result[1])

    def __sub__(self, other: "G2Point") -> "G2Point":
        if self == G2Point.zero():
            return other
        if other == G2Point.zero():
            return self
        result = bn128.add((self.x, self.y), bn128.neg((other.x, other.y)))
        return G2Point(result[0], result[1])
    
    def __neg__(self) -> "G2Point":
        g = bn128.neg((self.x, self.y))
        return G2Point(g[0], g[1])
    
    def ec_mul(self, coeff: Fr) -> "G2Point":
        if self.is_zero:
            return G2Point.zero()
        if coeff == Fr.zero():
            return G2Point.zero()
        h = bn128.multiply((self.x, self.y), coeff.n)
        return G2Point(h[0], h[1])
    
    # def __mul__(self, other: Fr) -> "G1Point":
    #     return ec_mul(self, other)

    # def __rmul__(self, other: Fr) -> "G1Point":
    #     return ec_mul(self, other)

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"
    
    def __repr__(self) -> str:
        return f"G2Point({self.x}, {self.y})"
    
    def __hash__(self) -> int:
        return hash((self.x, self.y))
    
    def zero() -> "G2Point":
        return G2Point(bn128.Z2, bn128.Z2, is_zero=True)

def ec_mul_group2(pt: G2Point, coeff: Fr) -> G2Point:
    assert isinstance(pt, G2Point), f"pt is not a G2Point"

    if pt.is_zero:
        return G2Point.zero()
    if coeff == Fr.zero():
        return G2Point.zero()
    h = bn128.multiply((pt.x, pt.y), coeff.n)
    return G2Point(h[0], h[1])

# def ec_gen_group2() -> G2Point:
#     return bn128.G2

# def ec_id_group2() -> G2Point:
#     return b.Z2

def ec_lincomb(pairs: list[tuple[G1Point, Fr]]) -> G1Point:
    assert len(pairs) > 0, "Pairs must be non-empty"
    for i in range(len(pairs)):
        assert isinstance(pairs[i][0], G1Point), f"pairs[{i}][0] is not a G1Point"
        assert isinstance(pairs[i][1], Fr), f"pairs[{i}][1] is not a Fr"

    o = bn128.Z1
    for pt, coeff in pairs:
        o = bn128.add(o, ec_mul(pt, coeff))
    return o

def ec_pairing_check(Ps: list[G1Point], Qs: list[G2Point]) -> bool:
    """
        Check the pairing equation

            e(Q_0, P_0) * e(Q_1, P_1) * ... * e(Q_n, P_n) ?= FQ12(1)
        Args:
            Ps: list of G1Points
            Qs: list of G2Points
        Returns:
            bool: True if the pairing equation holds, False otherwise
    """
    assert len(Ps) == len(Qs), f"Incompatible lengths: len(Ps)= {len(Ps)}, len(Qs)= {len(Qs)}"
    for i in range(len(Ps)):
        assert isinstance(Ps[i], G1Point), f"Ps[{i}] is not a G1Point"
        assert isinstance(Qs[i], G2Point), f"Qs[{i}] is not a G2Point"
    
    prod = bn128.FQ12.one()
    for i in range(len(Ps)):
        p = Ps[i]
        q = Qs[i]
        prod *= bn128.pairing((q.x, q.y), (p.x, p.y))
    return prod == bn128.FQ12.one()


# def poly_test():

#     Fr = Scalar(BN128_CURVE_ORDER)

#     vals = [1, 2, 3, 4]
#     vals_scalar = [Scalar(int(x)) for x in vals]
#     roots_of_unity = Scalar.roots_of_unity(4)

#     poly_lag = Polynomial(vals_scalar, Basis.LAGRANGE)
#     poly_coeff = poly_lag.ifft()
#     points = roots_of_unity + [Scalar(2), Scalar(3), Scalar(4)]
#     for i in range(len(points)):
#       point = points[i]
#       eval_lag = poly_lag.barycentric_eval(point)
#       coeff_eval = poly_coeff.coeff_eval(point)
#       assert eval_lag == coeff_eval

#     quo = poly_coeff / Scalar(2)
#     print("quo: ", quo.values)

if __name__ == "__main__":
    print(f"type(b.G1): {type(bn128.G1)}")
    print(f"type(b.Z1): {type(bn128.Z1)}")
    print(f"b.curve_order: {bn128.curve_order}")
    print(f"Fr(3) + Fr(9): {Fr(3) + Fr(9)}")
    print(f"Fr(3) * Fr(4): {Fr(3) * Fr(4)}")
    print(f"Fr(3) - Fr(5): {Fr(3) - Fr(5)}")
    print(f"Fr(3) / Fr(5): {Fr(3) / Fr(5)}")
    print(f"Fr(3) ** 2: {Fr(3) ** 2}")


    # test root of unity

    print(f"Fr.root_of_unity: {Fr.compute_root_of_unity()}")

    print(f"Fr.nth_root_of_unity(2): {Fr.nth_root_of_unity(2)}")
    print(f"Fr.nth_root_of_unity(2)**2: {Fr.nth_root_of_unity(2)**2}")
    assert Fr.nth_root_of_unity(2)**2 == Fr.one()
    print(f"Fr.nth_root_of_unity(256): {Fr.nth_root_of_unity(256)}")
    assert Fr.nth_root_of_unity(256)**256 == Fr.one()

    a = Fr(8)
    g = G1Point.ec_gen()
    print(f"g: {g}")
    print(f" > ec_mul(g, a): {ec_mul(g, a)}")
    # print(f" > ec_mul(g, a): {ec_add(ec_mul(g, Fr(3)), ec_mul(g, Fr(5))) }")
    print(f" > ec_mul(g, a): {ec_mul(g, Fr(3)) + ec_mul(g, Fr(5)) }")

    a = G1Point(bn128.G1[0], bn128.G1[1])
    b = a + a
    print(f"b: {b}")
    print(f"b.G1.double(): {bn128.double(bn128.G1)}")

    g2 = G2Point.ec_gen()
    print(f"g2: {g2}")
    g2_4 = g2.ec_mul(Fr(4))
    g1 = G1Point.ec_gen()
    g1_4 = ec_mul(g1, Fr(4))
    assert bn128.pairing([g2.x, g2.y], (g1_4.x, g1_4.y)) == bn128.pairing([g2_4.x, g2_4.y], (g1.x, g1.y))
    checked = ec_pairing_check([g1_4, -g1], [g2, g2_4])
    print(f"checked: {checked}")

    # Test case 2: 
    #   e(4*g1, 3*g2) = e(6*g1, 2*g2)

    g1_3 = ec_mul(g1, Fr(3))

    g2_2 = ec_mul_group2(g2, Fr(2))
    g1_6 = ec_mul(g1, Fr(6))

    assert bn128.pairing([g2_4.x, g2_4.y], (g1_3.x, g1_3.y)) == bn128.pairing([g2_2.x, g2_2.y], (g1_6.x, g1_6.y))
    checked = ec_pairing_check([g1_3, -g1_6], [g2_4, g2_2])
    print(f"checked: {checked}")
