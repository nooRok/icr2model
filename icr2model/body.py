# coding: utf-8
from warnings import warn

from .flavor import *
from .flavor.flavor import *


class Body:
    def __init__(self, flavors=None):
        self.flavors = Flavors()  # type: Flavors[int, Flavor]

    def _read_flavor(self, st, offset, parent=None, *_):
        if offset < 0:
            return
        if offset in self.flavors:
            self.flavors[offset].parents.append(parent)
            return
        st.seek(offset)
        f = build_flavor(FLAGS.index(st.read(4)), offset, parent)
        f.read(st)
        self.flavors[offset] = f
        if isinstance(f, RefFlavor):
            for child in f.children:
                self._read_flavor(st, child, offset)
        if isinstance(f, F13):
            self._read_flavor(st, f.origin, offset)
        if isinstance(f, F16):
            self._read_flavor(st, f.next_offset, offset)

    def _read_lod(self, st, root_offset):
        root_f = self.flavors[root_offset]  # type: F16
        next_f = self.flavors[root_f.next_offset]  # type: RefFlavor
        lod_root_f = self.flavors[next_f.children[0]]  # type: F11
        mgr_fs = (self.flavors[o] for o in lod_root_f.children)
        for mgr_f in mgr_fs:  # type: F11
            f17_o = mgr_f.offset + mgr_f.length
            self._read_flavor(st, f17_o, mgr_f.offset)

    def _read_vertex(self, st):
        for f in self.flavors.by_types(0).values():  # type: Flavor
            for vtype in set(self.flavors[p].type for p in f.parents):
                f.vtype = vtype
            st.seek(f.offset + 4)
            f.read(st)

    def read(self, stream, root_offset):
        with self.flavors:
            self._read_flavor(stream, root_offset)
            if self.flavors.has_types(12):  # track
                self._read_lod(stream, root_offset)
        self._read_vertex(stream)

    def to_bytes(self):
        b = b''
        for o, f in sorted(self.flavors.items()):  # type: int, Flavor
            assert f.length == len(f.to_bytes()), [f, f.offset, f.length, len(f.to_bytes())]
            b += bytes(o - len(b)) + f.to_bytes()
        return b

    def get_flavors(self, *types):
        warn('Use .flavors.by_types()', DeprecationWarning)
        return self.flavors.by_types(*types)
