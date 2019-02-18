# -*- coding: utf-8 -*-
from collections import namedtuple

from .unit import is_int32

__all__ = ['Vector']


def dot(a, b):
    """

    :param Sequence[int] a:
    :param Sequence[int] b:
    :return:
    :rtype: int
    """
    return sum(a * b for a, b in zip(a, b))


def cross(a, b):
    """

    :param Sequence[int] a:
    :param Sequence[int] b:
    :return:
    :rtype: tuple[int]
    """
    c = (a[1] * b[2] - a[2] * b[1],
         a[2] * b[0] - a[0] * b[2],
         a[0] * b[1] - a[1] * b[0])
    return c


class Vector(namedtuple('Vector', ['x', 'y', 'z'])):
    def __new__(cls, x, y, z):
        return super().__new__(cls, *map(round, (x, y, z)))

    def round(self):
        """
        for normal vector

        :return: values rounded to 2147483648 < x < -2147483649
        :rtype: Vector
        """
        if all(is_int32(v) for v in self):
            return self
        return (self / 2).round()

    def dot(self, other):
        """

        :param Vector other:
        :return:
        """
        return dot(self, other)

    def cross(self, other):
        """

        :param Vector other:
        :return:
        """
        return Vector(*cross(self, other))

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Vector(*(x * other for x in self))
        return self.dot(other)

    def __neg__(self):
        return Vector(*(-vec for vec in self))

    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(*(map(sum, zip(self, other))))
        raise TypeError

    def __sub__(self, other):
        return self.__add__(-other)

    def __floordiv__(self, other):
        """

        :rtype: Vector
        """
        if isinstance(other, int):
            return Vector(*(p // other for p in self))
        raise TypeError

    def __truediv__(self, other):
        return self.__floordiv__(other)
