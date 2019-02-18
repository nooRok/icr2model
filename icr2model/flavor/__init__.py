# coding: utf-8
from collections import Iterable

from .flag import Flag
from .flavor import *

__all__ = ['build_flavor',
           'Flag',
           'Flavor',
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

_TYPES = (F00,  # \x00\x00\x00\x00 F00, V01, V02
          F01,  # \x01\x00\x00\x80
          F02,  # \x02\x00\x00\x80
          None,  # F03
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
          F18  # \x12\x00\x00\x80
          )


def build_flavor(offset, type_, parent=None, values1=None, values2=None,
                 **attrs):
    """

    :param int offset:
    :param int type_:
    :param int|Iterable[int] parent:
    :param Iterable[int] values1:
    :param Iterable[int] values2:
    :param attrs: for future use
    :return:
    :rtype: Flavor
    """
    if type_ == 3:
        raise NotImplementedError
    f = _TYPES[type_](offset)  # type: Flavor
    if isinstance(parent, int):
        f.parents.append(parent)
    elif isinstance(parent, Iterable):
        f.parents.extend(parent)
    if values1:
        f.values1.extend(values1)
    if values2:
        f.values2.extend(values2)
    return f
