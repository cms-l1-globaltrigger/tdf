# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Bernhard Arnold <bernahrd.arnold@cern.ch>
#                     Johannes Wittmann <johannes.wittmann@cern.ch>
#
# Repository path   : $HeadURL: svn://heros.hephy.oeaw.ac.at/GlobalTriggerUpgrade/software/tdf/trunk/tdf/extcond/images.py $
# Last committed    : $Revision: 3820 $
# Last changed by   : $Author: arnold $
# Last changed date : $Date: 2015-04-15 11:45:58 +0200 (Wed, 15 Apr 2015) $
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

__version__ = '$Revision: 3820 $'

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
