# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Bernhard Arnold <bernahrd.arnold@cern.ch>
#                     Johannes Wittmann <johannes.wittmann@cern.ch>
#
# Repository path   : $HeadURL$
# Last committed    : $Revision$
# Last changed by   : $Author$
# Last changed date : $Date$
#

"""This module provides binary manipulation util classes and functions."""

import re
import uuid

__all__ = [ 'bitmask', 'charcount', 'requires', 'bitsplit', 'bitjoin',
    'hexencode', 'hexdecode', 'uuidencode', 'uuiddecode',
    'BitVector', 'BitStream', 'BitStreamReader', '__doc__', '__version__' ]
__version__ = '$Revision$'

def bitmask(n):
    """Calculates bitmask for *n* bits.

    Useful for masking a continous range of bits.

    Usage example
    -------------

    >>> mask = bitmask(8)
    >>> hex(mask)
    0xff
    >>> hex(0xdeadbeef & bitmask(4))
    0xbeef
    """
    return (1 << n) - 1

def charcount(n):
    """Returns number of hex characters (nibbles) required to represent *n* bits.

    Usage example
    -------------

    >>> charcount(32)
    8 # 32 bit requires 8 nibbles
    """
    return n // 4 + bool(n % 4)

def requires(n, width):
    """Returns required junks of *width* for value with width *n* bits.
    Represents an integer division always rounding up.
    >>> requires(32, 8)
    4
    """
    return n // width + bool(n % width)

def bitsplit(value, n, width=8):
    """Split a value from left to right into *n* values of *width* bits in size.
    >>> bitsplit(0xaabbccdd, 4, 8)
    [0xdd, 0xcc, 0xbb, 0xaa]
    >>> bitsplit(0xaabbccdd, 2, 16)
    [0xccdd, 0xaabb]
    """
    mask = bitmask(width)
    return [((value >> (i * width)) & mask) for i in range(n)]

def bitjoin(values, width):
    """High performance bit join function.
    Joins a list of values left to right to a single value.
    >>> values = [0xdd, 0xcc, 0xbb, 0xaa]
    >>> bitjoin(values, 8)
    0xaabbccdd
    """
    mask = bitmask(width)
    result = 0
    i = 0
    for value in values:
        result |= ((value & mask) << (i * width))
        i += 1
    return result

def bitdecode(value, slices={}):
    """Decodes value to bit slices.
    >>> bitdecode(0xdeadbeef, dict(foo=(15,0), bar=(31,16)'))
    {'bar': 0xdead, 'foo': 0xbeef, }
    """
    junks = {}
    for name, bs in slices.items():
        msb, lsb = bs if type(bs) in (tuple, list) else (bs, bs)
        junks[name] = (value & (bitmask(msb - lsb + 1) << lsb)) >> lsb
    return junks

def hexdecode(values, n=32):
    """Converts a list of values to a string. Optional attribute *n* is the
    width of the values.
        >>> values = [1769105782, 544437602, 1953066613, 29545, ]
        >>> hexdecode(values)
        'viribus unitis'
    """
    chars = []
    for value in values:
        chars.extend([chr(c) for c in bitsplit(value, charcount(n), 8) if c])
    return ''.join(chars)

def hexencode(s, n=32):
    """Converts a string to a list of values. Optional attribute *n* is the width
    of the values. A width of 32 bits can store 4 characters as a character
    always consumes 8 bits.
        >>> hexencode('viribus unitis')
        [1769105782, 544437602, 1953066613, 29545]
    """
    count = requires(len(s), requires(n, 8)) # calculate required number of values.
    return bitsplit(int(s[::-1].encode('hex'), 16), count, n)

def uuiddecode(values, n=32):
    """Converts a list of values to an UUID4 string. Optional attribute *n* is
    the width of the values.
        >>> values = [1769105782, 544437602, 1953066613, 29545, ]
        >>> hexdecode(values)
        'viribus unitis'
    """
    assert len(values) == requires(128, n)
    uuid = "{0:0{1}x}".format(bitjoin(values, 32), charcount(128))
    return "{0}-{1}-{2}-{3}-{4}".format(uuid[0:8], uuid[8:12], uuid[12:16], uuid[16:20], uuid[20:33])

def uuidencode(uuid, n=32):
    """Converts an UUID string to a list of values. Optional attribute *n* is the width
    of the values. A width of 32 bits can store 4 characters as a character
    always consumes 8 bits.
        >>> uuidencode('c715a069-7538-49dd-858a-f6f058a38a90')
        [892417891, ...]
    """
    uuid = str(uuid) # Cast UUID object to string.
    assert re.match('^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', uuid), "uuidencode() requires an UUID4 format string"
    raw = uuid.replace('-', '') # Remove dashes.
    return bitsplit(int(raw, 16), requires(128, n), n)

def integer(value):
    """Universal type cast of base encoded string represenataions and other
    integer compatible types. Returns an unsigned integer value.
    """
    if isinstance(value, str):
        if value.strip().startswith('0b'):
            return int(value, 2)
        elif value.strip().startswith('0o'):
            return int(value, 8)
        elif value.strip().startswith('0x'):
            return int(value, 16)
        else:
            return int(value, 10)
    return int(value)

class BitField(object):
    """Bit field representing a fixed sized integer."""
    def __init__(self, width, value=None):
        """Initialize bit field of *width* and optionaly initialize value."""
        self.resize(width, (integer(value) or 0) & self.bitmask)
    def set(self, value):
        """Initialize bit field with value, will be masked by bit fields width."""
        self.__value = integer(value) & self.bitmask
    def resize(self, width, value=None):
        """Resize the bit fields width. This will cut off bits if reduced in width."""
        self.__width = width
        self.set(int(self) if value is None else integer(value))
    def bitsplit(self, width):
        """Split bit field into multiple junks of *width*."""
        return [BitField(width, value) for value in bitsplit(int(self), requires(self.width, width), width)]
    # Integer operator implementations:
    def __iadd__(a, b):
        a.set(int(a) + int(b))
        return a
    def __radd__(a, b):
        return BitField(a.width, int(b) + int(a))
    def __add__(a, b):
        return BitField(a.width, int(a) + int(b))
    def __isub__(a, b):
        a.set(int(a) - int(b))
        return a
    def __rsub__(a, b):
        return BitField(a.width, int(b) - int(a))
    def __sub__(a, b):
        return BitField(a.width, int(a) - int(b))
    def __imul__(a, b):
        a.set(int(a) * int(b))
        return a
    def __rmul__(a, b):
        return BitField(a.width, int(b) * int(a))
    def __mul__(a, b):
        return BitField(a.width, int(a) * int(b))
    def __idiv__(a, b):
        a.set(int(a) // int(b))
        return a
    def __rdiv__(a, b):
        return BitField(a.width, int(b) // int(a))
    def __div__(a, b):
        return BitField(a.width, int(a) // int(b))
    def __lshift__(a, b):
        return BitField(a.width, int(a) << int(b))
    def __rshift__(a, b):
        return BitField(a.width, int(a) >> int(b))
    def __invert__(a):
        return BitField(a.width, ~int(a))
    def __iand__(a, b):
        a.set(int(a) & int(b))
        return a
    def __and__(a, b):
        return BitField(a.width, int(a) & int(b))
    def __ior__(a, b):
        a.set(int(a) | int(b))
        return a
    def __or__(a, b):
        return BitField(a.width, int(a) | int(b))
    def __ixor__(a, b):
        a.set(int(a) ^ int(b))
        return a
    def __xor__(a, b):
        return BitField(a.width, int(a) ^ int(b))
    def __lt__(a, b):
        return int(a) < int(b)
    def __gt__(a, b):
        return int(a) > int(b)
    def __le__(a, b):
        return int(a) <= int(b)
    def __ge__(a, b):
        return int(a) >= int(b)
    def __eq__(a, b):
        return int(a) == int(b)
    def __ne__(a, b):
        return int(a) != int(b)
    def __len__(self):
        """Width of the bit field."""
        return self.width
    def __int__(self):
        """Converts the bit field into a imutable integer."""
        return self.__value & self.bitmask
    def __iter__(self):
        """Returns iterator over bits of the bit field."""
        value = int(self)
        return iter([((value >> i) & 1) for i in range(self.width)])
    def __str__(self):
        return ''.join(('0x', self.hex))
    def __repr__(self):
        return ''.join(('0x', self.hex))
    def __getitem__(self, index):
        """Get bit slice of the bit field. Returns a bit filed."""
        if isinstance(index, slice):
            m, n = index.start, index.stop + 1
            width = n - m
            return BitField(width, (int(self) >> m) & bitmask(width))
        return BitField(1, int(self) & (1 << index))
    def __setitem__(self, index, value):
        """Set bit slice of the bit field."""
        if isinstance(index, slice):
            m, n = index.start, index.stop + 1
        else:
            m, n = index, index + 1
        width = n - m
        mask = bitmask(width)
        value = value & mask
        self.__value &= ~(mask << m)
        self.__value |= value << m
    @property
    def dec(self):
        """Decimal string representation of the bit field."""
        return "{value:d}".format(value=int(self))
    @property
    def bin(self):
        """Binary string representation of the bit field."""
        return "{value:0{chars}b}".format(value=int(self), chars=self.width)
    @property
    def hex(self):
        """Hex string representation of the bit field."""
        return "{value:0{chars}x}".format(value=int(self), chars=self.charcount)
    @property
    def width(self):
        """Width of the bit field."""
        return self.__width
    @property
    def bitmask(self):
        """Bit mask representing the width of the bit field."""
        return bitmask(self.width)
    @property
    def charcount(self):
        """Number of hex characters reqired to represent bit field."""
        return charcount(self.width)
