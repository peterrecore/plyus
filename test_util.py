import unittest
import json
import random
import logging
from util import *

class TestAllTheThings(unittest.TestCase):

    def test_reverse_map(self):
        m = {1:"a", 2:"b", 3:"c"}
        r = reverse_map(m)
        self.assertEqual(r["a"], 1)
        self.assertEqual(r["b"], 2)
        self.assertEqual(r["c"], 3)
        self.assertEqual(len(r), len(m))

    def test_lowest_higher_than(self):
        a = [3, 9, 7, 2] 
        self.assertEqual(lowest_higher_than(a, 3), 7)
        self.assertEqual(lowest_higher_than(a, 1), 2)
        self.assertIs(lowest_higher_than(a, 9), None)

    def test_json(self):
        x = json.loads("[1,2,3]")
        self.assertTrue(len(x) == 3)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()