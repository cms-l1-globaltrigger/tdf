# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Bernhard Arnold <bernahrd.arnold@cern.ch>
#                     Johannes Wittmann <johannes.wittmann@cern.ch>
#
# Repository path   : $HeadURL: https://svn.cern.ch/reps/cactus/trunk/cactusprojects/ugt/tdf/tdf/finor/images.py $
# Last committed    : $Revision: 44462 $
# Last changed by   : $Author: arnold $
# Last changed date : $Date: 2016-04-12 15:32:19 +0200 (Die, 12 Apr 2016) $
#

"""FinOR specific memory images.
"""

from tdf.core import TDF
from tdf.core.filereader import FileReader
from tdf.core.testvector import TestVector
from tdf.core.images import (
    ColumnMemoryImage,
)
from tdf.core.binutils import (
    bitmask,
    charcount,
    bitjoin,
    bitsplit,
)
import json
import sys

__version__ = '$Revision: 44462 $'

# Blocksize of 32 bit simulation and spy memories.
MEMORY_BLOCKSIZE = 4096

class FinORMemoryImage(ColumnMemoryImage):
    """Memory for the final OR boards."""

    def __init__(self):
        super(FinORMemoryImage, self).__init__(MEMORY_BLOCKSIZE, MEMORY_BLOCKSIZE)

    def finor(self, offset = 0):
        """Return finors as list. Offset rotates values by BX. Provided for convenience."""
        values = self.merged()[:TDF.ORBIT_LENGTH]
        return values[offset:] + values[:offset]

    def read(self, fs):
        """Read from simple dump file."""
        self.clear()
        reader = FileReader(fs, fields = (('finor', 'x16'), ))
        self.inject(reader.read()['finor'], 0, 1)

    def __str__(self):
        return '\n'.join(format(value, '08x') for value in self.finor())

    def compare(self, image, offset = 0, size = TDF.ORBIT_LENGTH, outfile = sys.stdout):
        assert isinstance(image, FinORMemoryImage), "can only compare two memory images of same type"
        errors = []
        a = self.finor(offset)
        b = image.finor()
        for bx in range(size):
            value_a = a[bx]
            value_b = b[bx]
            if value_a != value_b:
                errors.append("Data missmatch in BX {bx} with offset {offset}\ntarget: 0x{value_a:016x}\nsource: 0x{value_b:016x}".format(**locals()))
        if errors:
            errors.append("Found {0} data mismatches by comparing a range of {1} BX with offset {2}".format(len(errors), size, offset))
            outfile.write("\n".join(errors))
            outfile.write("\n")
        else:
            outfile.write("Success. No external condition data errors.\n")
        outfile.flush()
        return len(errors)
