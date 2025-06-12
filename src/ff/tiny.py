from typing import Optional, Union
from random import Random, randint
from utils import is_power_of_two, prime_field_inv, log_2

ORDER = 193
ROOT_OF_UNITY = 125
MULTIPLICATIVE_GENERATOR = 5
TWO_ADICITY = 6

class PrimeField:

    # field_modulus = 193
    # ROOT_OF_UNITY = 125
    # MULTIPLICATIVE_GENERATOR = 5
    # TWO_ADICITY = 6

    def __init__(self, val) -> None:
        if self.field_modulus is None:
            raise AttributeError("Field Modulus hasn't been specified")

        if isinstance(val, PrimeField):
            self.n = val.n % self.field_modulus
        elif int(val) == int(val):
            self.n = int(val) % self.field_modulus
        else:
            raise TypeError(
                "Expected an int or PrimeField object, but got object of type {}"
                .format(type(val))
            )

    def __add__(self, other) -> "PrimeField":
        if isinstance(other, PrimeField):
            on = other.n
        elif int(other) == int(other):
            on = int(other)
        else:
            raise TypeError(
                "Expected an int or Fp object, but got object of type {}"
                .format(type(other))
            )

        return type(self)((self.n + on) % self.field_modulus)

    def __mul__(self, other) -> "PrimeField":
        if isinstance(other, PrimeField):
            on = other.n
        elif int(other) == int(other):
            on = int(other)
        else:
            raise TypeError(
                "Expected an int or PrimeField object, but got object of type {}"
                .format(type(other))
            )

        return type(self)((self.n * on) % self.field_modulus)

    def __rmul__(self, other) -> "PrimeField":
        return self * other

    def __radd__(self, other) -> "PrimeField":
        return self + other

    def __rsub__(self, other) -> "PrimeField":
        if isinstance(other, PrimeField):
            on = other.n
        elif int(other) == int(other):
            on = int(other)
        else:
            raise TypeError(
                "Expected an int or PrimeField object, but got object of type {}"
                .format(type(other))
            )

        return type(self)((on - self.n) % self.field_modulus)

    def __sub__(self, other) -> "PrimeField":
        if isinstance(other, PrimeField):
            on = other.n
        elif int(other) == int(other):
            on = other
        else:
            raise TypeError(
                "Expected an int or PrimeField object, but got object of type {}"
                .format(type(other))
            )

        return type(self)((self.n - on) % self.field_modulus)

    def __div__(self, other) -> "PrimeField":
        if isinstance(other, PrimeField):
            on = other.n
        elif int(other) == int(other):
            on = int(other)
        else:
            raise TypeError(
                "Expected an int or PrimeField object, but got object of type {}"
                .format(type(other))
            )

        return type(self)(
            self.n * prime_field_inv(on, self.field_modulus) % self.field_modulus
        )

    def __truediv__(self, other) -> "PrimeField":
        return self.__div__(other)

    def __rdiv__(self, other) -> "PrimeField":
        if isinstance(other, PrimeField):
            on = other.n
        elif int(other) == int(other):
            on = int(other)
        else:
            raise TypeError(
                "Expected an int or PrimeField object, but got object of type {}"
                .format(type(other))
            )

        return type(self)(
            prime_field_inv(self.n, self.field_modulus) * on % self.field_modulus
        )

    def __rtruediv__(self, other) -> "PrimeField":
        return self.__rdiv__(other)

    # def __pow__(self, other: Union["PrimeField", Integer]) -> "PrimeField":
    #     if other == 0:
    #         return type(self)(1)
    #     elif other == 1:
    #         return type(self)(self.n)
    #     elif other % 2 == 0:
    #         return (self * self) ** (other // 2)
    #     else:
    #         return ((self * self) ** (other // 2)) * self

    def __eq__(self, other) -> bool:
        if isinstance(other, PrimeField):
            return self.n == other.n
        elif int(other) == int(other):
            return self.n == other
        else:
            raise TypeError(
                "Expected an int or PrimeField object, but got object of type {}"
                .format(type(other))
            )

    def __ne__(self, other) -> bool:
        return not self == other

    def __neg__(self) -> "PrimeField":
        return type(self)(-self.n)

    def __str__(self) -> str:
        return self.repr()
        
    def __repr__(self) -> str:
        return self.repr()
    
    # Override the default (inefficient) __pow__ function in py_ecc.fields.field_elements.FQ
    def __pow__(self, other: int) -> "PrimeField":
        return type(self)(pow(self.n, other, self.field_modulus))
    
    # def __repr__(self) -> str:
    #     return repr(self.n)

    def __int__(self) -> int:
        return self.n

    @classmethod
    def one(cls) -> "PrimeField":
        return cls(1)

    @classmethod
    def zero(cls) -> "PrimeField":
        return cls(0)
    
    @classmethod
    def neg_one(cls) -> "PrimeField":
        return cls(cls.field_modulus - 1)

    @classmethod
    def rand(cls, rndg: Optional[Random] = None) -> "PrimeField":
        if rndg is None:
            return cls(randint(1, cls.field_modulus - 1))
        return cls(rndg.randint(1, cls.field_modulus - 1))
    
    @classmethod
    def random(cls) -> "PrimeField":
        return cls.rand()
    
    @classmethod
    def rands(cls, rndg: Random, n: int) -> list["PrimeField"]:
        return [cls(rndg.randint(1, cls.field_modulus - 1)) for _ in range(n)]
    
    @classmethod
    def from_bytes(cls, b: bytes) -> "PrimeField":
        i = int.from_bytes(b, "big")
        return cls(i)
    
    def inv(self) -> "PrimeField":
        return type(self)(prime_field_inv(self.n, self.field_modulus))
    
    def repr(self) -> str:
        k = self.field_modulus // 2
        if self.n < k:
            return f"{self.n}"
        else:
            return f"-{self.field_modulus - self.n}"
        
    def exp(self: "PrimeField", other: int) -> "PrimeField":
        return type(self)(pow(self.n, other, self.field_modulus))
    
    @classmethod
    def compute_root_of_unity(cls) -> "PrimeField":
        return cls(pow(cls.MULTIPLICATIVE_GENERATOR, ((cls.field_modulus - 1) // 2 ** cls.TWO_ADICITY), cls.field_modulus))
    
    @classmethod
    def root_of_unity(cls) -> "PrimeField":
        return cls(cls.ROOT_OF_UNITY)
    
    @classmethod
    def multiplicative_generator(cls) -> "PrimeField":
        return cls(cls.MULTIPLICATIVE_GENERATOR)

    @classmethod
    def nth_root_of_unity(cls, n: int) -> "PrimeField":
        assert is_power_of_two(n), "n must be a power of two"
        return cls(pow(cls.ROOT_OF_UNITY, 2**(cls.TWO_ADICITY - log_2(n)), cls.field_modulus))
    

class F193(PrimeField):
    field_modulus = 193
    ROOT_OF_UNITY = 125
    MULTIPLICATIVE_GENERATOR = 5
    TWO_ADICITY = 6
