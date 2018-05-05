import math

def anglebetween(a, b):
    """a and b are 2 tuple of coordinates"""
    return math.atan2(a[0] - b[0], a[1] - b[1])
