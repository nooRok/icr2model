# coding: utf-8
import warnings

__all__ = ['Flag']

_TYPES = (b'\x00\x00\x00\x00', b'\x01\x00\x00\x80', b'\x02\x00\x00\x80',
          b'\x03\x00\x00\x80', b'\x04\x00\x00\x80', b'\x05\x00\x00\x80',
          b'\x06\x00\x00\x80', b'\x07\x00\x00\x80', b'\x08\x00\x00\x80',
          b'\t\x00\x00\x80', b'\n\x00\x00\x80', b'\x0b\x00\x00\x80',
          b'\x0c\x00\x00\x80', b'\r\x00\x00\x80', b'\x0e\x00\x00\x80',
          b'\x0f\x00\x00\x80', b'\x10\x00\x00\x80', b'\x11\x00\x00\x80',
          b'\x12\x00\x00\x80')


class Flag:
    def __init__(self, type_=None):
        """

        :param int type_:
        """
        self._type = type_  # type: int
        if isinstance(type_, bytes):  # for keeping compatibility
            self._type = _TYPES.index(type_)

    def read(self, stream):
        b = stream.read(4)  # type: bytes
        self._type = _TYPES.index(b)

    @property
    def i(self):
        """

        :return: flavor flag type (0-18)
        :rtype: int
        """
        if self._type is None:
            raise TypeError
        return self._type

    @property
    def b(self):
        """

        :return: flavor flag type bytes (``\\x00\\x00\\x00\\x00, \\x01\\x00\\x00\\x80 ... \\x12\\x00\\x00\\x80``)
        :rtype: bytes
        """
        return _TYPES[self.i]

    @classmethod
    def from_int(cls, idx):
        """
        *Pending Deprecation*

        :param int idx:
        :return: flag bytes hex (``\\x00\\x00\\x00\\x00, \\x01\\x00\\x00\\x80 ... \\x12\\x00\\x00\\x80``)
        :rtype: bytes
        """
        warnings.warn('use Flag()',
                      PendingDeprecationWarning)
        return cls(idx).b

    @classmethod
    def from_stream(cls, stream):
        f = cls()
        f.read(stream)
        return f

    @property
    def type(self):
        return self.i
