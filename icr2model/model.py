# coding: utf-8
from io import BytesIO
from warnings import warn

from .body import Body
from .header import Header


class Model:
    def __init__(self, path=''):
        self.path = path
        self.header = Header()
        self.body = Body()

    def read(self):
        with open(self.path, 'rb') as f:
            self.header.read(f)
            st = BytesIO(f.read())
        self.body.read(st, self.header.root_offset)

    def sorted(self, optimize=True):
        """

        :param bool optimize: See description of param ``optimize`` of :meth:`icr2model.flavor.Flavors.sorted`
        :return: New model object
        :rtype: Model
        """
        new_m = Model()
        new_m.body.flavors = self.body.flavors.sorted(optimize)
        root_offset = max(new_m.body.flavors)
        new_m.header.root_offset = root_offset
        new_m.header.body_length = root_offset + new_m.body.flavors[root_offset].length
        new_m.header.files = self.header.files
        assert (sum(f.length for f in new_m.body.flavors.values()) ==
                root_offset + new_m.body.flavors[root_offset].length)
        return new_m

    def sort(self, optimize=True):
        """

        :param bool optimize: See description of param ``optimize`` of :meth:`icr2model.flavor.Flavors.sorted`
        :return:
        """
        new_m = self.sorted(optimize)
        self.header = new_m.header
        self.body = new_m.body

    def to_bytes(self):
        return self.header.to_bytes() + self.body.to_bytes()

    def is_track(self):
        return self.body.flavors.has_types(12, 17)

    @classmethod
    def open(cls, path):
        m = cls(path)
        m.read()
        return m

    def optimized(self):
        warn('Use .sorted()', DeprecationWarning)
        with self.body.flavors:
            pass
        return self.sorted(True)

    def get_bytes(self):
        warn('Use .to_bytes()', DeprecationWarning)
        return self.to_bytes()
