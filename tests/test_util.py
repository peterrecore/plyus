import unittest
import json
import random
import logging
import util

class Foo(object):
    def __init__(self,prop1, prop2,prop3):
        self.prop1 = prop1
        self.prop2 = prop2
        self.prop3 = prop3
        pass
    def __eq__(self, other):
        if (self.prop1 != other.prop1 or
            self.prop2 != other.prop2 or
            self.prop3 != other.prop3 or
            self.__class__ != other.__class__ or 
            self.__module__ != other.__module__):
            return False
        return True

class TestAllTheThings(unittest.TestCase):


    def test_draw_too_many(self):
        with self.assertRaises(ValueError):
            xs = [1,2,3]
            a = util.draw_n(xs, 4)

    def test_reverse_map(self):
        m = {1:"a", 2:"b", 3:"c"}
        r = util.reverse_map(m)
        self.assertEqual(r["a"], 1)
        self.assertEqual(r["b"], 2)
        self.assertEqual(r["c"], 3)
        self.assertEqual(len(r), len(m))

    def test_lowest_higher_than(self):
        a = [3, 9, 7, 2] 
        self.assertEqual(util.lowest_higher_than(a, 3), 7)
        self.assertEqual(util.lowest_higher_than(a, 1), 2)
        self.assertIs(util.lowest_higher_than(a, 9), None)

    def test_json(self):
        x = json.loads("[1,2,3]")
        self.assertTrue(len(x) == 3)

    def test_object_to_json(self):
        f = Foo(u"peter", u"purple",23)
        s = unicode(util.to_json(f))
        logging.debug("s ==> %s" % s)
        logging.debug("f ==> %s" % s)
        f_as_string = unicode('{"__class__": "Foo", "__module__": "test_util", "prop1": "peter", "prop2": "purple", "prop3": 23}')
        self.assertEqual(s,f_as_string) 
        f2 = util.from_json(s)
        print f.__dict__ , f.__module__, f.__class__
        print f2.__dict__, f2.__module__, f2.__class__
        self.assertEquals(f,f2)

    def test_flatten(self):
        xss = [[1], [2,3],[], [4,5,6]]
        xs = util.flatten(xss)
        self.assertEquals(xs,[1,2,3,4,5,6])

        yss = [[1],[2,3], [1]]
        ys = util.flatten(yss)
        self.assertEquals(ys,[1,2,3,1])

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()