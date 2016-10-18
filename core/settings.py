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

"""This module provides a set constants and settings used by various modules of
the TDF package.

Example
-------

    >>> from tdf.core.settings import TDF
    >>> print TDF.ORBIT_LENGTH
    3564

"""

import os
from tdf.core.toolbox import to_namedtuple
from tdf.extern import yaml
from tdf.core import binutils
from tdf import __version__ as TDF_VERSION

__all__ = [ 'TDF', '__doc__', '__version__', ]
__version__ = '$Revision$'

# uHAL constants.
UHAL_DATA_WIDTH = 32
UHAL_ADDR_WIDTH = 32

def getpath(name, default = None):
    """Returns absolute path if variable *name* is set, else None or absolute
    path of default if set."""
    value = os.getenv(name, default)
    return value and os.path.abspath(value)

class DataSpecification(object):
    """Container class for object and algorithm data specifications.

    Attribute *count* is the number of occurrences (eg. objects), attribute
    *width* the width in bits."""

    def __init__(self, count, width, coding = {}):
        self._count = count
        self._width = width
        self._coding = coding
        self._dwords = binutils.requires(width, UHAL_DATA_WIDTH)
        self._charcount = binutils.charcount(width)
        self._bitmask = binutils.bitmask(width)

    @property
    def count(self):
        """Returns the number of occurrences (eg. number objects)."""
        return self._count

    @property
    def width(self):
        """Returns data width in bits."""
        return self._width

    @property
    def dwords(self):
        """Returns data width in DWORDs (32 bits). Provided for convenience."""
        return self._dwords

    @property
    def bitmask(self):
        """Returns binary mask for data."""
        return self._bitmask

    @property
    def charcount(self):
        """Returns number of hex charachters required to express data."""
        return self._charcount

    def binstr(self, value):
        """Returns binary formatted string of attribute *value* with leading
        zeros according to data width."""
        return '{0:0{1}b}'.format(binutils.integer(value) & self.bitmask, self.width)

    def hexstr(self, value):
        """Returns hex formatted string of attribute *value* with leading zeros
        according to data width."""
        return '{0:0{1}x}'.format(binutils.integer(value) & self.bitmask, self.charcount)

    def decode(self, value):
        """Decode object value according to given bit slice mapping."""
        assert isinstance(value, int)
        if not self._coding:
            return {}
        data = dict([(k, (v.msb, v.lsb)) for k, v in self._coding._asdict().items()])
        return binutils.bitdecode(value, data)

class TDFCore:
    """Constants for TDF software."""

    VERSION = TDF_VERSION
    """Current framework release version."""

    EXIT_SUCCESS = 0
    """POSIX return value for successfull application execution."""

    EXIT_FAIL = 1
    """POSIX return value for failed application execution."""

    DATA_WIDTH = UHAL_DATA_WIDTH
    """Architecture data bus width in bits."""

    ADDR_WIDTH = UHAL_ADDR_WIDTH
    """Architecture address bus width in bits."""

    ROOT_DIR = getpath('TDF_ROOT', '/opt/tdf')
    """Absolute path to TDF root directory, used to access side files. If
    environment variable *TDF_ROOT* is not set it uses */opt/tdf*.
    """

    CONFIG_DIR = os.path.join(ROOT_DIR, 'etc', 'config')
    """Absolute path to TDF etc/config directory."""

    ROUTINES_DIR = os.path.join(ROOT_DIR, 'etc', 'routines')
    """Absolute path to TDF etc/routines directory."""

    SETTINGS_DIR = os.path.join(ROOT_DIR, 'etc', 'settings')
    """Absolute path to TDF etc/settings directory."""

    UNITTEST_DIR = os.path.join(ROOT_DIR, 'etc', 'unittest')
    """Absolute path to TDF etc/unittest directory."""

    L1MENU_DIR = getpath('TDF_L1MENU_DIR')
    """Absolute path to L1 menu directory. If environment variable
    *TDF_L1MENU_DIR* is not set it returns *None*."""

    MP7_ROOT_DIR = getpath('MP7_ROOT')
    """Absolute path to MP7 software root directory, used to execute mp7butler
    scripts.
    """

    def __init__(self): raise NotImplementedError()

class TDF(TDFCore):
    """Constants for TDF software."""

    # Ugly
    OBJECTS = to_namedtuple(yaml.load(open(os.path.join(TDFCore.SETTINGS_DIR, 'objects.yml')).read()))

    ORBIT_LENGTH = 3564
    """LHC orbit length in bunch crossings."""

    BX_SEC = 1 / 40000000.
    """BX time in seconds."""

    ORBIT_SEC = ORBIT_LENGTH * BX_SEC
    """Orbit time in seconds."""

    MUON = DataSpecification(**OBJECTS.muon._asdict())
    """Muon object specification."""

    EG = DataSpecification(**OBJECTS.eg._asdict())
    """e/gamma object specification."""

    #TAU = DataSpecification(**OBJECTS.tau._asdict())
    TAU = DataSpecification(12, 32)
    """Tau object specification."""

    JET = DataSpecification(**OBJECTS.jet._asdict())
    """Jet object specification."""

    ETT = DataSpecification(**OBJECTS.ett._asdict())
    """ETT specification."""

    HT = DataSpecification(**OBJECTS.ht._asdict())
    """HT specification."""

    ETM = DataSpecification(**OBJECTS.etm._asdict())
    """ETM specification."""

    HTM = DataSpecification(**OBJECTS.htm._asdict())
    """HTM specification."""

    ETMHF = DataSpecification(1, 32)
    """ETMHF specification."""

    HTMHF = DataSpecification(1, 32)
    """ETMHF specification."""

    LINK_11_FR_0 = DataSpecification(1, 32)
    LINK_11_FR_1 = DataSpecification(1, 32)
    LINK_11_FR_2 = DataSpecification(1, 32)
    LINK_11_FR_3 = DataSpecification(1, 32)
    LINK_11_FR_4 = DataSpecification(1, 32)
    LINK_11_FR_5 = DataSpecification(1, 32)
    """Link 9 spare frames specification."""

    EXTCOND = DataSpecification(1, 256)
    """External conditions specification."""

    ALGORITHM = DataSpecification(1, 512)
    """Algorithm data specification."""

    FINOR = DataSpecification(1, 1)
    """FINOR data specification."""

    MASKS = DataSpecification(1, 2, {'veto_mask': {'msb':1, 'lsb':1}, 'finor_mask': {'msb':0, 'lsb':0}, })
    """FINOR and veto data specification."""

    def __init__(self): raise NotImplementedError()
