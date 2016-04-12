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

"""ExtCond specific memory images.
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

__version__ = '$Revision$'

# Blocksize of 32 bit simulation and spy memories.
MEMORY_BLOCKSIZE = 4096

class ExtCondMemoryImage(ColumnMemoryImage):
    """Memory for external conditions."""

    def __init__(self):
        super(ExtCondMemoryImage, self).__init__(MEMORY_BLOCKSIZE * 2, MEMORY_BLOCKSIZE)

    def extconds(self, offset = 0):
        """Return extconds as list. Offset rotates values by BX. Provided for convenience."""
        values = self.merged()[:TDF.ORBIT_LENGTH]
        return values[offset:] + values[:offset]

    def read(self, fs):
        """Read from simple dump file."""
        self.clear()
        reader = FileReader(fs, fields = (('extconds', 'x16'), ))
        self.inject(reader.read()['extconds'], 0, 2)

    def __str__(self):
        return '\n'.join(format(value, '016x') for value in self.extconds())

    def compare(self, image, offset = 0, size = TDF.ORBIT_LENGTH, outfile = sys.stdout):
        assert isinstance(image, ExtCondMemoryImage), "can only compare two memory images of same type"
        errors = []
        a = self.extconds(offset)
        b = image.extconds()
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
