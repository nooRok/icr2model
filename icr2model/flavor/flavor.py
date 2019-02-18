# coding: utf-8
from .flag import Flag
from .values import Values, BspValues, Coordinates, UV

__all__ = ['Flavor',
           'FixedFlavor',
           'RefFlavor',
           'VertexFlavor',
           'FaceFlavor',
           'BspFlavor',
           'F00',
           'V01',
           'V02',
           'F01',
           'F02',
           'F04',
           'F05',
           'F06',
           'F07',
           'F08',
           'F09',
           'F10',
           'F11',
           'F12',
           'F13',
           'F14',
           'F15',
           'F16',
           'F17',
           'F18']

_READ_SIZES = ((12, None),  # lllhh(3l2h)
               (8, None),  # var
               (12, None),  # var
               (12, 0),
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
    """
    .. attribute:: parents

        :type: list[int]
    """
    padding = False  #: for __str__() formatting flag

    def __init__(self, offset, type_, parent=None):
        """

        :param int offset:
        :param int type_:
        :param int parent:
        """
        self._offset = offset
        self._type = type_
        self._values1 = Values()
        self._values2 = Values()
        self.parents = []  # type: list[int] #
        if parent is not None:
            self.parents.append(parent)

    def read(self, data):
        """

        :param io.BytesIO|io.FileIO data:
        """
        read_sizes = _READ_SIZES[self._type]
        for value, size in zip((self._values1, self._values2), read_sizes):
            value.read(data, size)

    @property
    def offset(self):
        """

        :rtype: int
        """
        return self._offset

    @property
    def type(self):
        """

        :rtype: int
        """
        return self._type

    @property
    def values1(self):
        """

        :rtype: Values
        """
        return self._values1

    @property
    def values2(self):
        """

        :rtype: Values
        """
        return self._values2

    def get_bytes(self):
        """

        :rtype: bytes
        """
        values = (Flag(self._type).b,
                  self._values1.b,
                  self._values2.b)
        return b''.join(values)

    @property
    def length(self):
        """

        :return: flavor flag length (4) + flavor values bytes length
        :rtype: int
        """
        sizes = (4, _READ_SIZES[self.type][0],
                 _READ_SIZES[self.type][1] or len(self._values2.b))
        return sum(sizes)

    @property
    def _def_type(self):
        """
        for str, n2def

        :return:
        """
        return 'F{:02}'.format(self._type)

    def __str__(self):
        values = [self._def_type,
                  '{:>{w}}'.format(self._offset, w=6 if self.padding else 0)]
        values.extend('{:>{w}}'.format(v, w=11 if self.padding else 0)
                      for v in self._values1.i)
        values.extend('{:>{w}}'.format(v, w=11 if self.padding else 0)
                      for v in self._values2.i)
        return ' '.join(values)

    def __eq__(self, other):
        return (type(self) == type(other) and
                self.values1 == other.values1 and
                self.values2 == other.values2)

    def dump(self):
        return {'type': self.type,
                'values1': self.values1.i,
                'values2': self.values2.i,
                'parents': self.parents}


class FixedFlavor(Flavor):
    """
    flavor with fixed length values
    """


class RefFlavor(Flavor):
    """
    flavor; refer to other flavor(s)
    """

    @property
    def children(self):
        """

        :rtype: tuple[int]
        """
        return self._values2.i


class VarFlavor(RefFlavor):
    """
    flavor with variable number of reference(s): variable length values
    """

    def read(self, data):
        """

        :param io.BytesIO|io.FileIO data:
        """
        v1_size = _READ_SIZES[self._type][0]
        self._values1.read(data, v1_size)
        v2_size = self._values1.i[-1] * 4
        self._values2.read(data, v2_size)


class VertexFlavor(FixedFlavor):
    """
    F00 / V01 / V02

    * flag: ``\\x00\\x00\\x00\\x00``
    * values1: 4 bytes * 3; x, y, z (if vtype 1 or 2)
    * values2: 2 bytes * 2; u, v (if vtype 2)

    vtype definitions:
        * 0: nill (F00)
        * 1: plane (V01)
        * 2: textured (V02)

    parentにFaceFlavorが含まれていればV01/V02
    含まれていなければF00
    """
    _VTYPE = ('F00', 'V01', 'V02')

    def __init__(self, offset, type_=0, parent=None):
        super().__init__(offset, type_, parent)
        self._vtype = 0  # vertex type: 0=null, 1=vtx, 2=vtx with uv
        self._values1 = Values()
        self._values2 = Values(format_='h')

    def read(self, data):
        """

        :param io.BytesIO|io.FileIO data:
        :return:
        """
        if self._vtype:
            self._values1.read(data, _READ_SIZES[0][0])
            if self._vtype == 2:
                self._values2.read(data, 4)
        else:
            return

    def set_vtype(self, vtype):
        """

        :param int vtype: 0-2
        """
        if vtype in (1, 2):
            if vtype > self._vtype:
                self._vtype = vtype

    @property
    def vtype(self):
        """

        :return: 0-2
        :rtype: int
        """
        return self._vtype

    @property
    def co(self):
        """

        :return: Coordinates(int x, int y, int z)
        :rtype: Coordinates
        """
        return Coordinates(*self._values1.i)

    @property
    def uv(self):
        """

        :return: UV(int u, int v)
        :rtype: UV
        """
        return UV(*self._values2.i)

    @property
    def _def_type(self):
        type_ = ('V01' if self._vtype == 1 else
                 'V02' if self._vtype == 2 else
                 'F00')
        return type_

    def dump(self):
        d = super().dump()
        d['vtype'] = self._vtype
        return d


class F00(VertexFlavor):
    def __init__(self, offset, parent=None):
        super().__init__(offset, 0, parent)


class V01(VertexFlavor):
    def __init__(self, offset, parent=None):
        super().__init__(offset, 0, parent)


class V02(VertexFlavor):
    def __init__(self, offset, parent=None):
        super().__init__(offset, 0, parent)


class FaceFlavor(RefFlavor):
    """
    F01 / F02

    * flag: ``\\x01\\x00\\x00\\x80`` or ``\\x02\\x00\\x00\\x80``
    * values1:
        * F01: 4 bytes * 3; color, num of vertices-1
        * F02: 4 bytes * 4; textureflag, color, number of vertices-1
    * values2: 4 bytes * n (number of vertices)

    textureflag:
        * 1 = Asphalt/Concrete
        * 2 = Grass/Dirt
        * 4 = Wall
        * 8 = Trackside Object
        * 16 = Car Decals
        * 32 = Horizont
        * 64 = Grandstand
    """

    def read(self, data):
        """

        :param io.BytesIO|io.FileIO data:
        """
        v1_size = _READ_SIZES[self._type][0]
        self._values1.read(data, v1_size)
        v2_size = (self._values1.i[-1] + 1) * 4
        self._values2.read(data, v2_size)

    @property
    def color(self):
        """

        :return: 0-255
        :rtype: int
        """
        return self._values1.i[-2]


class F01(FaceFlavor):
    def __init__(self, offset, parent=None):
        super().__init__(offset, 1, parent)


class F02(FaceFlavor):
    def __init__(self, offset, parent=None):
        super().__init__(offset, 2, parent)


class F04(RefFlavor):
    """
    F04: mip

    * flag: ``\\x04\\x00\\x00\\x80``
    * values1: 4 bytes * 3; file index, color, offset
    * values2: 4 bytes
    """

    def __init__(self, offset, parent=None):
        super().__init__(offset, 4, parent)

    @property
    def mip_index(self):
        """

        :rtype: int
        """
        return self._values1.i[0]


class BspFlavor(RefFlavor):
    """
    F05 / F06 / F07 / F08 / F09 / F10: definition drawing order

    * flag:
        ``\\x05\\x00\\x00\\x80``, ``\\x06\\x00\\x00\\x80``, ``\\x07\\x00\\x00\\x80``, ``\\x08\\x00\\x00\\x80``,
        ``\\x09\\x00\\x00\\x80 (\\t\\x00\\x00\\x80)`` or ``\\x10\\x00\\x00\\x80 (\\n\\x00\\x00\\x80)``
    * values1: 4 bytes * 5 (4 bytes * 3 + 8 bytes); normal (x, y, z), distance
    * values2:
        * F05: 4 bytes
        * F06: 4 bytes * 2
        * F07: 4 bytes * 3
        * F08: 4 bytes * 3
        * F09: 4 bytes * 4
        * F10: 4 bytes * 2
    """

    def __init__(self, offset, type_, parent=None):
        super().__init__(offset, type_, parent)
        self._values1 = BspValues()
        self._values2 = Values()


class F05(BspFlavor):
    def __init__(self, offset, parent=None):
        super().__init__(offset, 5, parent)


class F06(BspFlavor):
    def __init__(self, offset, parent=None):
        super().__init__(offset, 6, parent)


class F07(BspFlavor):
    def __init__(self, offset, parent=None):
        super().__init__(offset, 7, parent)


class F08(BspFlavor):
    def __init__(self, offset, parent=None):
        super().__init__(offset, 8, parent)


class F09(BspFlavor):
    def __init__(self, offset, parent=None):
        super().__init__(offset, 9, parent)


class F10(BspFlavor):
    def __init__(self, offset, parent=None):
        super().__init__(offset, 10, parent)


class F11(VarFlavor):
    """
    F11: groups other flavors

    * flag: ``\\x0b\\x00\\x00\\x80``
    * values1: 4 bytes; number of grouping objects
    * values2: 4 bytes * n; objects
    """

    def __init__(self, offset, parent=None):
        super().__init__(offset, 11, parent)

    @property
    def next_offset(self):
        """

        :return: for converted track model. see F16.next_offset
        :rtype: int
        """
        return self._offset


class F12(FixedFlavor):
    """
    F12: track ?

    * flag: ``\\x0c\\x00\\x00\\x80``
    * values1: 4 bytes * 4
    """

    def __init__(self, offset, parent=None):
        super().__init__(offset, 12, parent)


class F13(RefFlavor):
    """
    F13: object LOD detail

    * flag: ``\\x0d\\x00\\x00\\x80 (\\r\\x00\\x00\\x80)``
    * values1: 4 bytes; [0] reference point(center of object?)
    * values2: 4 bytes * n;
        | [far dist, far offset, ..., near dist, near offset]
        | [0, 1] distance, flavor offset
        | [2, 3] distance, flavor offset...
    """

    def __init__(self, offset, parent=None):
        super().__init__(offset, 13, parent)

    def read(self, data):
        """
        read処理終了条件:
            distance value == 0

        .. note::
            (dist, offset) * 4 で固定?

        :param io.BytesIO|io.FileIO data:
        """
        self._values1.read(data, _READ_SIZES[13][0])
        while True:
            d, o = (int.from_bytes(data.read(4), 'little'),
                    int.from_bytes(data.read(4), 'little'))
            self._values2.extend((d, o))
            if d == 0:
                break

    @property
    def origin(self):
        """

        :rtype: int
        """
        return self.values1.i[0]

    @property
    def distances(self):
        """

        :rtype: list[int]
        """
        return self._values2.i[::2]

    @property
    def children(self):
        """

        :rtype: list[int]
        """
        return self._values2.i[1::2]


class F14(Flavor):
    """
    F14: car color definitions

    * flag: ``\\x0e\\x00\\x00\\x80``
    * values1: 4 bytes * n; see read() doc
    * values2: (4 bytes, 4 bytes) * n; pairs of color index and palette index

    * colors[:30]: car 3do colors
    * colors[30:60]: pit crew (30 colors)
    * colors[60:]: helmet pmp (8 colors)
    """
    _TERMINATION = bytearray((255, 255, 255, 255))  # -1, \xff\xff\xff\xff

    def __init__(self, offset, parent=None):
        super().__init__(offset, 14, parent)

    def read(self, data):
        """

        :param io.BytesIO|io.FileIO data: data
        """
        self._values1.read(data, _READ_SIZES[14][0])
        self._values2.read(data, self._values1.i[0] * 8)
        assert self._values1.i[0] * 2 == len(self._values2.i)

    @property
    def indices(self):
        """

        :rtype: list[int]
        """
        return self._values2.i[::2]

    @property
    def colors(self):
        """

        :rtype: list[int]
        """
        return self._values2.i[1::2]


class F15(FixedFlavor):
    """
    F15: ObjectFlavor

    * flag: ``\\x0f\\x00\\x00\\x80``
    * values1: 4 bytes * 7; object x, y, z, rot z, rot y, rot x, file index
    """

    def __init__(self, offset, parent=None):
        super().__init__(offset, 15, parent)

    @property
    def object_index(self):
        """

        :return: ~(object_index) = index of files['3do']
        :rtype: int
        """
        return self._values1.i[-1]

    @property
    def location(self):
        """

        :return: location x, y, z
        :rtype: tuple[int]
        """
        return self._values1.i[:3]

    @property
    def rotation(self):
        """

        :return: rotation z, y, x
        :rtype: tuple[int]
        """
        return self._values1.i[3:6]


class F16(VarFlavor):
    """
    F16: root

    * flag: ``\\x10\\x00\\x00\\x80``
    * values1: 4 bytes * 2; next offset, number of objects
    * values2: 4 bytes * n; objects
    """

    def __init__(self, offset, parent=None):
        super().__init__(offset, 16, parent)

    @property
    def next_offset(self):
        """

        :return:
        :rtype: int
        """
        return self._values1.i[0]


class F17(FixedFlavor):
    """
    F17: LOD for track

    * flag: ``\\x11\\x00\\x00\\x80``
    * values1: 4 bytes * 4; track positions?
    """

    def __init__(self, offset, parent=None):
        super().__init__(offset, 17, parent)

    @property
    def manager_offset(self):
        """

        :return: lod manager (F11) offset
        :rtype: int
        """
        return self.offset + self.length


class F18(FixedFlavor):
    """
    F18: pmp

    * flag: ``\\x12\\x00\\x00\\x80``
    * values1: 4 bytes * 3;
        * 0 - 3 size?
        * 4 - 7 size?
        * 8 - 11 pmp index?

    point to multiple pmp position?

    helmet.3do::

        ボディ開始オフセットからpmpflavorまでzerofillで動作可
        (58-)からF18開始オフセットまでFFfill動作可
        helmet.3doはfill:300で動作(300未満だと動作するが表示されない)
        helmet.3doのheadersizeは84bytes
        384bytesまでがヘッダとみなされる？
    """

    def __init__(self, offset, parent=None):
        super().__init__(offset, 18, parent)

    def read(self, data):
        """

        :param io.BytesIO|io.FileIO data:
        """
        super(F18, self).read(data)
        pass

    @property
    def pmp_index(self):
        """

        :rtype: int
        """
        return self._values1.i[-1]
