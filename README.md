PyDict
======

This project provides two simple classes that are drop-in replacement for 
the Python dictionary class written in pure Python. These classes are for 
educational purposes only to illustrate how dictionaries work. They are not 
competitive in terms of real empirical performance. The original version was 
based heavily on Benjamin Peterson's code here:
http://pybites.blogspot.com/2008/10/pure-python-dictionary-implementation.html

The first implementation provided is using open addressing with double 
hashing (currently, the second hash function is a constant, which means 
it behaves like linear probing, but the method hash2 can be replaced for
for better performance as an exercise).

This second implementation is using chaining and requires the package 
coinor.blimpy to be installed (this provides a drop-in replacement for the 
Python list class based on linked lists).

There is a method for visualizing the dictionary that requires pygame.

These classes are used as part of an undergraduate laboratory in the class

IE172: Algorithms in Systems Engineering

at Lehigh University. Check this page for more materials associated with 
the lab (currently Lab 6):

http://coral.ie.lehigh.edu/~ted/teaching/ie172

