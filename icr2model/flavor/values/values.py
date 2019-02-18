# coding: utf-8
import warnings
from collections import Iterable
from struct import pack, unpack

from .vector import Vector

__all__ = ['Values', 'ShortValues', 'BspValues', 'ValuesLengthError']

_sizes = {'l': 4, 'h': 2}


class ValuesLengthError(Exception):
    pass


class Values(list):
    def __init__(self, *args, format_='l', **kwargs):
        super().__init__(*args, **kwargs)
        self._check()
        self._f = format_

    def _check(self):
        if all(isinstance(x, int) for x in self):
            return True
        raise TypeError(self)

    def read(self, stream, size):
        data = stream.read(size)
        size = len(data) // _sizes[self._f]
        fmt = '{}{}'.format(size, self._f)
        self.extend(unpack(fmt, data))

    def set_data(self, data):
        """
        *Pending Deprecation*

        :param bytes data:
        """
        warnings.warn('', PendingDeprecationWarning)
        size = len(data) // _sizes[self._f]
        fmt = '{}{}'.format(size, self._f)
        self.extend(unpack(fmt, data))

    def update(self, data):
        """
        *Pending Deprecation*

        :param bytes|bytearray|Iterable[int]|Values data:
        """
        warnings.warn('', PendingDeprecationWarning)
        if isinstance(data, (bytes, bytearray)):
            self.set_data(data)
        elif isinstance(data, Values):
            self.set_data(data.b)
        elif isinstance(data, Iterable):
            self.extend(data)
        else:
            raise TypeError(type(data))

    @property
    def _format(self):
        return '{}{}'.format(len(self), self._f)

    @property
    def b(self):
        """

        :rtype: bytes
        """
        return pack(self._format, *self)

    @property
    def i(self):
        """

        :rtype: tuple[int]
        """
        return self[:]

    def extend(self, iterable):
        super().extend(iterable)
        self._check()

    def append(self, object):
        super().append(object)
        self._check()


class ShortValues(Values):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, format_='h', **kwargs)


class BspValues(Values):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, format_='5l', **kwargs)
        if len(self) == 4:
            self.distance = self.pop()

    def _check(self, min_=0):
        if super()._check() and min_ <= len(self) <= 5:
            return True
        raise ValuesLengthError(self)

    def read(self, stream, size):
        data = stream.read(size)
        self.extend(unpack(self._f, data))

    def set_data(self, data):
        """
        *Pending Deprecation*

        :param bytes data:
        """
        warnings.warn('', PendingDeprecationWarning)
        self.extend(unpack(self._f, data))

    @property
    def _format(self):
        return self._f

    @property
    def normal(self):
        """

        :rtype: list[int]
        """
        if self._check(3):
            return self[:3]

    @normal.setter
    def normal(self, val):
        self[:3] = val[:3]
        self._check(3)

    @property
    def distance(self):
        """

        :rtype: int
        """
        if self._check(4):
            return unpack('q', pack('2l', self[3], self[4]))[0]

    @distance.setter
    def distance(self, val):
        if self._check(3):
            self[3:] = unpack('2l', pack('q', val))

    @classmethod
    def from_coordinates(cls, co1, co2, co3):
        """
        (x, y, z), (x, y, z), (x, y, z)から法線、距離を算出

        :param Iterable[int] co1: coordinates (x:int, y:int, z:int)
        :param Iterable[int] co2: coordinates (x:int, y:int, z:int)
        :param Iterable[int] co3: coordinates (x:int, y:int, z:int)
        :return: co1, co2, co3から算出した値を格納した新しいBspValuesインスタンス
        :rtype: BspValues
        """
        a, b, c = (Vector(*co1), Vector(*co2), Vector(*co3))
        n = (b - a).cross(c - a).round()
        v = cls(n)
        v.distance = -(n.dot(a))
        return v
