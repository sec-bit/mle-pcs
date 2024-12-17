import random

class Mersenne31:
    P: int = 2**31 -1
    value: int
    def __init__(self, value: int):
        self.value = value % self.P

    @classmethod
    def zero(cls):
        return cls(0)

    @classmethod
    def one(cls):
        return cls(1)

    @classmethod
    def neg_one(cls):
        return cls(cls.P - 1)

    @classmethod
    def random(cls):
        return cls(random.randint(0, cls.P - 1))

    def __add__(self, other):
        if isinstance(other, type(self)):
            return type(self)((self.value + other.value) % self.P)
        raise TypeError("Unsupported operand type for +")

    def __sub__(self, other):
        if isinstance(other, type(self)):
            return type(self)((self.value - other.value) % self.P)
        raise TypeError("Unsupported operand type for -")

    def __mul__(self, other):
        if isinstance(other, type(self)):
            return type(self)((self.value * other.value) % self.P)
        raise TypeError("Unsupported operand type for *")

    def __neg__(self):
        return type(self)(self.P - self.value if self.value != 0 else 0)

    def __repr__(self):
        return f"Mersenne31({self.value})"

    def inv(self):
        if self.value == 0:
            raise ZeroDivisionError("Cannot invert zero")
        return self.pow(self.P - 2)

    def pow(self, n: int):
        result = type(self).one()
        base = self
        while n > 0:
            if n & 1:
                result *= base
            base *= base
            n >>= 1
        return result

    def square(self):
        return self * self

class Complex:
    """ Irreducible polynomial: i^2 + 1 = 0 """
    def __init__(self, real: Mersenne31, imag: Mersenne31):
        self.real: Mersenne31 = real
        self.imag: Mersenne31 = imag

    @classmethod
    def zero(cls):
        return cls(Mersenne31.zero(), Mersenne31.zero())

    @classmethod
    def one(cls):
        return cls(Mersenne31.one(), Mersenne31.zero())

    @classmethod
    def random(cls):
        return cls(Mersenne31.random(), Mersenne31.random())

    def __repr__(self):
        return f"Complex({self.real}, {self.imag}i)"

    def __eq__(self, other):
        if isinstance(other, Complex):
            return self.real == other.real and self.imag == other.imag
        return False

    def __add__(self, other):
        if isinstance(other, Complex):
            return Complex(self.real + other.real, self.imag + other.imag)
        raise TypeError("Unsupported operand type for +")

    def __sub__(self, other):
        if isinstance(other, Complex):
            return Complex(self.real - other.real, self.imag - other.imag)
        raise TypeError("Unsupported operand type for -")

    def __mul__(self, other):
        if isinstance(other, Complex):
            return Complex(
                self.real * other.real - self.imag * other.imag,
                self.real * other.imag + self.imag * other.real
            )
        raise TypeError("Unsupported operand type for *")

    def __neg__(self):
        return Complex(-self.real, -self.imag)

    def inv(self):
        norm = self.real.square() + self.imag.square()
        norm_inv = norm.inv()
        return Complex(self.real * norm_inv, -self.imag * norm_inv)

    def conjugate(self):
        return Complex(self.real, -self.imag)

    def norm(self):
        return self.real.square() + self.imag.square()

class Mersenne31QuadExtension:
    """ Irreducible polynomial: w^2 + 1 + 2i = 0"""
    def __init__(self, c0: Complex, c1: Complex):
        self.c0: Complex = c0
        self.c1: Complex = c1

    @classmethod
    def zero(cls):
        return cls(Complex.zero(), Complex.zero())

    @classmethod
    def one(cls):
        return cls(Complex.one(), Complex.zero())

    @classmethod
    def random(cls):
        return cls(Complex.random(), Complex.random())

    def __repr__(self):
        return f"QuadExtension({self.c0}, {self.c1}w)"

    def __eq__(self, other):
        if isinstance(other, Mersenne31QuadExtension):
            return self.c0 == other.c0 and self.c1 == other.c1
        return False

    def __add__(self, other):
        if isinstance(other, Mersenne31QuadExtension):
            return Mersenne31QuadExtension(self.c0 + other.c0, self.c1 + other.c1)
        raise TypeError("Unsupported operand type for +")

    def __sub__(self, other):
        if isinstance(other, Mersenne31QuadExtension):
            return Mersenne31QuadExtension(self.c0 - other.c0, self.c1 - other.c1)
        raise TypeError("Unsupported operand type for -")

    def __mul__(self, other):
        if isinstance(other, Mersenne31QuadExtension):
            # (a + bw)(c + dw) = ac + (ad + bc)w + bdw^2
            # w^2 = -1 - 2i
            # = (ac - bd(-1 - 2i)) + (ad + bc)w
            # = (ac + bd + 2bdi) + (ad + bc)w
            c0 = self.c0 * other.c0 + (self.c1 * other.c1 * Complex(Mersenne31(1), Mersenne31(2)))
            c1 = self.c0 * other.c1 + self.c1 * other.c0
            return Mersenne31QuadExtension(c0, c1)
        raise TypeError("Unsupported operand type for *")

    def __neg__(self):
        return Mersenne31QuadExtension(-self.c0, -self.c1)

    def conjugate(self):
        return Mersenne31QuadExtension(self.c0, -self.c1)

    def norm(self):
        # compute x * x.conjugate()
        return self * self.conjugate()

    def inv(self):
        # compute inverse: norm = multiply all conjugates together
        # for example: a.norm() = a * a.conj1 * a.conj2 * ... * a.conjn
        # so a.inv() =  a * a.conj1 * a.conj2 * ... * a.conjn / norm
        norm = self.norm().c0
        norm_inv = norm.inv()
        conj = self.conjugate()
        return Mersenne31QuadExtension(conj.c0 * norm_inv, conj.c1 * norm_inv)

# Example usage:
if __name__ == "__main__":
    print("Testing Mersenne31Complex:")
    a = Complex(Mersenne31(5), Mersenne31(7))
    b = Complex(Mersenne31(3), Mersenne31(2))
    print(f"a = {a}")
    print(f"b = {b}")
    print(f"a + b = {a + b}")
    print(f"a - b + b = {a - b + b}")
    print(f"a * b = {a * b}")
    print(f"a.inv() = {a.inv()}")
    print(f"a * a.inv() = {a * a.inv()}")

    print("\nTesting Mersenne31QuadExtension:")
    x = Mersenne31QuadExtension.random()
    y = Mersenne31QuadExtension.random()
    print(f"x = {x}")
    print(f"y = {y}")
    print(f"x + y = {x + y}")
    print(f"x * y = {x * y}")
    print(f"x * y * y.inv() = {x * y * y.inv()}")
    print(f"x.inv() = {x.inv()}")
    print(f"x * x.inv() = {x * x.inv()}")
