import unittest
import json
import random
import logging
from util import *

class Foo(object):
    def __init__(self,prop1, prop2):
        self.prop1 = prop1
        self.prop2 = prop2
        pass
    def __eq__(self, other):
        if (self.prop1 != other.prop1 or
            self.prop2 != other.prop2 or
            self.__class__ != other.__class__ or 
            self.__module__ != other.__module__):
            return False
        return True

class TestAllTheThings(unittest.TestCase):


    def test_draw_too_many(self):
        with self.assertRaises(ValueError):
            xs = [1,2,3]
            a = draw_n(xs, 4)

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

    def test_object_to_json(self):
        f = Foo(u"peter", u"purple")
        s = to_json(f)
        self.assertEqual(s, '{"__class__": "Foo", "__module__": "__main__", "prop1": "peter", "prop2": "purple"}') 
        f2 = from_json(s)
        print f.__dict__ , f.__module__, f.__class__
        print f2.__dict__, f2.__module__, f2.__class__
        self.assertEquals(f,f2)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()