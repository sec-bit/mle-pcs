import unittest
from hashlib import sha256
import sys

sys.path.append("../src")
sys.path.append("src")
from merkle import MerkleTree, verify_decommitment

class TestMerkleTree(unittest.TestCase):

    def test_init_with_valid_data(self):
        data = [1, 2, 3, 4]
        tree = MerkleTree(data)
        self.assertEqual(len(tree.data), 4)
        self.assertEqual(tree.height, 2)

    def test_init_with_non_power_of_two_data(self):
        data = [1, 2, 3]
        tree = MerkleTree(data)
        self.assertEqual(len(tree.data), 4)
        self.assertEqual(tree.height, 2)
        self.assertEqual(tree.data[-1], 0)  # Check padding

    def test_init_with_empty_list(self):
        with self.assertRaises(AssertionError):
            MerkleTree([])

    def test_get_authentication_path(self):
        data = [1, 2, 3, 4]
        tree = MerkleTree(data)
        path = tree.get_authentication_path(0)
        self.assertEqual(len(path), 2)

    def test_get_authentication_path_out_of_range(self):
        data = [1, 2, 3, 4]
        tree = MerkleTree(data)
        with self.assertRaises(AssertionError):
            tree.get_authentication_path(4)

    def test_verify_decommitment(self):
        data = [1, 2, 3, 4]
        tree = MerkleTree(data)
        leaf_id = 2
        leaf_data = data[leaf_id]
        path = tree.get_authentication_path(leaf_id)
        self.assertTrue(verify_decommitment(leaf_id, leaf_data, path, tree.root))

    def test_verify_decommitment_with_wrong_leaf_data(self):
        data = [1, 2, 3, 4]
        tree = MerkleTree(data)
        leaf_id = 2
        wrong_leaf_data = 5
        path = tree.get_authentication_path(leaf_id)
        self.assertFalse(verify_decommitment(leaf_id, wrong_leaf_data, path, tree.root))

    def test_verify_decommitment_with_wrong_path(self):
        data = [1, 2, 3, 4]
        tree = MerkleTree(data)
        leaf_id = 2
        leaf_data = data[leaf_id]
        path = tree.get_authentication_path(leaf_id)
        wrong_path = [sha256(b'wrong').hexdigest() for _ in path]
        self.assertFalse(verify_decommitment(leaf_id, leaf_data, wrong_path, tree.root))

    def test_large_tree(self):
        data = list(range(1024))
        tree = MerkleTree(data)
        self.assertEqual(tree.height, 10)
        for i in range(1024):
            path = tree.get_authentication_path(i)
            self.assertTrue(verify_decommitment(i, data[i], path, tree.root))

if __name__ == '__main__':
    unittest.main()
