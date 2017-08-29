# -*- coding: utf-8 -*-
#
# Copyright 2013-2017 Bernhard Arnold <bernahrd.arnold@cern.ch>
#                     Johannes Wittmann <johannes.wittmann@cern.ch>
#
# Repository path   : $HeadURL: $
# Last committed    : $Revision: $
# Last changed by   : $Author: $
# Last changed date : $Date: $
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

__version__ = '$Revision: $'

# Blocksize of 32 bit simulation and spy memories.
MEMORY_BLOCKSIZE = 4096

class Finor502MemoryImage(ColumnMemoryImage):
    """Memory for the final OR boards.

    Layout  31             16 15     8 7      0
            |               | |      | |      |
           [........|.......T|..VVVVVV|..FFFFFF]
           T = finor2tcds (1 bit)
           V = veto (6 bits)
           F = finor (6 bits)

    """

    Inputs = 6

    def __init__(self):
        super(Finor502MemoryImage, self).__init__(MEMORY_BLOCKSIZE, MEMORY_BLOCKSIZE)

    def finors(self, offset=0):
        """Return FinORs as list. Offset rotates values by BX. Provided for convenience."""
        values = self.merged()[:TDF.ORBIT_LENGTH]
        # Mask FinOR bits
        mask = bitmask(self.Inputs) # lower 8 bits
        values = [(value >> 0) & mask for value in values]
        return values[offset:] + values[:offset]

    def vetos(self, offset=0):
        """Return vetos as list. Offset rotates values by BX. Provided for convenience."""
        values = self.merged()[:TDF.ORBIT_LENGTH]
        # Mask veto bits
        mask = bitmask(self.Inputs) # upper 8 bits
        values = [(value >> 8) & mask for value in values]
        return values[offset:] + values[:offset]

    def finors2tcds(self, offset=0):
        """Return merged FinORs to TCDS as list. Offset rotates values by BX. Provided for convenience."""
        values = self.merged()[:TDF.ORBIT_LENGTH]
        # Mask FinOR2TCDS bit
        mask = 0x1 # bit #16
        values = [(value >> 16) & mask for value in values]
        return values[offset:] + values[:offset]

    def __str__(self):
        finors = self.finors()
        vetos = self.vetos()
        finors2tcds = self.finors2tcds()
        return '\n'.join("{:01x} {:04x} {:04x}".format(finors2tcds[i], vetos[i], finors[i]) for i in range(len(finors)))

    def compare(self, image, offset = 0, size = TDF.ORBIT_LENGTH, outfile = sys.stdout):
        assert isinstance(image, Finor502MemoryImage), "can only compare two memory images of same type"
        errors = []
        a = self.finors(offset)
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
            outfile.write("Success. No FinOR/veto data errors.\n")
        outfile.flush()
        return len(errors)
