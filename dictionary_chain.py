"""
A drop-in replacement for the Python dictionary class written in pure Python.
This is for educational purposes only, for illustrating how dictionaries work.
The original version was based heavily on Benjamin Peterson's code here:
http://pybites.blogspot.com/2008/10/pure-python-dictionary-implementation.html

This file implements chaining and requires the package coinor.blimpy to be
installed (this provides a drop-in replacement for the Python list class
based on linked lists).

There is a method for visualizing the dictionary that requires pygame.

Copyright 2014 Aykut Bulut, Ted Ralphs, and Lehigh University
"""
from __future__ import division
from __future__ import print_function
from builtins import hex
from builtins import range
from past.utils import old_div
from builtins import object
__author__  = "Aykut Bulut and Ted Ralphs"
__url__     = "https://github.com/tkralphs/PyDict"
__license__ = 'CC BY 3.0'

try:
    import pygame
    from pygame.locals import *
except ImportError:
    PYGAME_INSTALLED = False
else:
    PYGAME_INSTALLED = True

import random, string
from math import sqrt
import time
from coinor.blimpy import LinkedList

dummy = "<dummy key>"

times = {}

def print_timing(func):
    def wrapper(*arg, **kargs):
        t1 = time.clock()
        res = func(*arg, **kargs)
        t2 = time.clock()
        times[func.__name__] = t2-t1
        print('%s took %0.3fms' % (func.__name__, (t2-t1)*1000.0))
        return res
    wrapper.func = func
    return wrapper

counts = {}

def counter(func):
    counts[func.__name__] = 0
    def wrapper(*arg, **kargs):
        counts[func.__name__] += 1
        res = func(*arg, **kargs)
        return res
    return wrapper

@counter
def compare(i, j):
    return i == j

def c_mul(a, b):
    return eval(hex((int(a) * b) & 0xFFFFFFFF)[:-1])

class Entry(object):
    """
    A hash table entry.

    Attributes:
       * key - The key for this entry.
       * hash - The has of the key.
       * value - The value associated with the key.
    """

    def __init__(self):
        self.key = None
        self.value = None
        self.hash = 0

    def __repr__(self):
        return "<Entry: key={0} value={1}>".format(self.key, self.value)

class Dict(object):
    """
    A mapping interface implemented as a hash table.

    Attributes:
        * used - The number of entires used in the table.
        * filled - used + number of entries with a dummy key.
        * table - List of entries; contains the actual dict data.
        * size - Length of table. Used to fetch values.
    """

    def __init__(self, size):
        self.size = size
        self.clear()

    def hash(self, s):
        h, a, b = 0, 31415, 27183
        if s is None:
            pass
        for c in s:
            h = (a*h + ord(c)) % self.size
            a = a+b % (self.size - 1)
        if h < 0:
            return h + self.size
        else:
            return h

    @classmethod
    def fromkeys(cls, keys, value=0):
        """
        Return a new dictionary from a sequence of keys.
        """
        d = cls()
        for key in keys:
            d[key] = value
        return d

    def clear(self):
        """
        Clear the dictionary of all data.
        """
        self.filled = 0
        self.used = 0
        self.table = [LinkedList() for i in range(self.size)]

    def pop(self, *args):
        """
        Remove and return the value for a key.
        """
        have_default = len(args) == 2
        try:
            v = self[args[0]]
        except KeyError:
            if have_default:
                return args[1]
            raise
        else:
            del self[args[0]]
            return v

    def popitem(self):
        """
        Remove and return any key-value pair from the dictionary.
        """
        if self.used == 0:
            raise KeyError("empty dictionary")
        entry0 = self.table[0][0]
        entry = entry0
        if entry0.value is None:
            i = entry0.hash
            if i >= self.size or i < i:
                i = 1
            entry = self.table[i][0]
            while entry.value is None:
                i += 1
                if i >= self.size:
                    i = 1
                entry = self.table[i][0]
        res = entry.key, entry.value
        self._del(entry)
        entry0.hash = i + 1
        return res

    def setdefault(self, key, default=0):
        """
        If key is in the dictionary, return it. Otherwise, set it to the default
        value.
        """
        val = self._lookup(key).value
        if val is None:
            self[key] = default
            return default
        return val

    def _lookup(self, key):
        """
        Find the entry for a key.
        """
        key_hash = self.hash(key)
        i = key_hash
        LL = self.table[i]
        k = 0
        while k<len(LL):
            if compare(LL[k].key, key):
                return LL[k]
            k+=1
        k = 0
        while k<len(LL):
            if LL[k].key == None:
                return LL[k]
            k+=1
        LL.append(Entry())
        return LL[k]

    def _insert(self, key, value):
        """
        Add a new value to the dictionary or replace an old one.
        """
        entry = self._lookup(key)
        if entry.value is None:
            self.used += 1
            if entry.key is not dummy:
                self.filled += 1
        entry.key = key
        entry.hash = self.hash(key)
        entry.value = value

    def _del(self, entry):
        """
        Mark an entry as free with the dummy key.
        """
        entry.key = dummy
        entry.value = None
        self.used -= 1

    def __getitem__(self, key):
        value = self._lookup(key).value
        if value is None:
            # Check if we're a subclass.
            if type(self) is not Dict:
                # Try to call the __missing__ method.
                missing = getattr(self, "__missing__")
                if missing is not None:
                    return missing(key)
            raise KeyError("no such key: {0!r}".format(key))
        return value

    def __setitem__(self, key, what):
        # None is used as a marker for empty entries, so it can't be in a
        # dictionary.
        assert what is not None and key is not None, \
            "key and value must not be None"
        self._insert(key, what)

    def __delitem__(self, key):
        entry = self._lookup(key)
        if entry.value is None:
            raise KeyError("no such key: {0!r}".format(key))
        self._del(entry)

    def __contains__(self, key):
        """
        Check if a key is in the dictionary.
        """
        key_hash = self.hash(key)
        i = key_hash
        LL = self.table[i]
        k = 0
        while k<len(LL):
            if compare(LL[k].key, key):
                return True
            k+=1
        return False

    def __eq__(self, other):
        if not isinstance(other, Dict):
            try:
                # Try to coerce the other to a Dict, so we can compare it.
                other = Dict(other)
            except TypeError:
                return NotImplemented
        if self.used != other.used:
            # They're not the same size.
            return False
        # Look through the table and compare every entry, breaking out early if
        # we find a difference.
        for entry in self.table:
            if entry.value is not None:
                try:
                    bval = other[entry.key]
                except KeyError:
                    return False
                if not bval == entry.value:
                    return False
        return True

    def __ne__(self, other):
        return not self == other

    def keys(self):
        """
        Return a list of keys in the dictionary.
        """
        return [entry for entry in self]

    def values(self):
        """
        Return a list of values in the dictionary.
        """
        return [self[entry] for entry in self]

    def items(self):
        """
        Return a list of key-value pairs.
        """
        return [(entry, self[entry]) for entry in self]

    def __iter__(self):
        return DictKeysIterator(self)

    def itervalues(self):
        """
        Return an iterator over the values in the dictionary.
        """
        return DictValuesIterator(self)

    def iterkeys(self):
        """
        Return an iterator over the keys in the dictionary.
        """
        return DictKeysIterator(self)

    def iteritems(self):
        """
        Return an iterator over key-value pairs.
        """
        return DictItemsIterator(self)

    def _from_sequence(self, seq):
        for double in seq:
            if len(double) != 2:
                raise ValueError("{0!r} doesn't have a length of 2".format(
                        double))
            self[double[0]] = double[1]

    def get(self, key, default=0):
        """
        Return the value for key if it exists otherwise the default.
        """
        try:
            return self[key]
        except KeyError:
            return default

    def __len__(self):
        return self.used

    def __repr__(self):
        r = ["{0!r} : {1!r}".format(k, v) for k, v in self.items()]
        return "Dict({" + ", ".join(r) + "})"

    def draw_init(self, dimension):

        # Initialize the pygame modules
        pygame.init()

        # Set the dimensions
        self.screen = pygame.display.set_mode((dimension,
                                               dimension))

        # Grab the background surface of the screen
        self.bg = self.screen.convert()

        # Grab the game clock
        self.clock = pygame.time.Clock()

    def draw_dictionary(self):

        if not PYGAME_INSTALLED:
            print("Please install Pygame for visualization...exiting")
            return

        cell_dimension = 10
        num_squares = int(sqrt(self.size)) + 1
        board_dimension = cell_dimension*num_squares
        self.draw_init(board_dimension)

        # Draw every cell in the board as a rectangle on the screen
        i = j = 0
        for cell in self.table:
            shade = min(50*len(cell), 255)
            print(len(cell), end=' ')
            rectangle = (j*cell_dimension, i*cell_dimension,
                         cell_dimension, cell_dimension)
            pygame.draw.rect(self.bg, (shade, shade, shade), rectangle)
            if j == num_squares:
                j = 0
                i += 1
                print()
            else:
                j += 1

        while i < num_squares:
            rectangle = (j*cell_dimension, i*cell_dimension,
                         cell_dimension, cell_dimension)
            pygame.draw.rect(self.bg, (255, 255, 255), rectangle)
            if j == num_squares:
                j = 0
                i += 1
            else:
                j += 1


        # Blit bg to the screen, flip display buffers
        self.screen.blit(self.bg, (0,0))
        pygame.display.flip()

        # Queue user input to catch QUIT signals
        quit = False
        while quit != True:
            for e in pygame.event.get():
                if e.type == QUIT:
                    quit = True

class DictIterator(object):

    def __init__(self, d):
        self.d = d
        self.used = self.d.used
        self.len = self.d.used
        self.pos1 = 0
        self.pos2 = 0

    def __iter__(self):
        return self

    def __next__(self):
        # Check if the dictionary has been mutated under us.
        if self.used != self.d.used:
            # Make this state permanent.
            self.used = -1
            raise RuntimeError("dictionary size changed during iteration")
        i = self.pos1
        k = self.pos2
        while i < self.d.size:
            if len(self.d.table[i]) > 0:
                if k < len(self.d.table[i]):
                    self.pos2 = k+1
                    self.pos1 = i
                    if self.d.table[i][k].key == None or\
                       self.d.table[i][k].key == dummy:
                        k += 1
                        continue
                    return self._extract(self.d.table[i][k])
                else:
                    k = 0
                    self.pos2 = 0
                    i += 1
            else:
                k = 0
                self.pos2 = 0
                i+=1
        self.pos1 = i+1
        if i >= self.d.size:
            # We're done.
            raise StopIteration
        self.len = self.len-1

    next = __next__

    def _extract(self, entry):
        return getattr(entry, self.kind)

    def __len__(self):
        return self.len

class DictKeysIterator(DictIterator):
    kind = "key"

class DictValuesIterator(DictIterator):
    kind = "value"

class DictItemsIterator(DictIterator):

    def _extract(self, entry):
        return entry.key, entry.value

@print_timing
def testing(dict_size = 2000, num_items = 1000):
    random.seed(3)
    cd = Dict(dict_size)
    i = 0
    while i < num_items:
        s = ''.join(random.choice(string.ascii_letters) for k in range(10))
        cd[s] = random.randint(3,9)
        i += 1
    ll1 = list(cd.keys())
    counts['compare'] = 0
    for i in range(len(ll1)):
        ll1[i] in cd
    print('Average number of comparisons: ', old_div((1.0*counts['compare']),len(ll1)))
    print('Load factor: ', old_div((1.0*len(ll1)),dict_size))

if __name__ == '__main__':

    mytimes = {}
    for dict_size in range(100, 1000, 100):
        times['testing'] = 0
        testing(dict_size = dict_size)
        mytimes[dict_size] = times['testing']
