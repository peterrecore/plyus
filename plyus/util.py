import logging
import json
import itertools
import errors


def draw_n(some_list, n):
    if len(some_list) < n:
        raise ValueError("trying to draw %s elements from a list of len %s" % (n, len(some_list)))

    r = some_list[0:n]
    logging.debug("draw_n: items are %s " % r)
    del some_list[0:n]
    return r


def reverse_map(m):
    reversed = {}
    for (k, v) in m.items():
        reversed[v] = k
    return reversed


def lowest_higher_than(lst, x):
    """Given a list, find the lowest int that is higher than n"""
    for a in lst:
        if not isinstance(a, int):
            raise errors.FatalPlyusError("element wsa not an int")

    for n in sorted(lst):
        if n > x:
            return n
    return None


def flatten(list_of_lists):
    flat_list = list(itertools.chain.from_iterable(list_of_lists))
    return flat_list


def ids(xs):
    return [x.id for x in xs]


def convert_to_builtin_type(obj):
    # Convert objects to a dictionary of their representation
    # based on code from http://pymotw.com
    d = {'__class__': obj.__class__.__name__,
         '__module__': obj.__module__,
    }
    d.update(obj.__dict__)
    return d

#this method has a major caveat - the __init__ method of the class being built
# must have arguments named the same as the instance variables
def dict_to_object(d):
    if '__class__' in d:
        class_name = d.pop('__class__')

        module_name = d.pop('__module__')
        logging.debug("class is %s and module is %s" % (class_name, module_name))
        module = __import__(module_name)
        logging.debug("module is %s" % module)
        class_ = getattr(module, class_name)
        args = dict((key.encode('ascii'), value) for key, value in d.items())
        inst = class_(**args)
    else:
        inst = d
    return inst


def to_json(x):
    j = json.dumps(x, default=convert_to_builtin_type, sort_keys=True)#,indent=2)
    #logging.debug("json output is %s" % j)
    return j


def from_json(s):
    d = json.loads(s)
    logging.debug("json loading type %s" % type(d))
    return d
