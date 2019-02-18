# coding: utf-8
import warnings
from collections import namedtuple
from io import BytesIO

from .body import Body
from .flavor import build_flavor, VertexFlavor
from .header import Header

_types = ('TRACK', 'OBJECT', 'CAR')


class Model:
    Types = namedtuple('Types', _types)(*_types)

    def __init__(self, filepath=''):
        """

        :param str filepath:
        """
        self._filepath = filepath
        self._header = Header()
        self._body = Body()

    def read(self):
        with open(self._filepath, 'rb') as data:
            self._header.read(data)
            body = BytesIO(data.read())
        self._body.read(body, self._header.root_offset)

    def _ensure_header_values(self):
        self._header.body_size = self._body.length
        self._header.root_offset = self._body.root_offset

    def optimize(self):
        self._body.optimize()
        self._ensure_header_values()

    def optimized(self):
        model = self.__class__(self._filepath)
        model.body.flavors.update(self._body.optimized().flavors)
        model.header.set_files(**self._header.files)
        model._ensure_header_values()
        return model

    def get_bytes(self, optimize=False):
        """

        :param bool optimize: *Pending Deprecation*
        :return:
        :rtype: bytes
        """
        if optimize:
            warnings.warn('use Model.optimized().get_bytes()',
                          PendingDeprecationWarning)
            return self.optimized().get_bytes()
        self._ensure_header_values()
        return self._header.get_bytes() + self._body.get_bytes()

    def load(self, obj):
        self._header.body_size = obj['header']['body_size']
        self._header.root_offset = obj['header']['root_offset']
        self._header.set_files(**obj['header']['files'])
        for k, v in obj['body'].items():
            offset = int(k)
            flavor = build_flavor(offset,
                                  v['type'],
                                  values1=v['values1'],
                                  values2=v['values2'])
            flavor.parents.extend(v['parents'])
            if isinstance(flavor, VertexFlavor):
                flavor.set_vtype(v['vtype'])
            self._body.flavors[offset] = flavor

    def dump(self):
        return {'header': self.header.dump(), 'body': self.body.dump()}

    @property
    def header(self):
        """

        :rtype: Header
        """
        return self._header

    @property
    def body(self):
        """

        :rtype: Body
        """
        return self._body

    @property
    def type(self):
        """

        :return: 'TRACK'|'CAR'|'OBJECT'
        :rtype: str
        """
        warnings.warn('', PendingDeprecationWarning)
        if self._body.get_flavors(12):
            return 'TRACK'
        elif self._body.get_flavors(16):
            return 'CAR'
        return 'OBJECT'

    def is_track(self):
        return self._body.is_track()
