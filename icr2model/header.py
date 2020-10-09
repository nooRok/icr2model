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

    def read(self, st):
        self.body_length, self.root_offset = unpack('2l', st.read(8))
        for ext, num_files in zip(EXT, unpack('3l', st.read(12))):
            names = (st.read(8) for _ in range(num_files))
            self.files[ext] = [n.strip(NULL).decode() for n in names]

    def to_bytes(self):
        files = [self.files[t] for t in EXT]
        b = (pack('2l', *(self.body_length, self.root_offset)) +
             pack('3l', *map(len, files)))
        for names in files:
            bnames = (n.encode().ljust(8, NULL) for n in names)
            b += b''.join(bnames)
        return b

    def set_files(self, **files):
        warn('Use .files', PendingDeprecationWarning)
        self.files.update(files)
