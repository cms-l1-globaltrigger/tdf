# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Bernhard Arnold <bernahrd.arnold@cern.ch>
#                     Johannes Wittmann <johannes.wittmann@cern.ch>
#
# Repository path   : $HeadURL: svn://heros.hephy.oeaw.ac.at/GlobalTriggerUpgrade/software/tdf/trunk/tdf/core/settings.py $
# Last committed    : $Revision: 3782 $
# Last changed by   : $Author: arnold $
# Last changed date : $Date: 2015-02-24 19:02:44 +0100 (Tue, 24 Feb 2015) $
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
from tdf.core.types import struct
from tdf.extern import yaml
from tdf.core import binutils
from tdf import __version__ as TDF_VERSION

__all__ = [ 'TDF', '__doc__', '__version__', ]
__version__ = '$Revision: 3782 $'

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
        data = dict([(k, (v.msb, v.lsb)) for k, v in self._coding.__dict__.items()])
        return binutils.bitdecode(value, data)

class TDFCORE:
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

# Ugly
OBJECTS = struct(**yaml.load(open(os.path.join(TDFCORE.SETTINGS_DIR, 'objects.yml')).read()))

class TDF(TDFCORE):
    """Constants for TDF software."""

    ORBIT_LENGTH = 3564
    """LHC orbit length in bunch crossings."""

    BX_SEC = 1 / 40000000.
    """BX time in seconds."""

    ORBIT_SEC = ORBIT_LENGTH * BX_SEC
    """Orbit time in seconds."""

    MUON = DataSpecification(**OBJECTS.muon.__dict__)
    """Muon object specification, returns an object of type :class:`DataSpecification`."""

    EG = DataSpecification(**OBJECTS.eg.__dict__)
    """e/gamma object specification, returns an object of type :class:`DataSpecification`."""

    TAU = DataSpecification(**OBJECTS.tau.__dict__)
    """Tau object specification, returns an object of type :class:`DataSpecification`."""

    JET = DataSpecification(**OBJECTS.jet.__dict__)
    """Jet object specification, returns an object of type :class:`DataSpecification`."""

    ETT = DataSpecification(**OBJECTS.ett.__dict__)
    """ETT specification, returns an object of type :class:`DataSpecification`."""

    HT = DataSpecification(**OBJECTS.ht.__dict__)
    """HT specification, returns an object of type :class:`DataSpecification`."""

    ETM = DataSpecification(**OBJECTS.etm.__dict__)
    """ETM specification, returns an object of type :class:`DataSpecification`."""

    HTM = DataSpecification(**OBJECTS.htm.__dict__)
    """HTM specification, returns an object of type :class:`DataSpecification`."""

    EXTCOND = DataSpecification(1, 256)
    """External conditions specification, returns an object of type :class:`DataSpecification`."""

    ALGORITHM = DataSpecification(1, 512)
    """Algorithm data specification, returns an object of type :class:`DataSpecification`."""

    FINOR = DataSpecification(1, 1)
    """FINOR data specification, returns an object of type :class:`DataSpecification`."""

    def __init__(self): raise NotImplementedError()
