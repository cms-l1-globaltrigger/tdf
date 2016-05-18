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

"""This module provides a test vector reader class for Global Trigger input data
provided by the emulator.

A test vector file is a whitespace separated CSV file with an optional header
line. The first column is a zero padded 4 characters width decimal value with a
valid range from 0 to 3563. The following columns represent various input object
data of different bit widths. All input object data are zero padded hex values
of 8, 16, 64 or 128 characters width. The last column is assigned to the FINOR
as a single bit value. All hex characters (a-f) expected in lower case.

=========  ========  ==================================
Column(s)  Format    Description
=========  ========  ==================================
1          i4        BX index (dec 0-3563)
2 - 9      x16 * 8   8 muons, each 64 bit (hex)
10 - 21    x8 * 12   12 e/gs, each 32 bit (hex)
22 - 29    x8 * 8    8 tau, each 32 bit (hex)
30 - 41    x8 * 12   12 jet, each 32 bit (hex)
42         x8        ett, 32 bit (hex)
43         x8        ht, 32 bit (hex)
44         x8        etm, 32 bit (hex)
45         x8        htm, 32 bit (hex)
46         x64       external conditions, 256 bit (hex)
47         x128      algorithms, 512 bit (hex)
48         b1        FINOR, 1 bit (bin)
=========  ========  ==================================

Header format specification
---------------------------

A simplified YAML syntax is used to store header information. Each line is
prefixed with an | (pipe) character.

  |name: TestVector_Sample
  |description: A simple sample test vector.
  |datetime: 2014-04-04T18:14:00
  |events: 3564
  |menu_name: L1Menu_Sample
  |menu_uuid: d71af861-abaf-4ced-997c-3dfcba3fdcb6

Masking algorithms
------------------

To mask a range of algorithms required at usign multiple modules.

>>> tv = TestVector(fp)
>>> tv.maskAlgorithms([0, 1, 2, 3, 4, 5, 6, 7, 42])
>>> tv.serialize()

"""

import sys
from filereader import FileReader
from binutils import charcount, bitsplit, bitjoin
from settings import TDF

__all__ = [ 'TestVector', 'TestVectorReader', '__doc__', '__version__' ]
__version__ = '$Revision$'

class TestVector(object):
    """
    Supported header informations are *name*, *description*, *datetime* (ISO
    timestamp), *events* (integer), *menu_name*, *menu_uuid (UUID4 format).
    """

    MetaDataItems = ('name', 'description', 'datetime', 'events', 'menu_name', 'menu_uuid', )
    MetaDataStartChar = '|'
    YamlSeparator = ':'

    def __init__(self, fs = None):
        self.reset()
        if isinstance(fs, str):
            self.read(open(fs, 'rb'))
        elif isinstance(fs, file):
            self.read(fs)

    def reset(self):
        def mklist(): return [0 for _ in range(TDF.ORBIT_LENGTH)]
        self.name = None
        self.description = None
        self.datetime = None
        self.events = None
        self.menu_name = None
        self.menu_uuid = None
        # Initialize the object data containers.
        self._muon = [mklist() for _ in range(TDF.MUON.count)]
        self._eg  = [mklist() for _ in range(TDF.EG.count)]
        self._tau = [mklist() for _ in range(TDF.TAU.count)]
        self._jet = [mklist() for _ in range(TDF.JET.count)]
        self._ett = mklist()
        self._ht  = mklist()
        self._etm = mklist()
        self._htm = mklist()
        self._extcond = mklist()
        self._algorithms = mklist()
        self._finor = mklist()

    def read(self, fp):
        self.reset()
        self.readMetaData(fp)
        # Read file line by line.
        for row in TestVectorReader(fp):
            for i, muon in enumerate(row['muon']):
                self._muon[i].append(muon)
            for i, eg in enumerate(row['eg']):
                self._eg[i].append(eg)
            for i, tau in enumerate(row['tau']):
                self._tau[i].append(tau)
            for i, jet in enumerate(row['jet']):
                self._jet[i].append(jet)
            self._ett.append(row['ett'])
            self._ht.append(row['ht'])
            self._etm.append(row['etm'])
            self._htm.append(row['htm'])
            self._extcond.append(row['ext_con'])
            self._algorithms.append(row['algorithm'])
            self._finor.append(row['finor'])

    def readMetaData(self, fp):
        """Read metadata from file header.
        Example format:
          |name: TestVector_3kTTbar
          |description: sample TTbar pattern.
          |datetime: 2014-09-03T13:19:21
          |events: 3000
          |menu_name: L1Menu_Sample
          |menu_uuid: 98c404c2-747e-40ec-9255-39bc3018a84b
        """
        # Store the current file position.
        pos = fp.tell()
        # Collect comments (lines starting with `|').
        comments = []
        line = fp.readline()
        while line.startswith(self.MetaDataStartChar):
            comments.append(line.lstrip(self.MetaDataStartChar).rstrip())
            line = fp.readline()
        # Restore the previous file position.
        fp.seek(pos)
        # Pick out the metadata values.
        for comment in comments:
            meta = comment.split(self.YamlSeparator)
            if len(meta) == 2:
                key, value = meta[0].strip(), meta[1].strip()
                if key in self.MetaDataItems:
                    setattr(self, key, value)

    def updateFinor(self):
        """Update FinOR according to the active algorithm bits."""
        for bx in range(len(self)):
            self._finor[bx] = int(bool(self._algorithms[bx]))

    def maskAlgorithms(self, mask):
        """Mask out algorithms that are not in argument *mask* and calculates
        FinOR according to the updated algoritms.
        """
        # Calcualte bit mask
        mask = bitjoin([1 if index in mask else 0 for index in range(TDF.ALGORITHM.width)], 1)
        for bx in range(len(self)):
            self._algorithms[bx] &= mask
        # Update the FinOR
        self.updateFinor()

    def muon(self, i):
        assert 0 <= i < TDF.MUON.count, "invalid muon index"
        return self._muon[i]

    def muons(self):
        """Retruns a list of all muon objects data. Provided for convenience."""
        return self._muon

    def eg(self, i):
        assert 0 <= i < TDF.EG.count, "invalid e/g index"
        return self._eg[i]

    def egs(self):
        """Retruns a list of all e/g objects data. Provided for convenience."""
        return self._eg

    def tau(self, i):
        assert 0 <= i < TDF.TAU.count, "invalid tau index"
        return self._tau[i]

    def taus(self):
        """Retruns a list of all Tau objects data. Provided for convenience."""
        return self._tau

    def jet(self, i):
        assert 0 <= i < TDF.JET.count, "invalid jet index"
        return self._jet[i]

    def jets(self):
        """Retruns a list of all jet objects data. Provided for convenience."""
        return self._jet

    def ett(self):
        return self._ett

    def ht(self):
        return self._ht

    def etm(self):
        return self._etm

    def htm(self):
        return self._htm

    def extconds(self):
        return self._extcond

    def algorithms(self):
        return self._algorithms

    def finor(self):
        return self._finor

    def serialize(self):
        """Serialize the test vector to string."""
        rows = []
        for i in range(len(self)):
            cols = []
            cols.append('{i:04d}'.format(i=i))
            cols.extend(TDF.MUON.hexstr(values[i]) for values in self.muons())
            cols.extend(TDF.EG.hexstr(values[i]) for values in self.egs())
            cols.extend(TDF.TAU.hexstr(values[i]) for values in self.taus())
            cols.extend(TDF.JET.hexstr(values[i]) for values in self.jets())
            cols.append(TDF.ETT.hexstr(self.ett()[i]))
            cols.append(TDF.HT.hexstr(self.ht()[i]))
            cols.append(TDF.ETM.hexstr(self.etm()[i]))
            cols.append(TDF.HTM.hexstr(self.htm()[i]))
            cols.append(TDF.EXTCOND.hexstr(self.extconds()[i]))
            cols.append(TDF.ALGORITHM.hexstr(self.algorithms()[i]))
            cols.append(TDF.FINOR.hexstr(self.finor()[i]))
            rows.append(' '.join(cols))
        return '\n'.join(rows)

    def __len__(self):
        return len(self.finor())

    def __str__(self):
        return self.serialize()

class TestVectorReader(FileReader):
    """Global trigger test vector file reader. It derives from class FileReader.

    Usage example
    -------------

    Creating a simulation memory image.

    >>> reader = TestVectorReader("sample.txt")

    """

    FIELDS = (
        ('bx', 'd4'),
        ('muon', 'x{0}'.format(charcount(TDF.MUON.width)), TDF.MUON.count),
        ('eg',  'x{0}'.format(charcount(TDF.EG.width)), TDF.EG.count),
        ('tau', 'x{0}'.format(charcount(TDF.TAU.width)), TDF.TAU.count),
        ('jet', 'x{0}'.format(charcount(TDF.JET.width)), TDF.JET.count),
        ('ett', 'x{0}'.format(charcount(TDF.ETT.width))),
        ('ht',  'x{0}'.format(charcount(TDF.HT.width))),
        ('etm', 'x{0}'.format(charcount(TDF.ETM.width))),
        ('htm', 'x{0}'.format(charcount(TDF.HTM.width))),
        ('ext_con', 'x{0}'.format(charcount(TDF.EXTCOND.width))),
        ('algorithm', 'x{0}'.format(charcount(TDF.ALGORITHM.width))),
        ('finor', 'b1'),
    )
    """Format for columns of test vector file. Refer to class FileReader for detailed docmatation."""

    OBJECT_NAMES = ('muon', 'eg', 'tau', 'jet', 'ett', 'ht', 'etm', 'htm', 'ext_con')
    """Object names in order."""

    def __init__(self, fp):
        super(TestVectorReader, self).__init__(fp, fields = self.FIELDS)

class SimSpyDump(object):
    """
    """

    def __init__(self, f = None):
        self.reset()
        if isinstance(f, str):
            self.read(open(f, 'rb'))
        elif isinstance(f, file):
            self.read(f)

    def reset(self):
        # Initialize the object data containers.
        self._muon = [[] for _ in range(TDF.MUON.count)]
        self._eg  = [[] for _ in range(TDF.EG.count)]
        self._tau = [[] for _ in range(TDF.TAU.count)]
        self._jet = [[] for _ in range(TDF.JET.count)]
        self._ett = []
        self._ht  = []
        self._etm = []
        self._htm = []
        self._extcond = []

    def read(self, fp):
        self.reset()
        # Read file line by line.
        for row in TestVectorReader(fp):
            for i, muon in enumerate(row['muon']):
                self._muon[i].append(muon)
            for i, eg in enumerate(row['eg']):
                self._eg[i].append(eg)
            for i, tau in enumerate(row['tau']):
                self._tau[i].append(tau)
            for i, jet in enumerate(row['jet']):
                self._jet[i].append(jet)
            self._ett.append(row['ett'])
            self._ht.append(row['ht'])
            self._etm.append(row['etm'])
            self._htm.append(row['htm'])
            self._extcond.append(row['ext_con'])

    def muon(self, i):
        assert 0 <= i < TDF.MUON.count, "invalid muon index"
        return self._muon[i]

    def muons(self):
        """Retruns a list of all muon objects data. Provided for convenience."""
        return self._muon

    def eg(self, i):
        assert 0 <= i < TDF.EG.count, "invalid e/g index"
        return self._eg[i]

    def egs(self):
        """Retruns a list of all e/g objects data. Provided for convenience."""
        return self._eg

    def tau(self, i):
        assert 0 <= i < TDF.TAU.count, "invalid tau index"
        return self._tau[i]

    def taus(self):
        """Retruns a list of all Tau objects data. Provided for convenience."""
        return self._tau

    def jet(self, i):
        assert 0 <= i < TDF.JET.count, "invalid jet index"
        return self._jet[i]

    def jets(self):
        """Retruns a list of all jet objects data. Provided for convenience."""
        return self._jet

    def ett(self):
        return self._ett

    def ht(self):
        return self._ht

    def etm(self):
        return self._etm

    def htm(self):
        return self._htm

    def extconds(self):
        return self._extcond

class SimSpyDumpReader(FileReader):
    """Global trigger sim/spy dump file reader. It derives from class FileReader.

    Usage example
    -------------

    >>> reader = SimSpyDumpReader("sample.txt")

    """

    FIELDS = (
        ('muon', 'x{0}'.format(charcount(TDF.MUON.width)), TDF.MUON.count),
        ('eg',  'x{0}'.format(charcount(TDF.EG.width)), TDF.EG.count),
        ('tau', 'x{0}'.format(charcount(TDF.TAU.width)), TDF.TAU.count),
        ('jet', 'x{0}'.format(charcount(TDF.JET.width)), TDF.JET.count),
        ('ett', 'x{0}'.format(charcount(TDF.ETT.width))),
        ('ht',  'x{0}'.format(charcount(TDF.HT.width))),
        ('etm', 'x{0}'.format(charcount(TDF.ETM.width))),
        ('htm', 'x{0}'.format(charcount(TDF.HTM.width))),
        ('ext_con', 'x{0}'.format(charcount(TDF.EXTCOND.width))),
    )
    """Format for columns of test vector file. Refer to class FileReader for detailed docmatation."""

    OBJECT_NAMES = ('muon', 'eg', 'tau', 'jet', 'ett', 'ht', 'etm', 'htm', 'ext_con')
    """Object names in order."""

    def __init__(self, fp):
        super(SimSpyDumpReader, self).__init__(fp, fields = self.FIELDS)

class AlgorithmDump(object):
    """
    """

    def __init__(self, f = None):
        self.reset()
        if isinstance(f, str):
            self.read(open(f, 'rb'))
        elif isinstance(f, file):
            self.read(f)

    def reset(self):
        # Initialize the object data containers.
        self._algorithms = []

    def read(self, fp):
        self.reset()
        # Read file line by line.
        for row in TestVectorReader(fp):
            self._algorithms.append(row['algorithm'])

    def algorithms(self):
        return self._algorithms

class AlgorithmDumpReader(FileReader):
    """Global trigger algorithm dump file reader. It derives from class FileReader.

    Usage example
    -------------

    Creating a simulation memory image.

    >>> reader = AlgorithmDumpReader("dump.txt")

    """

    FIELDS = (
        ('algorithm', 'x{0}'.format(charcount(TDF.ALGORITHM.width))),
    )
    """Format for columns of test vector file. Refer to class FileReader for detailed docmatation."""

    def __init__(self, fp):
        super(AlgorithmDumpReader, self).__init__(fp, fields = self.FIELDS)

class FinorDump(object):
    """
    """

    def __init__(self, f = None):
        self.reset()
        if isinstance(f, str):
            self.read(open(f, 'rb'))
        elif isinstance(f, file):
            self.read(f)

    def reset(self):
        # Initialize the object data containers.
        self._finor = []

    def read(self, fp):
        self.reset()
        # Read file line by line.
        for row in TestVectorReader(fp):
            self._finor.append(row['finor'])

    def finor(self):
        return self._finor


class FinorDumpReader(FileReader):
    """Global trigger FINOR dump file reader. It derives from class FileReader.

    Usage example
    -------------

    >>> reader = FinorDumpReader("dump.txt")

    """

    FIELDS = (
        ('finor', 'b1'),
    )
    """Format for columns of test vector file. Refer to class FileReader for detailed docmatation."""

    def __init__(self, fp):
        super(FinorDumpReader, self).__init__(fp, fields = self.FIELDS)
