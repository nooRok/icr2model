# coding: utf-8
from struct import unpack
from warnings import warn

from .value.values import *

__all__ = ['Flavor', 'FixedFlavor', 'RefFlavor', 'VertexFlavor', 'FaceFlavor', 'BspFlavor',
           'F00', 'F01', 'F02', 'F03', 'F04', 'F05', 'F06', 'F07', 'F08', 'F09',
           'F10', 'F11', 'F12', 'F13', 'F14', 'F15', 'F16', 'F17', 'F18',
           'V01', 'V02',
           'FLAGS']

FLAGS = (b'\x00\x00\x00\x00',
         b'\x01\x00\x00\x80',
         b'\x02\x00\x00\x80',
         b'\x03\x00\x00\x80',
         b'\x04\x00\x00\x80',
         b'\x05\x00\x00\x80',
         b'\x06\x00\x00\x80',
         b'\x07\x00\x00\x80',
         b'\x08\x00\x00\x80',
         b'\t\x00\x00\x80',
         b'\n\x00\x00\x80',
         b'\x0b\x00\x00\x80',
         b'\x0c\x00\x00\x80',
         b'\r\x00\x00\x80',
         b'\x0e\x00\x00\x80',
         b'\x0f\x00\x00\x80',
         b'\x10\x00\x00\x80',
         b'\x11\x00\x00\x80',
         b'\x12\x00\x00\x80')

READ_SIZES = ((12, None),  # lllhh(3l2h)
              (8, None),  # var
              (12, None),  # var
              (8, 4),
              (8, 4),
              (20, 4),  # lllq(3lq)
              (20, 8),
              (20, 12),
              (20, 12),
              (20, 16),
              (20, 8),
              (4, None),  # F11 var
              (16, 0),
              (4, None),  # var
              (4, None),
              (28, 0),
              (8, None),  # F16 var
              (16, 0),
              (12, 0))  #: None = variable length


class Flavor:
    TYPE = None

    def __init__(self, offset, parent=None):
        self.offset = offset
        self.parents = [] if parent is None else [parent]
        self.values1 = Values()
        self.values2 = Values()

    def _read_v1(self, st):
        self.values1.read_stream(st, READ_SIZES[self.type][0])

    def _read_v2(self, st):
        self.values2.read_stream(st, READ_SIZES[self.type][1])

    def read_stream(self, st):
        self._read_v1(st)
        self._read_v2(st)

    def to_bytes(self):
        return (FLAGS[self.type] +
                self.values1.to_bytes() +
                self.values2.to_bytes())

    def to_str(self):
        return ' '.join(
            map(str, ['F{:02}'.format(self.type)] + self.values1 + self.values2))

    @property
    def type(self):
        return self.__class__.TYPE

    @property
    def length(self):
        v2len = READ_SIZES[self.type][1] or self.values2.length
        return READ_SIZES[self.type][0] + v2len + 4  # 4 for flag

    def __eq__(self, other):
        return (self.type == other.type and
                self.values1 == other.values1 and
                self.values2 == other.values2)


class FixedFlavor(Flavor):
    pass


class RefFlavor(Flavor):
    @property
    def children(self):
        return self.values2


class VarFlavor(RefFlavor):
    def _read_v2(self, st):
        self.values2.read_stream(st, self.values1[-1] * 4)


class VertexFlavor(FixedFlavor):
    TYPE = 0
    VTYPE = 0

    def __init__(self, offset, parent=None):
        super().__init__(offset, parent)
        self.values1 = CoordinateValues()
        self.values2 = UVValues()
        self._vtype = 0

    def _read_v2(self, st):
        if self.vtype == 2:
            self.values2.read_stream(st, 4)

    def read_stream(self, st):
        if self.vtype:
            super().read_stream(st)

    @property
    def co(self):
        return self.values1.co

    @property
    def uv(self):
        return self.values2.uv

    @property
    def vtype(self):
        return max(self.VTYPE, self._vtype)

    @vtype.setter
    def vtype(self, vtype):
        if vtype == 13:
            vtype = 1
        if vtype in (1, 2) and vtype > self._vtype:
            self._vtype = vtype

    def to_str(self):
        t = 'V{:02}'.format(self.vtype) if self.vtype else 'F00'
        return ' '.join(map(str, [t] + self.values1 + self.values2))

    @property
    def length(self):
        return self.values1.length + self.values2.length + 4  # 4 for flag

    def set_vtype(self, vtype):
        warn('Use .vtype', PendingDeprecationWarning)
        self.vtype = vtype


class F00(VertexFlavor):
    pass


class V01(VertexFlavor):
    VTYPE = 1


class V02(VertexFlavor):
    VTYPE = 2


class FaceFlavor(RefFlavor):
    def _read_v2(self, st):
        self.values2.read_stream(st, (self.values1[-1] + 1) * 4)

    @property
    def color(self):
        """

        :return: 0-255
        :rtype: int
        """
        return self.values1[-2]


class F01(FaceFlavor):
    TYPE = 1


class F02(FaceFlavor):
    TYPE = 2


class F03(FixedFlavor):
    TYPE = 3


class F04(RefFlavor):
    TYPE = 4

    @property
    def index(self):
        """

        :rtype: int
        """
        return self.values1[0]

    @property
    def mip_index(self):
        warn('Use .index', PendingDeprecationWarning)
        return self.index


class BspFlavor(RefFlavor):
    def __init__(self, offset, parent=None):
        super().__init__(offset, parent)
        self.values1 = BspValues()


class F05(BspFlavor):
    TYPE = 5


class F06(BspFlavor):
    TYPE = 6


class F07(BspFlavor):
    TYPE = 7


class F08(BspFlavor):
    TYPE = 8


class F09(BspFlavor):
    TYPE = 9


class F10(BspFlavor):
    TYPE = 10


class F11(VarFlavor):
    TYPE = 11

    @property
    def next_offset(self):
        return self.offset


class F12(FixedFlavor):
    TYPE = 12


class F13(RefFlavor):
    TYPE = 13

    def _read_v2(self, st):
        while True:
            d, o = unpack('2l', st.read(8))
            self.values2.extend((d, o))
            if d == 0:
                break

    @property
    def origin(self):
        return self.values1[0]

    @property
    def distances(self):
        return self.values2[::2]

    @property
    def children(self):
        """

        :rtype: list[int]
        """
        return self.values2[1::2]


class F14(Flavor):
    TYPE = 14

    def _read_v2(self, st):
        self.values2.read_stream(st, self.values1[0] * 8)
        assert self.values1[0] * 2 == len(self.values2)

    def to_bytes(self):
        return super().to_bytes() + b'\xff\xff\xff\xff'

    @property
    def length(self):
        return super().length + 4


class F15(FixedFlavor):
    TYPE = 15

    @property
    def index(self):
        """

        :rtype: int
        """
        return self.values1[-1]

    @property
    def location(self):
        """

        :return: location x, y, z
        :rtype: list[int]
        """
        return self.values1[:3]

    @property
    def rotation(self):
        """

        :return: rotation z, y, x
        :rtype: list[int]
        """
        return self.values1[3:6]

    @property
    def object_index(self):
        warn('Use .index', PendingDeprecationWarning)
        return self.index


class F16(VarFlavor):
    TYPE = 16

    @property
    def next_offset(self):
        return self.values1[0]


class F17(FixedFlavor):
    TYPE = 17


class F18(FixedFlavor):
    TYPE = 18

    @property
    def index(self):
        """

        :rtype: int
        """
        return self.values1[-1]

    @property
    def pmp_index(self):
        warn('Use .index', PendingDeprecationWarning)
        return self.index
