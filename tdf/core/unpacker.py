# -*- coding: utf-8 -*-
#
# Copyright 2013-2015 Bernhard Arnold <bernahrd.arnold@cern.ch>
#
# Repository path   : $HeadURL: svn://heros.hephy.oeaw.ac.at/GlobalTriggerUpgrade/software/tdf/trunk/tdf/core/unpacker.py $
# Last committed    : $Revision: 3751 $
# Last changed by   : $Author: arnold $
# Last changed date : $Date: 2015-02-13 15:13:07 +0100 (Fri, 13 Feb 2015) $
#

"""Base classes for custom readout record unpackers.
"""

from tdf.core.binutils import bitmask, charcount
import re, sys

__version__ = '$Revision: 3751 $'

TTY_WIDTH = 128
TTY_HR_CHAR = '-'

RECORD_EOL = '\n'
RECORD_WIDTH = 64

# -----------------------------------------------------------------------------
#  Record data class.
# -----------------------------------------------------------------------------

class RecordItem(object):
    """Container for a mapped value.

    Examples
    ========

    Defines a single bit item of name *data* on bit position 0.
    >>> item = RecordItem("data[0]")
    >>> item.bitwith
    1

    Defines a 8 bit item of name *data* starting from bit position 8.
    >>> item = RecordItem("data[15:8]")
    >>> item.bitwith
    8

    Defines a list of 4 bit items of same name *data*.
    >>> items = [
    ... RecordItem("data[1][7:4]"),
    ... RecordItem("data[0][3:0]"), ]
    """

    # Precompiled regular expression for item descriptor string. See class documentation for format description.
    _regex_pattern = re.compile(r'^(?P<name>[a-zA-Z_][0-9a-zA-Z_]*)(?:\[(?P<index>[0-9]+)\])?\[(?:(?P<msb>[0-9]+)\:)?(?P<lsb>[0-9]+)\]$')

    class ComparisonError(object):
        """Comparison error value container."""

        def __init__(self, item, reference, mask = None):
            self.item = item
            self.reference = reference
            self.mask = mask

        @property
        def _bitmask_info(self):
            if self.mask:
                note = "NOTE: applied bitmask"
                return "\n{note:<86} 0x{self.mask:>16x} {self.mask:>22d}".format(**locals())
            return ""

        @property
        def _missmatch_item(self):
            """Mismatch with another item."""
            return RECORD_EOL.join((
                "ERROR: mismatch `{self.item.name}' != `{self.reference.name}' (val != ref) at address 0x{self.item.line:04x}{self._bitmask_info}",
                str(self.item),
                str(self.reference),
            )).format(**locals())

        @property
        def _missmatch_value(self):
            """Mismatch with constant integer value."""
            required = "       required"
            return RECORD_EOL.join((
                "ERROR: mismatch `{self.item.name}' != required value (val != ref) at address 0x{self.item.line:04x}{self._bitmask_info}",
                str(self.item),
                "{required:<86} 0x{self.reference:>16x} {self.reference:>22d}",
            )).format(**locals())

        def __str__(self):
            if isinstance(self.reference, RecordItem):
                return self._missmatch_item
            return self._missmatch_value

    def __init__(self, code, line = 0, value = 0):
        """Attribute *code* is the items format descriptior. Optional attribute
        *line* is the line offset where the item is located in the record.
        Optional attribute *value* is the value assigned to the item. The
        assigned value is masked by the item's bit width.
        """
        m = self._regex_pattern.match(code)
        if not m:
            raise ValueError("RecordItem(): format mismatch of item descriptor: {code}".format(**locals()))
        params = m.groupdict()
        self.name = params['name']
        self.index = params['index'] if params['index'] is None else int(params['index'])
        self.lsb = int(params['lsb'])
        self.msb = self.lsb if params['msb'] is None else int(params['msb'])
        if not RECORD_WIDTH < self.msb <= self.lsb <= 0:
            ValueError("RecordItem(): msb/lsb out of range: [{self.msb}:{self.lsb}]".format(**locals()))
        # Set the item's initial value.
        self.line = line
        self.value = value

    @property
    def bitwidth(self):
        """Returns items width in bits."""
        return self.msb - self.lsb + 1

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value & bitmask(self.bitwidth)

    def compare(self, reference, mask = None):
        """Compare items value with another item or a constant value.

        Attribute *reference* can be an object of class RecordItem or a constant
        integer value.

        Returns an ComparisonError object if *reference* value does not match,
        else returns None on success.

        Examples
        ========

        >>> item = RecordItem("data:[42]")
        >>> ref = RecordItem("reference:[0]", value = 42)
        >>> item.compare(reference)
        <ComparisonError object>

        >>> RecordItem("data:[31:0]").compare(42)
        <RecordItem.ComparisonError object>
        """
        if isinstance(reference, RecordItem):
            if mask:
                if (self.value & mask) != (reference.value & mask):
                    return RecordItem.ComparisonError(self, reference, mask)
            if self.value != reference.value:
                return RecordItem.ComparisonError(self, reference)
        else:
            if mask:
                if (self.value & mask) != (reference & mask):
                    return RecordItem.ComparisonError(self, reference, mask)
            if self.value != reference:
                return RecordItem.ComparisonError(self, reference)

    def __str__(self):
        """Returns formatted string representation to be used as row of a record
        report listing (showing line, name, hex value, dec value).
        """
        pos = str(self.lsb) if self.bitwidth == 1 else "{self.msb}:{self.lsb}".format(**locals())
        index = "" if self.index is None else "[{self.index}]".format(**locals())
        name = "{self.name}{index}[{pos}]".format(**locals())
        return "0x{self.line:04x} {name:<79} 0x{self.value:>16x} {self.value:>22d}".format(**locals())

# -----------------------------------------------------------------------------
#  Item list class.
# -----------------------------------------------------------------------------

class ItemList(list):
    """Item list, able to join items to multi line record."""

    def join_value(self):
        """Join all values."""
        value = 0
        offset = 0
        for item in self:
            value |= item.value << offset
            offset += item.bitwidth
        return value

    def join_size(self):
        """Returns sum of bits of all items of this list."""
        return sum([item.bitwidth for item in self])

# -----------------------------------------------------------------------------
#  Record data class.
# -----------------------------------------------------------------------------

class RecordData(object):
    """Iterateable record data container."""

    def __init__(self):
        self._data = 0
        self._lines = 0
        self._pos = 0

    def append(self, value):
        self._data |= (value & bitmask(RECORD_WIDTH)) << (self.lines * RECORD_WIDTH)
        self._lines += 1

    def index(self, i):
        """Return value of record line with offset *i* (0..n). Raises an
        IndexError if *i* is out of bounds (*i* >= number of lines).
        """
        if i < self.lines:
            return (self._data >> (i * RECORD_WIDTH)) & bitmask(RECORD_WIDTH)
        raise IndexError("index(): record index out of range: {i}".format(**locals()))

    @property
    def lines(self):
        """Returns the record size in lines."""
        return self._lines

    @property
    def pos(self):
        """Returns the current line position. Incremented by reading using
        methods *next()* or *readline()*.
        """
        return self._pos

    @property
    def eor(self):
        """Returns True if end of record is reached using methods *next()* or
        *readline()* (read lines => max length of lines).
        """
        return self.pos + 1 >= self.lines

    def next(self):
        """Returns the next record line. Raises an StopIteration exception if
        end of record is reached.
        """
        if not self.eor:
            value = self.index(self.pos)
            self._pos += 1
            return value
        raise StopIteration

    def __iter__(self):
        return self

    def __str__(self):
        """Returns formatted string representation to be used as row of a record
        report listing (showing line, name, hex value, dec value).
        """
        return RECORD_EOL.join([
            "0x{offset:04x} {value:0{chars}x}".format(offset = i, value = self.index(i), chars = charcount(RECORD_WIDTH))
            for i in range(self.lines)])

# -----------------------------------------------------------------------------
#  Record file reader class.
# -----------------------------------------------------------------------------

class RecordFileReader(object):
    """Generic record file reader."""

    def __init__(self, file):
        self._file = file

    def read(self):
        record = RecordData()
        pattern = re.compile('^[0-9a-f]{{{chars}}}(?:(?:\r)?{eol})?$'.format(chars = charcount(RECORD_WIDTH), eol = RECORD_EOL))
        for i, line in enumerate(self._file):
            if not pattern.match(line):
                raise ValueError("read(): format mismatch in line {lineno}".format(lineno = i + 1))
            record.append(int(line, 16))
        return record

# -----------------------------------------------------------------------------
#  Record section class.
# -----------------------------------------------------------------------------

class RecordSection(object):
    """

    Examples
    ========

    Unpacking an items collects it internally but also creates an object
    attribute of same name.
    >>> section.unpack_line(0, "spam[31:0]")
    >>> section.spam
    <RecordItem object>
    >>> section.spam.value
    42

    Using list items the attribute returns the list of items.
    >>> section.unpack_line(0, "spam[0][3:0]", "spam[1][7:4]")
    >>> section.spam
    [<RecordItem object>, <RecordItem object>]

    Joining lists is as easy (assuming spam[0]=0xfe, spam[1]=0xca).
    >>> section.spam.join_size()
    8
    >>> hex(section.spam.join_value())
    0xcafe
    """

    def __init__(self, data, name = None):
        self.pos = data.pos
        self.data = data
        self.data_raw = []
        self.unpack_pos = 0
        self.name = name or "<unnamed>"
        self.items = []

    def unpack_line(self, *args):
        """Unpacks a record line."""
        if self.unpack_pos >= self.data.lines:
            IndexError("unpack_line(): no more line to unpack: {self.unpack_pos}".format(**locals()))

        value = self.data.next()
        self.data_raw.append(value)

        for arg in args:
            item = RecordItem(arg, self.unpack_pos + self.pos)

            if hasattr(self, item.name) and item.index is None:
                raise AttributeError("unpack_line(): attribute already exists: {arg}".format(**locals()))
            item.value = (value >> item.lsb) & bitmask(item.bitwidth)
            self.items.append(item)

            if item.index is None:
                setattr(self, item.name, item)
            else:
                setattr(self, item.name, ItemList(filter(lambda item_: item_.name == item.name, self.items)))

            # Sort by line number and descending LSB position.
            self.items.sort(key = lambda item: (item.line, item.index, -item.lsb))

        self.unpack_pos += 1

    def __str__(self):
        """Returns formatted string representation to be used as row of a record
        report listing (showing line, name, hex value, dec value).
        """
        buf = [" {self.name} {self.unpack_pos:d}x64-bit ".format(**locals()).center(TTY_WIDTH, TTY_HR_CHAR)]
        for item in self.items:
            buf.append(str(item))
        return RECORD_EOL.join(buf)
