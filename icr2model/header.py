# coding: utf-8
from struct import pack, unpack


class Header:
    """
    Header structure:
        * body size: 4 bytes; 3do file size - header size
        * root offset: 4 bytes; root flavor offset
        * numbers of files: 4 bytes * 3; mip, pmp, 3do
        * file names: 8 bytes * number of each types

        20 bytes + files * 8 bytes = header size

    .. attribute:: body_size

        :type: int

    .. attribute:: root_offset

        :type: int
    """
    _TYPES = ('mip', 'pmp', '3do')

    def __init__(self, body_size=0, root_offset=0, **files):
        """

        :param int body_size: file size without header
        :param int root_offset: root flavor offset
        :param dict[str, list[str]] files: key='mip'|'pmp'|'3do'
        """
        self.body_size = body_size
        self.root_offset = root_offset
        self._files = files

    def set_files(self, **files):
        """
        >>> h = Header()
        >>> h.set_files(mip=['mip1', 'mip2', 'mip3'])
        >>> h.set_files(**{'3do': ['3do1', '3do2', '3do3']})
        >>> h.files == {'mip': ['mip1', 'mip2', 'mip3'], '3do': ['3do1', '3do2', '3do3'], 'pmp': []}  # noqa
        True

        :param files: mip|pmp|3do=[filenames (w/o ext)] or \**dict[str,list[str]]
        """
        for type_, names in files.items():
            assert all(isinstance(n, str) for n in names)
            self._files[type_.lower()] = names

    def _read_body_info(self, data):
        """

        :param io.BytesIO|io.FileIO data:
        """
        self.body_size, self.root_offset = unpack('2l', data.read(8))

    def _read_files(self, data):
        """

        :param io.BytesIO|io.FileIO data:
        """
        counts = unpack('3l', data.read(12))
        for type_, count in zip(self._TYPES, counts):
            fmt, size = '8s' * count, 8 * count
            b_names = unpack(fmt, data.read(size))
            s_names = [n.strip(b'\x00').decode() for n in b_names]
            self.set_files(**{type_: s_names})

    def read(self, data):
        """

        :param io.BytesIO|io.FileIO data:
        """
        self._read_body_info(data)
        self._read_files(data)

    def get_bytes(self):
        """

        :rtype: bytes
        """
        buffer = bytearray()
        files = [self.files[t] for t in self._TYPES]
        buffer.extend(pack('2l', self.body_size, self.root_offset))
        buffer.extend(pack('3l', *map(len, files)))
        for names in files:
            [buffer.extend(pack('8s', n.encode())) for n in names]
        return bytes(buffer)

    def dump(self):
        return {'files': self.files,
                'body_size': self.body_size,
                'root_offset': self.root_offset}

    @property
    def header_size(self):
        """

        :rtype: int
        """
        fixes = sum([4, 4, 4 * 3])  # size, offset, file counts
        files = sum(map(len, self.files.values())) * 8
        return fixes + files

    @property
    def files(self):
        """

        :return:
            {'mip': ['mip1', 'mip2', 'mip3'],
            '3do': ['3do1', '3do2', '3do3'],
            'pmp': ['pmp1', 'pmp2', 'pmp3']}
        :rtype: dict[str, list[str]]
        """
        return {t: self._files.get(t, []) for t in self._TYPES}
