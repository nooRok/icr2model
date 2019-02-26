# coding: utf-8
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

    :param float value:
    :return: overflowed value (-2147483649=0, 2147483648=0)
    :rtype: int
    """
    if is_int32(value):
        return int(value)
    return to_int32(value / 2)


def to_degree(papy_degree):
    """
    For F15 rotation

    :param int papy_degree: -2147483649 < papy_degree < 2147483648
    :return: degree 0 - 360
    :rtype: float
    """
    return papy_degree / (INT32_MAX / 180.0)


def to_papy_degree(degree, ndigits=1):
    """

    :param float degree: 0 ~ 360
    :param int ndigits: round
    :return: papy_degree -2147483649 < degree < 2147483648
    :rtype: int
    """
    return to_int32(round(degree, ndigits) * (INT32_MAX / 180.0))
