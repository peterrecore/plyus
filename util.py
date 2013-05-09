import logging
import json

def draw_n(some_list, n):
    #TODO: check to make sure there are enough elements to return
    r = some_list[0:n]
    logging.info("draw_n: items are %s " % r)
    del some_list[0:n]
    return r

def reverse_map(m):
	reversed = {}
	for (k,v) in m.items():
		reversed[v] = k
	return reversed
    # given a mapping from player # to 

def lowest_higher_than(list, x):
   	"""Given a list, find the lowest element that is higher than n"""
   	for n in sorted(list):
   		if n > x: 
   			return n
   	return None

def ids(xs):
	return [x.id for x in xs]

def convert_to_builtin_type(obj):
    # Convert objects to a dictionary of their representation
    # based on code from http://pymotw.com
    d = { '__class__':obj.__class__.__name__, 
          '__module__':obj.__module__,
          }
    d.update(obj.__dict__)
    return d
