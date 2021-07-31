# coding: utf-8
from collections import Iterable, defaultdict

from .flavor import *

__all__ = ['build_flavor', 'Flavors']

_FLAVOR = (F00,  # \x00\x00\x00\x00 F00, V01, V02
           F01,  # \x01\x00\x00\x80
           F02,  # \x02\x00\x00\x80
           F03,  # F03
           F04,  # \x04\x00\x00\x80
           F05,  # \x05\x00\x00\x80
           F06,  # \x06\x00\x00\x80
           F07,  # \x07\x00\x00\x80
           F08,  # \x08\x00\x00\x80
           F09,  # \t\x00\x00\x80
           F10,  # \n\x00\x00\x80
           F11,  # \x0b\x00\x00\x80
           F12,  # \x0c\x00\x00\x80
           F13,  # \r\x00\x00\x80
           F14,  # \x0e\x00\x00\x80
           F15,  # \x0f\x00\x00\x80
           F16,  # \x10\x00\x00\x80
           F17,  # \x11\x00\x00\x80
           F18)  # \x12\x00\x00\x80


def build_flavor(type_, offset, parent=None, values1=None, values2=None, **_):
    """

    :param int type_:
    :param int offset:
    :param int parent:
    :param values1:
    :param values2:
    :return:
    :rtype: Flavor
    """
    f = _FLAVOR[type_](offset)
    if isinstance(parent, (int, Iterable)):
        p = [parent] if isinstance(parent, int) else parent
        f.parents[:] = p
    if isinstance(f, VertexFlavor):
        f.vtype = 2 if values2 else 1 if values1 else 0
    f.values1[:] = values1 or []
    f.values2[:] = values2 or []
    return f


class Flavors(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._by_type = defaultdict(set)  # type: dict[int, set[int]]  # offsets by type
        self._cmp_map = {}

    def by_types(self, *types):  # make sure to build ._by_type
        """

        :param types: Flavor type(s) 0-18
        :return: Dict of flavors filtered by an argument ``types``
        :rtype: dict[int, Flavor]
        """
        if self.has_types(*types):
            offsets = [o for t in types for o in self._by_type[t]]
            return {o: self[o] for o in offsets}
        return {}

    def has_types(self, *types):
        """

        :param types: Flavor type(s) 0-18
        :return:
        :rtype: bool
        """
        t = ((k for k, v in self._by_type.items() if v) if self._by_type else
             (f.type for f in self.values()))
        return bool(set(t) & set(types))

    def _get_eq_flavor(self, offset, offsets):
        eq_os = (o for o in offsets if self._cmp_map[o] == self._cmp_map[offset])
        return next(eq_os, None)

    def _gen_redirections(self, offsets):
        os_ = sorted(offsets)
        while os_:
            o = os_.pop()
            eq_o = self._get_eq_flavor(o, os_)
            if eq_o is not None:
                yield o, eq_o

    def _gen_vtx_redirections(self):
        vtx_os = sorted(self._by_type[0])
        v01_os = [o for o in vtx_os if self[o].vtype == 1]
        v02_os = [o for o in vtx_os if self[o].vtype == 2]
        v02_co_map = {self[o].co: o for o in v02_os}
        vtx_map = dict(self._gen_redirections(v02_os))  # type: dict[int, int]
        while v01_os:  # v01
            v01_o = v01_os.pop()
            v01_co = self[v01_o].co
            v02_o = (v02_co_map[v01_co] if v01_co in v02_co_map else
                     self._get_eq_flavor(v01_o, v01_os))  # avoid to skip v02 with offset 0
            if v02_o is not None:
                yield v01_o, vtx_map.get(v02_o, v02_o)
        yield from vtx_map.items()  # v02

    def _generate_redirections(self, *types):
        for t in types or range(19):
            if t == 0:
                yield from self._gen_vtx_redirections()
            elif t == 11:
                mgr_os = {self[o].parents[0] for o in self._by_type[17]}  # mgr_os == lod_root_f.children
                f11_os = self._by_type[11] - mgr_os
                yield from self._gen_redirections(f11_os)
            elif t == 12:
                pass
            elif t == 17:
                pass
            else:
                yield from self._gen_redirections(self._by_type[t])

    def _generate_sorted_offsets(self):  # chg only orders
        vtx_os = self._by_type[0]
        yield from sorted(vtx_os, key=lambda o: (-self[o].vtype, o))
        if self.has_types(12) and self.has_types(17):  # trk
            root_f = self[max(self)]
            next_f = self[root_f.next_offset]  # type: F11
            lod_root_f = self[next_f.children[0]]  # type: F11
            excls = ({root_f.offset, next_f.offset, lod_root_f.offset, *lod_root_f.children} |
                     self._by_type[0] | self._by_type[17])
            yield from sorted(set(self) - excls)
            lod_os = {self[o].parents[0]: o for o in self._by_type[17]}  # F11: F17
            assert set(lod_root_f.children) == set(lod_os), \
                [sorted(lod_root_f.children), sorted(lod_os)]
            for mgr_o in lod_root_f.children:
                yield mgr_o  # F11
                yield lod_os[mgr_o]  # F17
            yield lod_root_f.offset
            if isinstance(root_f, F16):  # icr2
                yield next_f.offset
            else:  # converted
                assert root_f == next_f
            yield root_f.offset
        else:  # obj/car
            yield from sorted(set(self) - vtx_os)

    def sorted(self, optimize=True):
        """

        :param bool optimize:
            A flag to merge redundant flavors (they have same values) to single flavor and
            make their parents refer merged flavor
        :return: New flavors object
        :rtype: Flavors
        """
        opt_map = dict(self._generate_redirections()) if optimize else {}  # type: dict[int, int]
        new_os = {}  # type: dict[int, int]  # org offset: new offset
        new_fs = {}  # type: dict[int, Flavor]
        offset = 0
        for org_o in self._generate_sorted_offsets():  # type: int
            if org_o in opt_map:
                new_os[org_o] = new_os[opt_map[org_o]]
                continue
            new_os[org_o] = offset
            org_f = self[org_o]
            if isinstance(org_f, F04) and org_o == 0:
                # and org_f.children == [-1]
                v1, v2 = org_f.values1, org_f.values2
            elif isinstance(org_f, RefFlavor):
                v2 = [new_os[o] for o in org_f.children]
                for o in v2:
                    new_fs[o].parents.append(offset)
                if isinstance(org_f, F13):
                    v1 = [new_os[org_f.origin]]
                    v2 = [v for vs in zip(org_f.distances, v2) for v in vs]
                    new_fs[v1[0]].parents.append(offset)
                elif isinstance(org_f, F16):
                    v1 = (new_os[org_f.values1[0]], org_f.values1[1])
                    new_fs[v1[0]].parents.append(offset)
                else:
                    v1 = org_f.values1
            else:
                v1, v2 = org_f.values1, org_f.values2
            new_f = build_flavor(org_f.type, offset, values1=v1, values2=v2)
            if isinstance(org_f, F17):
                lod_mgr_o = new_fs[max(new_fs)].offset  # F11 offset
                new_f.parents.append(lod_mgr_o)
            new_fs[offset] = new_f
            offset += new_f.length
        with Flavors(new_fs) as fs:  # for to build ._by_type
            return fs

    def sort(self, optimize=True):
        """

        :param bool optimize: See description of param ``optimize`` of :meth:`icr2model.flavor.Flavors.sorted`
        :return:
        """
        new_fs = self.sorted(optimize)
        self.clear()
        self._by_type.clear()
        self._cmp_map.clear()
        with self:
            self.update(new_fs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for o, f in self.items():  # type: int, Flavor
            self._by_type[f.type].add(o)
            self._cmp_map[o] = (f.type, tuple(f.values1), tuple(f.values2))
