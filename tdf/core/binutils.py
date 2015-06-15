# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Bernhard Arnold <bernahrd.arnold@cern.ch>
#                     Johannes Wittmann <johannes.wittmann@cern.ch>
#
# Repository path   : $HeadURL: svn://heros.hephy.oeaw.ac.at/GlobalTriggerUpgrade/software/tdf/trunk/tdf/core/binutils.py $
# Last committed    : $Revision: 3790 $
# Last changed by   : $Author: arnold $
# Last changed date : $Date: 2015-02-26 12:37:22 +0100 (Thu, 26 Feb 2015) $
#

"""This module provides binary manipulation util classes and functions."""

import re
import uuid

__all__ = [ 'bitmask', 'charcount', 'requires', 'bitsplit', 'bitjoin',
    'hexencode', 'hexdecode', 'uuidencode', 'uuiddecode',
    'BitVector', 'BitStream', 'BitStreamReader', '__doc__', '__version__' ]
__version__ = '$Revision: 3790 $'

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

def bitsplit(value, n, width = 8):
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

def bitdecode(value, slices = {}):
    """Decodes value to bit slices.
    >>> bitdecode(0xdeadbeef, dict(foo=(15,0), bar=(31,16)'))
    {'bar': 0xdead, 'foo': 0xbeef, }
    """
    junks = {}
    for name, bs in slices.items():
        msb, lsb = bs if type(bs) in (tuple, list) else (bs, bs)
        junks[name] = (value & (bitmask(msb - lsb + 1) << lsb)) >> lsb
    return junks

def hexdecode(values, n = 32):
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

def hexencode(s, n = 32):
    """Converts a string to a list of values. Optional attribute *n* is the width
    of the values. A width of 32 bits can store 4 characters as a character
    always consumes 8 bits.
        >>> hexencode('viribus unitis')
        [1769105782, 544437602, 1953066613, 29545]
    """
    count = requires(len(s), requires(n, 8)) # calculate required number of values.
    return bitsplit(int(s[::-1].encode('hex'), 16), count, n)

def uuiddecode(values, n = 32):
    """Converts a list of values to an UUID4 string. Optional attribute *n* is
    the width of the values.
        >>> values = [1769105782, 544437602, 1953066613, 29545, ]
        >>> hexdecode(values)
        'viribus unitis'
    """
    assert len(values) == requires(128, n)
    uuid = "{0:0{1}x}".format(bitjoin(values, 32), charcount(128))
    return "{0}-{1}-{2}-{3}-{4}".format(uuid[0:8], uuid[8:12], uuid[12:16], uuid[16:20], uuid[20:33])

def uuidencode(uuid, n = 32):
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

class BitVector(object):
    """Simple bit vector implementation with bit slice extraction feature.

    Usage example
    -------------

    >>> vector = BitVector(0xdeadbeef)
    >>> hex(vector[31:16])
    0xdead
    >>> hex(vector[15:0])
    0xbeef
    >>> vector[0]
    1

    """
    def __init__(self, value = 0):
        """Attribute *value* must be an unsigned integer."""
        self.__value__ = value

    @property
    def value(self):
        """Returns the vectors integer value."""
        return self.__value__

    def __getitem__(self, index):
        """Access bit slices like [n:m] or [n]"""
        if isinstance(index, slice):
            n, m = index.start, index.stop
            if m >= n:
                raise ValueError("bit vector slices must be calles in format [n:m] or [n]")
            return (self.value >> m) & bitmask(n - m + 1)
        if isinstance(index, int):
            return (self.value >> index) & 1
        raise TypeError("bit vector indices must be integers, not {0}".format(type(index)))

class BitValue(BitVector):
    """Value container for de/serialization.

    Convenient serialization to map to memory layout and back from memory dump
    to actual values using bitsplit() and bitjoin() functions.

    TODO: to be merged with bit vector class.

    >>> v = BitValue(64, 0xdead0000beef0000)
    >>> v.serialize(16)
    [0x0000, 0xbeef, 0x0000, 0xdead]
    >>> v.deserialize([0xcafe, 0x0000], 16)
    >>> v
    0xcafe0000

    """
    def __init__(self, width, value = 0):
        super(BitValue, self).__init__()
        self.__width__ = width
        self.__itridx__ = 0 # iterator
        self.value = value # @value.setter
    @property
    def width(self):
        return self.__width__
    @property
    def value(self):
        """Returns the vectors integer value."""
        return self.__value__
    @value.setter
    def value(self, value):
        self.__value__ = value & bitmask(self.__width__)
    def __iter__(self):
        return self
    def next(self):
        if self.__itridx__ < self.__width__:
            self.__itridx__ += 1
            return self[self.__itridx__ - 1]
        raise StopIteration()
    def __int__(self):
        return self.__value__
    def __str__(self):
        chars = charcount(self.__width__)
        return '0x{self.__value__:0{chars}x}'.format(**locals())
    def __repr__(self):
        return self.__str__()
    def serialize(self, n = 32):
        """Attribute *n* is the bit width to split the content."""
        return bitsplit(self.__value__, self.__width__ // n, n)
    def deserialize(self, values, n = 32):
        """Attribute *n* is the bit width of teh value list."""
        self.value = bitjoin(values, n)

class BitStream(object):
    """Binary stream, reading from the right (lowest bit).

    Usage example
    -------------

    >>> stream = BitStream(int("0000cafe0000babe", 16))
    >>> hex(stream.read(16))
    '0xbabe'
    >>> stream.seek(32)
    >>> hex(stream.read(16))
    '0xcafe'


    >>> stream = BitStream(0xad)
    >>> [b for b in stream]
    [1, 0, 1, 1, 0, 1, 0, 1]

    """

    def __init__(self, data = 0):
        self._pos = 0
        self._size = 0
        self._data = 0

    def read(self, n = None):
        """Read *n* bits from stream and return them as integer value. If *n* is
        not specifed or None, all bits are returned as a single integer.
        """
        if n is None:
            return self.read(self._size - self._pos)
        if (self._pos + n) > self._size:
            return 0
        value = int((self._data >> self._pos) & bitmask(n))
        self._pos += n
        return value

    def seek(self, i):
        """Seek to stream position."""
        if i < 0: i = 0
        elif i > self._size: i = self._size
        self._pos = i

    @property
    def eof(self):
        """Returns True if end of stream is reached."""
        return self._pos >= self._size

    @property
    def pos(self):
        return self._pos

    def __len__(self):
        return self._size

    def __iter__(self):
        return self

    def next(self):
        if not self.eof:
            return self.read(1)
        raise StopIterator()

class BitStreamReader(BitStream):
    """

    Usage example
    -------------

    # sample.dat
    # 0000cafe
    # 0000babe
    # ee000000

    >>> stream = BitStreamReader(open("sample.dat"), 32)
    >>> stream.lineno
    1
    >>> hex(stream.read(16))
    '0xcafe'
    >>> stream.pos
    16
    >>> stream.skip() # ignore the remaining bits of line 1
    >>> stream.lineno
    2
    >>> stream.pos
    32
    >>> stream.read(16)
    '0xbabe'
    >>> stream.skip() # ignore the remaining bits of line 2
    >>> stream.lineno
    3
    >>> stream.seek(stream.pos + 24)
    >>> hex(stream.read(8))
    '0xee'

    """

    def __init__(self, file, width, base = 16):
        """Reads a bit stream from text file.

        Attribute *file* requires an iteratable object, *width* is the width in
        bits to read from each line, *base* is the integer base, default is 16
        (hex).
        """
        super(BitStreamReader, self).__init__()
        self._width = width
        self._base = base
        self.load(file)

    def load(self, file):
        """Load data from file. Attribute *file* requires be an interatable
        object.
        """
        self._pos = 0
        self._size = 0
        self._data = 0
        for i, line in enumerate(file):
            value = int(line, self._base) & bitmask(self._width)
            self._data |= value << (self._width * i)
            self._size += self._width

    @property
    def width(self):
        """Returns width in bits."""
        return self._width

    @property
    def lineno(self):
        """Returns line number of source file of current stream position."""
        return (self._pos-1) / self._width + 2

    def skip(self):
        """Seek to the begin next line."""
        self.read(self._width - (self._pos % self._width))
