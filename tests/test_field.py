import unittest
import sys

sys.path.append("../src")
sys.path.append("src")

from field import Field, magic

class TestField(unittest.TestCase):
    def setUp(self):
        self.f1 = Field([1, 2, 3])
        self.f2 = Field([4, 5, 6])

    def test_initialization(self):
        self.assertEqual(Field(5).value, [5])
        self.assertEqual(self.f1.value, [1, 2, 3])

    def test_addition(self):
        result = self.f1 + self.f2
        self.assertEqual(result.value, [5, 7, 9])

    def test_subtraction(self):
        result = self.f2 - self.f1
        self.assertEqual(result.value, [3, 3, 3])

    def test_multiplication(self):
        result = self.f1 * self.f2
        self.assertEqual(result.value, [4, 10, 18])

    def test_division(self):
        f3 = Field([2, 4, 6])
        result = f3 / self.f1
        self.assertEqual(result.value, [2, 2, 2])

    def test_power(self):
        result = self.f1 ** 2
        self.assertEqual(result.value, [1, 4, 9])
        
        result = self.f1 ** Field([2, 3, 2])
        self.assertEqual(result.value, [1, 8, 9])

    def test_inverse(self):
        f4 = Field([2, 4, 5])
        result = f4.inverse()
        self.assertNotEqual(result, [1, 1, 1])
        result = result * f4
        self.assertEqual(result.value, [1, 1, 1])

    def test_equality(self):
        self.assertEqual(self.f1, Field([1, 2, 3]))
        self.assertEqual(Field(5), 5)
        self.assertNotEqual(self.f1, self.f2)

    def test_negation(self):
        result = -self.f1
        self.assertNotEqual(result.value, [0, 0, 0])
        result = result + self.f1
        self.assertEqual(result.value, [0, 0, 0])

    def test_modulo(self):
        f5 = Field([10, 15, 20])
        result = f5 % 3
        self.assertEqual(result.value, [1, 0, 2])

    def test_operation_counts(self):
        Field.reset_operation_count()
        _ = self.f1 + self.f2
        _ = self.f1 * self.f2
        self.assertEqual(Field.get_operation_count('add'), 1)
        self.assertEqual(Field.get_operation_count('mul'), 1)

    def test_random_element(self):
        random_field = Field.random_element()
        self.assertIsInstance(random_field, Field)
        self.assertTrue(0 <= random_field.value[0] <= 193)

    def test_magic_field(self):
        from sage.all import GF

        MagicField = magic(GF(193))
        self.assertEqual(MagicField.zero(), 0)
        self.assertEqual(MagicField.one(), 1)
        self.assertEqual(MagicField.primitive_element(), 5)
        self.assertEqual(MagicField(192) + MagicField(1), 0)

if __name__ == '__main__':
    unittest.main()
