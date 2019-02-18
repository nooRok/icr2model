# coding: utf-8
__all__ = ['INT32_MAX', 'INT32_MIN',
           'is_int32', 'to_int32', 'to_degree', 'to_papy_degree']

INT32_MAX = (1 << 31)  #: 2147483648
INT32_MIN = ~(1 << 31)  #: -2147483649


def is_int32(value):
    """
    >>> is_int32(2147483648)
    False
    >>> is_int32(-2147483649)
    False
    >>> is_int32(2147483647)
    True
    >>> is_int32(-2147483648)
    True

    :param float value:
    :rtype: bool
    :return: INT32_MIN < value < INT32_MAX
    """
    return INT32_MIN < value < INT32_MAX


def to_int32(value):
    """
    http://eng-memo.hatenadiary.com/entry/2016/04/14/211401
    https://stackoverflow.com/questions/1604464/twos-complement-in-python

    >>> to_int32(2147483648)
    -2147483648
    >>> to_int32(2147483649)
    -2147483647
    >>> to_int32(4294967296)
    -2147483648
    >>> to_int32(-2147483649)
    2147483647
    >>> to_int32(-2147483650)
    2147483646
    >>> to_int32(-4294967297)
    2147483647

    :param int value:
    :return: overflowed value (-2147483649=2147483647, 2147483648=-2147483648)
    :rtype: int
    """
    if (value >= (1 << 32)) or (value <= ~(1 << 32)):
        return to_int32(value >> 1)
    return -(value & INT32_MAX) | (value & INT32_MAX - 1)


def to_degree(papy_degree):
    """
    for F15 rotation

    :param int papy_degree: -2147483649 < papy_degree < 2147483648
    :return: degree 0 ~ 360
    :rtype: float
    """
    return papy_degree / (INT32_MAX / 180.0)


def to_papy_degree(degree):
    """

    :param float degree: 0 ~ 360
    :return: papy_degree -2147483649 < degree < 2147483648
    :rtype: int
    """
    return to_int32(round(degree * (INT32_MAX / 180.0)))
