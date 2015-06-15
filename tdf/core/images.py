# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Bernhard Arnold <bernahrd.arnold@cern.ch>
#                     Johannes Wittmann <johannes.wittmann@cern.ch>
#
# Repository path   : $HeadURL: svn://heros.hephy.oeaw.ac.at/GlobalTriggerUpgrade/software/tdf/trunk/tdf/core/images.py $
# Last committed    : $Revision: 3782 $
# Last changed by   : $Author: arnold $
# Last changed date : $Date: 2015-02-24 19:02:44 +0100 (Tue, 24 Feb 2015) $
#

"""This module provides memory image classes."""

import sys

from filereader import FileReader
from testvector import TestVector
from settings import TDF
import binutils
import random

__all__ = [ 'GenericMemoryImage', 'ColumnMemoryImage',
            '__doc__', '__version__' ]
__version__ = '$Revision: 3782 $'

class GenericMemoryImage(object):
    """Abstract 32bit uHAL memory image provides data manipulation as well as
    serialization and deserilization functionality."""

    def __init__(self, size):
        """Attribute *size* the block size in DWORDs."""
        self.init(size)

    def init(self, size):
        """Initialize the image, create empty data block."""
        self._size = size
        self.clear()

    @property
    def size(self):
        return self._size

    @property
    def data(self):
        return self._data

    def clear(self, value = 0):
        """Clear image data block. Optional attribute *value* is the value the
        image is initialized."""
        self._data = [value] * self.size

    def fill_counter(self, reverse = False):
        """Fill data space with counter. The value represents the DWORDs address
        offset. Optional attribute *reverse* provides a decrementing counter
        ending with zero. Provided for debug purposes."""
        self._data = range(self.size)[::-1 if reverse else 1]

    def fill_random(self):
        """Fill data space with random values."""
        self._data = [random.randint(0, binutils.bitmask(TDF.DATA_WIDTH)) for _ in range(self.size)]

    def serialize(self):
        """Serialize memory image to DWORDs."""
        mask = binutils.bitmask(TDF.DATA_WIDTH)
        return [value & mask for value in self.data][:self.size]

    def deserialize(self, values):
        """Deserialize uHAL DWORDs to memory image. If size of *values* exceeds
        the memory size the additional values are omitted.
        """
        self.clear()
        mask = binutils.bitmask(TDF.DATA_WIDTH)
        for i, value in enumerate(values[:self.size]):
            self._data[i] = value & mask

    def read(self, fs):
        """Basic file reader for single column hex files."""
        reader = FileReader(fs, fields = (('values', 'x8'), ))
        values = reader.read()['values']
        self.deserialize(values)

    def compare(self, image, offset = 0, size = None, outfile = sys.stdout):
        assert isinstance(image, GenericMemoryImage), "can only compare two memory images of same type"
        if size is None:
            size = self.size
        if size > self.size:
            size = self.size
        data = self.data[offset:] + self.data[:offset]
        errors = []
        for i in range(self.size):
            if data[i] != image.data[i]:
                errors.append("Mismatch in line {0}:\n0x{1:08x}\n0x{2:08x}".format(i, data[i], image.data[i]))
        if len(errors):
            outfile.write("\n".join(errors))
            outfile.write("\n{0} mismatches found.\n".format(len(errors)))
            outfile.flush()
        else:
            outfile.write("No mismatches occurred.\n".format(len(errors)))
            outfile.flush()


    def __str__(self):
        return '\n'.join(['{0:08x}'.format(value) for value in self.data])

class ColumnMemoryImage(GenericMemoryImage):
    """Memory image using DWORD column based data mapping.

    Layout
    ======

        col 0    col 1    col 2    col 3
        00000000 00000004 00000008 0000000c
        00000001 00000005 00000009 0000000d
        00000002 00000006 0000000a 0000000e
        00000003 00000007 0000000b 0000000f

    """

    def __init__(self, size, blocksize):
        """Blocksize is the size of a single column. Number of columns
        mulitplied by blocksize is the memory size."""
        super(ColumnMemoryImage, self).__init__(size)
        self.blocksize = blocksize

    @property
    def columns(self):
        return self.size // self.blocksize

    def extract(self, column, count = 1):
        """Extract values spanning over multiple columns."""
        assert column + count - 1 < self.columns, "extract: invalid column slice"
        values = []
        for i in range(self.blocksize):
            step = self.blocksize
            begin = i + column * step
            end = begin + count * step
            values.append(binutils.bitjoin(self.data[begin:end:step], TDF.DATA_WIDTH))
        return values

    def inject(self, values, column, count = 1):
        """Inject values spanning over multiple columns."""
        # For number of values if values less/equal then blocksize.
        for i in range( min(len(values), self.blocksize) ):
            for ii, value in enumerate(binutils.bitsplit(values[i], count, TDF.DATA_WIDTH)):
                offset = (column + ii) * self.blocksize + i
                self._data[offset] = value

    def merged(self):
        """Return rows merged over all columns. Provided for convenience."""
        return self.extract(0, self.columns)

    def read(self, fs):
        """Basic file reader for multiple 32 bit colums hex files."""
        reader = FileReader(fs, fields = (('values', 'x8', self.columns), ))
        self.clear()
        for column, values in enumerate(reader.read()['values']):
            self.inject(values, column, 1)

    def __str__(self):
        lines = []
        fmtstr = '{{0:0{0}x}}'.format(binutils.charcount(TDF.DATA_WIDTH))
        for i in range(self.blocksize):
            line = []
            for value in self.data[i * self.columns:(i + 1) * self.columns]:
                line.append(fmtstr.format(value))
            lines.append(' '.join(line))
        return '\n'.join(lines)
