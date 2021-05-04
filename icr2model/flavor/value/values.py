# coding: utf-8
from array import array
from collections import namedtuple
from struct import unpack, pack
from warnings import warn

from .vector import Vector

__all__ = ['Values', 'BspValues', 'CoordinateValues', 'UVValues']


class ValuesLengthError(Exception):
    pass


class Values(list):
    _TYPECODE = 'l'

    def read(self, stream, size):
        self.extend(array(self._TYPECODE, stream.read(size)))

    def to_bytes(self):
        b = pack('{}{}'.format(len(self), self._TYPECODE), *self)
        if len(b) != self.length:
            raise ValuesLengthError
        return b

    @property
    def length(self):
        return len(self) * 4

    @property
    def i(self):
        warn('Use .values1/2 itself', PendingDeprecationWarning)
        return self


class BspValues(Values):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self:
            if len(self) < 3 or len(self) > 5:
                raise ValuesLengthError(args, kwargs)
            if len(self) == 3:
                self.extend([0, 0])
            if len(self) == 4:
                self.magnitude = self.pop()

    @property
    def normal(self):
        return self[:3]

    @normal.setter
    def normal(self, values):
        if len(values) != 3:
            raise ValuesLengthError
        self[:3] = values

    @property
    def magnitude(self):
        return unpack('q', pack('2l', *self[3:]))[0]

    @magnitude.setter
    def magnitude(self, val):
        """

        :param int val:
        """
        self[3:] = unpack('2l', pack('q', val))

    @property
    def length(self):
        return 20

    @classmethod
    def from_coordinates(cls, co1, co2, co3):
        va, vb, vc = (Vector(*co) for co in (co1, co2, co3))
        normal = Vector.cross(va, vb, vc).round()  # value A, B, C
        distance = -Vector.dot(va, normal)  # value D abs?
        bspv = cls(normal)
        bspv.magnitude = distance
        return bspv


class CoordinateValues(Values):
    Coordinate = namedtuple('Coordinate', ['x', 'y', 'z'])

    @property
    def co(self):
        return self.Coordinate(*self)

    @property
    def length(self):
        return 12 if self else 0


class UVValues(Values):
    _TYPECODE = 'h'
    UV = namedtuple('UV', ['u', 'v'])

    @property
    def uv(self):
        return self.UV(*self)

    @property
    def length(self):
        return 4 if self else 0
