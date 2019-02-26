# coding: utf-8
from collections import namedtuple

from .unit import is_int32


class Vector(namedtuple('Vector', ['x', 'y', 'z'])):
    def __new__(cls, *pt):
        return super().__new__(cls, *map(int, pt))

    def round(self):
        if all(map(is_int32, self)):
            return self
        return (self // 2).round()

    @classmethod
    def dot(cls, va, vb):
        return sum(a * b for a, b in zip(cls(*va), cls(*vb)))

    @classmethod
    def cross(cls, va, vb, vc):
        ab = cls(*vb) - cls(*va)
        ac = cls(*vc) - cls(*va)
        return cls(ab.y * ac.z - ab.z * ac.y,
                   ab.z * ac.x - ab.x * ac.z,
                   ab.x * ac.y - ab.y * ac.x)

    def __neg__(self):
        return Vector(*(-p for p in self))

    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(*(sum(ps) for ps in zip(self, other)))
        raise TypeError

    def __sub__(self, other):
        return self.__add__(-other)

    def __floordiv__(self, other):
        if isinstance(other, int):
            return Vector(*(p // other for p in self))
        raise TypeError

    def __truediv__(self, other):
        return self.__floordiv__(other)
