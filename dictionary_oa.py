"""
A drop-in replacement for the Python dictionary class written in pure Python.
This is for educational purposes only, for illustrating how dictionaries work.
The original version was based heavily on Benjamin Peterson's code here:
http://pybites.blogspot.com/2008/10/pure-python-dictionary-implementation.html

This file implements open addressing with double hashing (currently, the second 
hash function is a constant, which means it behaves like linear probing).
Replace the method hash2 below for better performance.

There is a method for visualizing the dictionary that requires pygame.
"""
__author__ = "Aykut Bulut and Ted Ralphs"
__url__    = "https://github.com/tkralphs/PyDict"

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

dummy = "<dummy key>"

times = {}

def print_timing(func):
    def wrapper(*arg, **kargs):
        t1 = time.clock()
        res = func(*arg, **kargs)
        t2 = time.clock()
        times[func.func_name] = t2-t1
        print '%s took %0.3fms' % (func.func_name, (t2-t1)*1000.0)
        return res
    wrapper.func = func
    return wrapper

counts = {}

def counter(func):
    counts[func.func_name] = 0
    def wrapper(*arg, **kargs):
        counts[func.func_name] += 1
        res = func(*arg, **kargs)
        return res
    return wrapper

@counter
def compare(i, j):
    return i == j

dummy = "<dummy key>"

def c_mul(a, b):
    return eval(hex((long(a) * b) & 0xFFFFFFFFL)[:-1])

class Entry(object):
    """
    A hash table entry.

    Attributes:
       * key - The key for this entry.
       * hash - The has of the key.
       * value - The value associated with the key.
    """

    __slots__ = ("key", "value", "hash")

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
        * size - Length of table, Used to fetch values.
    """

    def __init__(self, size = 111):
        self.size = size
        self.clear()
        self.colors = {0:(0,0,0), 
                       1:(200,200,100), 
                       2:(255, 255, 255)}

    def hash1(self, s, mask):
        h, a, b = 0, 31415, 27183
        if isinstance(s, int):
            return s % mask
        for c in s:
            h = (a*h + ord(c)) % mask
            a = a+b % mask - 1
        if h < 0:
            return h + mask
        else:
            return h

    def hash2(self, s, mask):
        # Caution: cannot return zero, but we're not checking 
        # that
        return 1

    def first_hash(self, s):
        return self.hash1(s, self.size)

    def second_hash(self, s):
        return self.hash2(s, self.size - 1) + 1

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
        self.table = []
        # Initialize the table to a clean slate of entries.
        for i in range(self.size):
            self.table.append(Entry())

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
        entry0 = self.table[0]
        entry = entry0
        i = 0
        if entry0.value is None:
            # The first entry in the table's hash is abused to hold the index to
            # the next place to look for a value to pop.
            i = entry0.hash
            if i >= self.size or i < i:
                i = 1
            entry = self.table[i]
            while entry.value is None:
                i += 1
                if i >= self.size:
                    i = 1
                entry = self.table[i]
        res = entry.key, entry.value
        self._del(entry)
        # Set the next place to start.
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
        key_hash = self.first_hash(key)
        entry = self.table[key_hash]
        if entry.key is None or entry is key:
            return entry
        free = None
        if entry.key is dummy:
            free = entry
        elif compare(entry.hash, key_hash) and key == entry.key:
            return entry

        i = key_hash
        while True:
            i += self.second_hash(key)
            i = i % self.size
            entry = self.table[i]
            if entry.key is None:
                return entry if free is None else free
            if entry.key is key or \
                    (compare(entry.hash, key_hash) and key == entry.key):
                return entry
            elif entry.key is dummy and free is None:
                free = dummy

        assert False, "not reached"

    def _resize(self, minused):
        """
        Resize the dictionary to at least minused.
        """
        newsize = self.size
        # Find the smalled value for newsize.
        while newsize <= minused and newsize > 0:
            newsize <<= 1
            newsize += 1
        oldtable = self.table
        # Create a new table newsize long.
        newtable = []
        while len(newtable) < newsize:
            newtable.append(Entry())
        # Replace the old table.
        self.table = newtable
        self.used = 0
        self.filled = 0
        # Copy the old data into the new table.
        for entry in oldtable:
            if entry.value is not None:
                self._insert_into_clean(entry)
            elif entry.key is dummy:
                entry.key = None
        self.size = newsize

    def _insert_into_clean(self, entry):
        """
        Insert an item in a clean dict. This is a helper for resizing.
        """
        i = entry.hash
        new_entry = self.table[i]
        while new_entry.key is not None:
            i += self.second_hash(new_entry.key)
            new_entry = self.table[i]
        new_entry.key = entry.key
        new_entry.value = entry.value
        new_entry.hash = entry.hash
        self.used += 1
        self.filled += 1

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
        entry.hash = self.first_hash(key)
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
        old_used = self.used
        self._insert(key, what)
        
        #For the purpose of experimentation, disable resizing
        return
        
        # Maybe resize the dict.
        if not (self.used > old_used and
                self.filled*3 >= self.size*2):
            return
        # Large dictionaries (< 5000) are only doubled in size.
        factor = 2 if self.used > 5000 else 4
        self._resize(factor*self.used)

    def __delitem__(self, key):
        entry = self._lookup(key)
        if entry.value is None:
            raise KeyError("no such key: {0!r}".format(key))
        self._del(entry)

    def __contains__(self, key):
        """
        Check if a key is in the dictionary.
        """
        return self._lookup(key).value is not None

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
        return [entry.key for entry in self.table if entry.value is not None]

    def values(self):
        """
        Return a list of values in the dictionary.
        """
        return [entry.value for entry in self.table if entry.value is not None]

    def items(self):
        """
        Return a list of key-value pairs.
        """
        return [(entry.key, entry.value) for entry in self.table
                if entry.value is not None]

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
        r = ["{0!r} : {1!r}".format(k, v) for k, v in self.iteritems()]
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
            print "Please install Pygame for visualization...exiting"
            return
        cell_dimension = 10
        num_squares = int(sqrt(self.size)) + 1
        board_dimension = cell_dimension*num_squares
        self.draw_init(board_dimension)

        # Draw every cell in the board as a rectangle on the screen
        i = j = 0
        for item in self.table:
            filled = item.key is not None and item.key is not dummy
            if filled:
                print item.hash,
            else:
                print '*',
            rectangle = (j*cell_dimension, i*cell_dimension,
                         cell_dimension, cell_dimension)
            pygame.draw.rect(self.bg, self.colors[filled], rectangle)
            if j == num_squares:
                j = 0
                i += 1
                print
            else:
                j += 1
                
        while i < num_squares:
            rectangle = (j*cell_dimension, i*cell_dimension,
                         cell_dimension, cell_dimension)
            pygame.draw.rect(self.bg, self.colors[2], rectangle)
            if j == num_squares:
                j = 0
                i += 1
            else:
                j += 1
            

        # Blit bg to the screen, flip display buffers
        self.screen.blit(self.bg, (0,0))
        pygame.display.flip()

        # Queue user input to catch QUIT signals
        quit_window = False
        while quit_window != True:
            for e in pygame.event.get():
                if e.type == QUIT: 
                    quit_window = True

class DictIterator(object):

    def __init__(self, d):
        self.d = d
        self.used = self.d.used
        self.len = self.d.used
        self.pos = 0

    def __iter__(self):
        return self

    def next(self):
        # Check if the dictionary has been mutated under us.
        if self.used != self.d.used:
            # Make this state permanent.
            self.used = -1
            raise RuntimeError("dictionary size changed during ineration")
        i = self.pos
        while i < self.d.size and self.d.table[i].value is None:
            i += 1
        self.pos = i + 1
        if i >= self.d.size - 1:
            # We're done.
            raise StopIteration
        self.len -= 1
        return self._extract(self.d.table[i])

    __next__ = next

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
def testing(dict_size = 2000, num_items = None, load_factor = 0.5):
    counts['compare'] = 0
    if num_items == None:
        num_items = dict_size * load_factor
    random.seed(3)
    cd = Dict(dict_size)
    i = 0
    while i < num_items:
        s = ''.join(random.choice(string.letters) for k in range(10))
        cd[s] = random.randint(3,9)
        i += 1
    ll1 = cd.keys()
    counts['compare'] = 0
    for i in range(len(ll1)):
        ll1[i] in cd
    print 'Average number of comparisons: ', (1.0*counts['compare'])/len(ll1)
    print 'Load factor: ', (1.0*len(ll1))/dict_size
            
if __name__ == '__main__':
    
    mytimes = {}
    for dict_size in range(1100, 3000, 500):
        times['testing'] = 0
        testing(dict_size = dict_size)
        mytimes[dict_size] = times['testing']
