# coding: utf-8
from struct import unpack, pack
from warnings import warn

EXT = ('mip', 'pmp', '3do')
NULL = b'\x00'


class Header:
    def __init__(self, body_length=0, root_offset=0, **files):
        self.body_length = body_length
        self.root_offset = root_offset
        self.files = files or {'mip': [], 'pmp': [], '3do': []}

    def read(self, stream):
        self.body_length, self.root_offset = unpack('2l', stream.read(8))
        for ext, num_files in zip(EXT, unpack('3l', stream.read(12))):
            names = (stream.read(8) for _ in range(num_files))
            self.files[ext] = [n.strip(NULL).decode() for n in names]

    def to_bytes(self):
        files = [self.files[t] for t in EXT]
        b = (pack('2l', *(self.body_length, self.root_offset)) +
             pack('3l', *map(len, files)))
        for names in files:
            for name in names:
                if len(name) > 8:
                    warn('Long filename {} is renamed to {}'.format(name, name[:8]))
                b += name[:8].encode().ljust(8, NULL)
        return b

    def set_files(self, **files):
        warn('Use .files', DeprecationWarning)
        self.files.update(files)
