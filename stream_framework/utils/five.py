"""
Python 3 compatibility implementations
"""
try:
    long_t = long  # Python 2
except NameError:
    long_t = int   # Python 3
