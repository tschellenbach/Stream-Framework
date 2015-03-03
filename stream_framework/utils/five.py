"""
Python 3 compatibility implementations
"""
import sys

if sys.version > '3':
    long_t = int
else:
    long_t = long