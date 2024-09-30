import unittest
from unittest.mock import Mock
import sys

sys.path.append('../src')
sys.path.append('src')

from group import DummyGroup

class TestDummyGroup(unittest.TestCase):
    def setUp(self):
        self.mock_field = Mock()
        self.mock_field.zero.return_value = 0
        self.mock_field.primitive_element.return_value = 1
        self.mock_field.order.return_value = 100
        self.group = DummyGroup(self.mock_field)

    def test_init(self):
        self.assertEqual(self.group.field, self.mock_field)

    def test_identity(self):
        self.assertEqual(self.group.identity(), 0)

    def test_generator(self):
        self.assertEqual(self.group.generator(), 1)

    def test_exp(self):
        self.assertEqual(self.group.exp(2, 3), 6)

    def test_scalar_mul_single(self):
        self.assertEqual(self.group.scalar_mul(2, 3), 6)

    def test_scalar_mul_list(self):
        self.assertEqual(self.group.scalar_mul([1, 2, 3], 2), [2, 4, 6])

    def test_add(self):
        self.assertEqual(self.group.add(2, 3), 5)

    def test_sub(self):
        self.assertEqual(self.group.sub(5, 3), 2)

    def test_order(self):
        self.assertEqual(self.group.order(), 100)

    def test_pairing(self):
        self.assertEqual(DummyGroup.pairing(2, 3), 6)

if __name__ == '__main__':
    unittest.main()
