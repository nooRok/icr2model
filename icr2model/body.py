# coding: utf-8
import warnings
from itertools import chain

from .flavor import *


def build_redirection_map(flavors):
    """

    :param dict[int, Flavor] flavors:
    :return:
    :rtype: dict[int, int]
    """
    items = sorted(flavors.items())
    types_map = {}  # type: dict[int, list[int]] #
    for o, f in items:  # type: int, Flavor
        types_map.setdefault(f.type, []).append(o)
    redir_map = {}
    for offset, flavor in items:  # type: int, Flavor
        eq_offsets = (o for o in types_map[flavor.type]
                      if (o < offset) and (flavors[o] == flavor))
        eq_offset = next(eq_offsets, None)
        if eq_offset is not None:
            redir_map[offset] = eq_offset
    return redir_map


def build_vertices_redirection_map(flavors):
    """

    :param dict[int, VertexFlavor] flavors:
    :return:
    :rtype: dict[int, int]
    """
    v01_flavors = {}  # type: dict[int, VertexFlavor] #
    v02_flavors = {o: f for o, f in flavors.items() if f.vtype == 2}
    v02_co_map = {f.co: o for o, f in v02_flavors.items()}
    redir_map = build_redirection_map(v02_flavors)
    for offset in (o for o, f in flavors.items() if f.vtype == 1):
        flavor = flavors[offset]
        v02_offset = v02_co_map.get(flavor.co)
        if v02_offset is None:
            v01_flavors[offset] = flavor
        else:
            redir_map[offset] = redir_map.get(v02_offset, v02_offset)
    redir_map.update(build_redirection_map(v01_flavors))
    return redir_map


def get_redirection_map(flavors):
    """
    *Pending Deprecation*

    :param dict[int, Flavor] flavors:
    :return:
    :rtype: dict[int, int]
    """
    warnings.warn('use build_redirection_map()',
                  PendingDeprecationWarning)
    return build_redirection_map(flavors)


def get_vertices_redirection_map(flavors):
    """
    *Pending Deprecation*

    :param dict[int, VertexFlavor] flavors:
    :return:
    :rtype: dict[int, int]
    """
    warnings.warn('use build_vertices_redirection_map()',
                  PendingDeprecationWarning)
    return build_vertices_redirection_map(flavors)


class Body:
    """
    .. attribute:: flavors

        :type: dict[int, Flavor]

    """

    def __init__(self, flavors=None):
        """

        :param dict[int, Flavor] flavors:
        """
        self.flavors = {} if flavors is None else flavors  # type: dict[int, Flavor] # noqa

    def _read_flavor(self, data, offset, parent=None):
        """

        :param io.BytesIO|io.FileIO data:
        :param int offset: flavor 読み込み開始位置
        :param int parent:
        """
        if offset in self.flavors:
            self.flavors[offset].parents.append(parent)
            return
        data.seek(offset)
        flag = Flag.from_stream(data)
        flavor = build_flavor(offset, flag.type, parent)  # type: Flavor
        self.flavors[offset] = flavor
        flavor.read(data)
        if isinstance(flavor, RefFlavor):
            for child in flavor.children:
                self._read_flavor(data, child, offset)
        if isinstance(flavor, F13):
            self._read_flavor(data, flavor.origin, offset)
        if isinstance(flavor, F16):
            self._read_flavor(data, flavor.next_offset, offset)

    def _read_vertex(self, data):
        """

        :param io.BytesIO|io.FileIO data:
        """
        flavors = self.get_flavors(0)  # type: dict[int, VertexFlavor] #
        for offset, flavor in flavors.items():
            vtype = max(self.flavors[p].type for p in set(flavor.parents))
            flavor.set_vtype(1 if vtype == 13 else vtype)
            data.seek(offset + 4)
            flavor.read(data)

    def read(self, data, root_offset):
        """

        :param io.BytesIO|io.FileIO data:
        :param int root_offset:
        """
        self._read_flavor(data, root_offset)
        self._read_vertex(data)
        if self.has_flavor_type(12):  # track
            """
            F11 (parent of LOD managers)
            ├F11 (LOD manager)
            |└F17 (LOD, not included in LOD manager's children)
            ├F11 (LOD manager)
            |└F17 (LOD)
            ├...

            LOD manager.children: [H, H, H, H, M, M, L] (7 items)
            """
            next_flavor = self.flavors[self.root_flavor.next_offset]  # type: F11
            lod_root_offset = next_flavor.children[0]
            lod_root_flavor = self.flavors[lod_root_offset]  # type: F11
            mgr_flavors = (self.flavors[o] for o in lod_root_flavor.children)
            for mgr_flavor in mgr_flavors:  # type: F11
                f17_offset = mgr_flavor.offset + mgr_flavor.length
                self._read_flavor(data, f17_offset, mgr_flavor.offset)

    def get_flavors(self, *types, exclude=False):
        """

        :param int types: 0-18
        :param bool exclude:
        :return:
        :rtype: dict[int, Flavor]
        """
        if types:
            if exclude:
                return {o: f for o, f in self.flavors.items()
                        if f.type not in types}
            return {o: f for o, f in self.flavors.items()
                    if f.type in types}
        return self.flavors.copy()

    def _build_optimization_map(self):
        """

        :return:
        :rtype: dict[int, int]
        """
        vtx_fs = self.get_flavors(0)  # type: dict[int, VertexFlavor] #
        body_fs = self.get_flavors(0, 17, exclude=True)
        for lod_f in self.get_flavors(17).values():
            body_fs.pop(lod_f.parents[0])
        opt_map = {}  # type: dict[int, int] #
        opt_map.update(build_vertices_redirection_map(vtx_fs))
        opt_map.update(build_redirection_map(body_fs))
        return opt_map

    def _get_sorted_offsets(self):
        """

        :rtype: __generator[int]
        """
        yield from (o for o, _ in sorted(self.get_flavors(0).items(),
                                         key=lambda i: (-(i[1].vtype), i[0])))
        if self.is_track():  # track 3do
            next_f = self.flavors[self.root_flavor.next_offset]  # type: F11
            lod_root_f = self.flavors[next_f.children[0]]  # type: F11
            exclude = {self.root_flavor.offset, next_f.offset, lod_root_f.offset}
            exclude.update(lod_root_f.children)  # for under 3.5
            body_fs = self.get_flavors(0, 16, 17, exclude=True)
            yield from (o for o in sorted(body_fs) if o not in exclude)
            if 'assert':
                f17ps = [f.parents for f in self.get_flavors(17).values()]
                assert all(len(p) == 1 for p in f17ps)
                assert (set(lod_root_f.children) == set(p[0] for p in f17ps))
            lod_fs = {f.parents[0]: f for f in self.get_flavors(17).values()}
            for mgr_o in lod_root_f.children:  # type: int
                yield mgr_o
                yield lod_fs[mgr_o].offset
            yield lod_root_f.offset
            if isinstance(self.root_flavor, F16):  # icr2
                yield next_f.offset
            else:  # converted
                assert self.root_flavor == next_f
            yield self.root_offset
        else:  # obj/car
            yield from sorted(self.get_flavors(0, exclude=True))

    def _rebuild(self, optimize=False):
        """

        :param bool optimize:
            Redirect flavor references (`True`) or only remove
            unused data between flavors (`False`).
        :return:
        :rtype: dict[int, Flavor]
        """
        opt_map = self._build_optimization_map() if optimize else {}
        offset_map = {}  # type: dict[int, int] #
        new_fs = {}  # type: dict[int, Flavor] #
        offset = 0
        for org_o in self._get_sorted_offsets():  # type: int
            if org_o in opt_map:
                offset_map[org_o] = offset_map[opt_map[org_o]]
                continue
            offset_map[org_o] = offset
            org_f = self.flavors[org_o]
            new_f = build_flavor(offset, org_f.type)
            if isinstance(org_f, RefFlavor):
                v2 = [offset_map[o] for o in org_f.children]
                for o in v2:
                    new_fs[o].parents.append(offset)
                if isinstance(org_f, F13):
                    origin = offset_map[org_f.origin]
                    new_fs[origin].parents.append(offset)
                    v1 = [origin]
                    v2 = chain(*zip(org_f.distances, v2))
                elif isinstance(org_f, F16):
                    v1_0, v1_1 = org_f.values1.i
                    v1 = (offset_map[v1_0], v1_1)
                    new_fs[v1[0]].parents.append(offset)
                else:
                    v1 = org_f.values1
            else:
                v1, v2 = org_f.values1, org_f.values2
                if isinstance(org_f, F17):
                    lod_mgr_o = new_fs[max(new_fs)].offset  # F11 offset
                    new_f.parents.append(lod_mgr_o)
            new_f.values1.extend(v1)
            new_f.values2.extend(v2)
            new_fs[offset] = new_f
            offset += new_f.length
        return new_fs

    def optimize(self):
        """
        optimize :attr:`flavors` (in-place)
        """
        self.flavors = self._rebuild(True)

    def optimized(self):
        """

        :return: new Body instance that flavors optimized.
        :rtype: Body
        """
        return Body(self._rebuild(True))

    def get_optimization_map(self):
        """
        *Pending Deprecation*

        :return:
        :rtype: dict[int, int]
        """
        warnings.warn('use build_redirection_map()',
                      PendingDeprecationWarning)
        return self._build_optimization_map()

    def get_remapped_flavors(self, optimize=False):
        """
        *Pending Deprecation*

        :param bool optimize:
            Redirect flavor references (`True`) or only remove
            unused data between flavors (`False`).
        :return:
        :rtype: dict[int, Flavor]
        """
        warnings.warn('use Body.optimized().flavors (for optimize=True) or '
                      'use .flavors directly (for optimize=False).',
                      PendingDeprecationWarning)
        return self._rebuild(optimize)

    def get_bytes(self):
        """
        データサイズがoffset位置に満たない場合は ``\\x00`` でパディングされる

        :rtype: bytes
        """
        buffer = bytearray()
        for o, f in sorted(self.flavors.items()):  # type: int, Flavor
            assert o == f.offset
            buffer.extend(bytes(max(0, o - len(buffer))))
            buffer.extend(f.get_bytes())
        return bytes(buffer)

    def dump(self):
        """
        for json

        :return:
        :rtype: dict
        """
        return {o: f.dump() for o, f in self.flavors.items()}

    def has_flavor_type(self, type_):
        """

        :param int type_: 0-18
        :return:
        :rtype: bool
        """
        fs = (f for f in self.flavors.values() if f.type == type_)
        return bool(next(fs, False))

    def is_track(self):
        """

        :return:
        :rtype: bool
        """
        return self.has_flavor_type(12) and self.has_flavor_type(17)

    @property
    def root_offset(self):
        """
        .. note::
            :class:`Flavor` の格納状況によって値が変動するので
            全ての :class:`Flavor` を格納し終えた状態で使用すること

        :rtype: int
        """
        return max(self.flavors.keys())

    @property
    def root_flavor(self):
        """

        :rtype: F16|F11|Flavor
        """
        return self.flavors[self.root_offset]

    @property
    def length(self):
        """
        .. seealso:: :attr:`.root_offset` の注意を参照

        :return:
        :rtype: int
        """
        return self.root_flavor.offset + self.root_flavor.length
