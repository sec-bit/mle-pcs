from unittest import TestCase, main
import sys

sys.path.append("src")
sys.path.append("../src")

from utils import bits_le_with_width, pow_2, is_power_of_two, next_power_of_two, log_2

class TestUtils(TestCase):

    def test_bits_le_with_width(self):
        self.assertEqual(bits_le_with_width(5, 4), [1, 0, 1, 0])
        self.assertEqual(bits_le_with_width(0, 3), [0, 0, 0])
        self.assertEqual(bits_le_with_width(7, 3), [1, 1, 1])
        self.assertEqual(bits_le_with_width(8, 3), "Failed")
        self.assertEqual(bits_le_with_width(15, 4), [1, 1, 1, 1])

    def test_pow_2(self):
        self.assertEqual(pow_2(0), 1)
        self.assertEqual(pow_2(1), 2)
        self.assertEqual(pow_2(3), 8)
        self.assertEqual(pow_2(10), 1024)

    def test_is_power_of_two(self):
        self.assertEqual(is_power_of_two(1), True)
        self.assertEqual(is_power_of_two(2), True)
        self.assertEqual(is_power_of_two(4), True)
        self.assertEqual(is_power_of_two(8), True)
        self.assertEqual(is_power_of_two(16), True)
        self.assertEqual(is_power_of_two(3), False)
        self.assertEqual(is_power_of_two(6), False)
        self.assertEqual(is_power_of_two(10), False)

    def test_next_power_of_two(self):
        self.assertEqual(next_power_of_two(0), 1)
        self.assertEqual(next_power_of_two(1), 1)
        self.assertEqual(next_power_of_two(2), 2)
        self.assertEqual(next_power_of_two(3), 4)
        self.assertEqual(next_power_of_two(5), 8)
        self.assertEqual(next_power_of_two(7), 8)
        self.assertEqual(next_power_of_two(9), 16)
        self.assertEqual(next_power_of_two(1023), 1024)
        
        with self.assertRaises(AssertionError):
            next_power_of_two(-1)

    def test_log_2(self):
        self.assertEqual(log_2(1), 0)
        self.assertEqual(log_2(2), 1)
        self.assertEqual(log_2(3), 1)
        self.assertEqual(log_2(4), 2)
        self.assertEqual(log_2(7), 2)
        self.assertEqual(log_2(8), 3)
        self.assertEqual(log_2(1024), 10)

        with self.assertRaises(ValueError):
            log_2(0)
        
        with self.assertRaises(ValueError):
            log_2(-1)
        
        with self.assertRaises(ValueError):
            log_2(1.5)


if __name__ == "__main__":
    main()

