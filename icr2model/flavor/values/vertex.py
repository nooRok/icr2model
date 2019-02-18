# coding: utf-8
from collections import namedtuple

__all__ = ['Coordinates', 'UV']

Coordinates = namedtuple('Coordinates', ['x', 'y', 'z'])
UV = namedtuple('UV', ['u', 'v'])
