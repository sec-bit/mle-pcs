import random

from unipolynomial import UniPolynomial

class Field:
    operation_counts = {
        'add': 0,
        'sub': 0,
        'mul': 0,
        'div': 0
    }

    def __init__(self, value):
        self.value = value if isinstance(value, list) else [value]

    @classmethod
    def _increment_count(cls, operation):
        cls.operation_counts[operation] += 1

    @classmethod
    def get_operation_count(cls, operation=None):
        if operation:
            return cls.operation_counts[operation]
        return cls.operation_counts

    @classmethod
    def reset_operation_count(cls, operation=None):
        if operation:
            cls.operation_counts[operation] = 0
        else:
            for op in cls.operation_counts:
                cls.operation_counts[op] = 0

    def _operate(self, other, operation, op_name):
        self._increment_count(op_name)
        if isinstance(other, Field):
            return Field([operation(a, b) for a, b in zip(self.value, other.value)])
        elif isinstance(other, list):
            return Field([operation(a, b) for a, b in zip(self.value, other)])
        else:
            return Field([operation(a, other) for a in self.value])

    def __add__(self, other):
        def safe_add(a, b):
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                return a + b
            elif hasattr(a, '__add__') and not isinstance(b, UniPolynomial):
                return a + b
            elif hasattr(b, '__add__') and not isinstance(a, UniPolynomial):
                return b + a
            else:
                raise TypeError(f"Unsupported operand types for +: '{type(a).__name__}' and '{type(b).__name__}'")
        
        return self._operate(other, safe_add, 'add')

    def __radd__(self, other):
        return self._operate(other, lambda a, b: a + b, 'add')

    def __sub__(self, other):
        return self._operate(other, lambda a, b: a - b, 'sub')

    def __rsub__(self, other):
        return self._operate(other, lambda a, b: b - a, 'sub')

    def __mul__(self, other):
        return self._operate(other, lambda a, b: a * b, 'mul')

    def __rmul__(self, other):
        return self._operate(other, lambda a, b: b * a, 'mul')

    def __truediv__(self, other):
        return self._operate(other, lambda a, b: a / b, 'div')

    def __rtruediv__(self, other):
        return self._operate(other, lambda a, b: b / a, 'div')

    def __pow__(self, exponent):
        self._increment_count('mul')  # Consider power as a series of multiplications
        if isinstance(exponent, int):
            if exponent >= 0:
                return Field([pow(a, exponent) for a in self.value])
            else:
                return Field([pow(a, -exponent) for a in self.value]).inverse()
        elif isinstance(exponent, Field):
            if len(exponent.value) != len(self.value):
                raise ValueError("Exponent Field must have the same length as the base Field")
            return Field([pow(a, b) for a, b in zip(self.value, exponent.value)])
        else:
            raise TypeError(f"Unsupported exponent type: {type(exponent)}")

    def inverse(self):
        return Field([1 / a for a in self.value])

    def __str__(self):
        return f"Field({self.value})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, Field):
            return self.value == other.value
        elif isinstance(other, list):
            return self.value == other
        else:
            return len(self.value) == 1 and self.value[0] == other
        
    def zero():
        return 0

    @classmethod
    def random_element(cls):
        return cls(random.randint(0, 193))

def magic(Fp):
    def magic_field(value):
        return Field(Fp(value))
    magic_field.Fp = Fp
    magic_field.zero = lambda : Fp.zero()
    magic_field.one = lambda : Fp.one()
    magic_field.primitive_element = lambda : Fp.primitive_element()
    return magic_field
