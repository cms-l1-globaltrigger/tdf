# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Bernhard Arnold <bernahrd.arnold@cern.ch>
#                     Johannes Wittmann <johannes.wittmann@cern.ch>
#
# Repository path   : $HeadURL: svn://heros.hephy.oeaw.ac.at/GlobalTriggerUpgrade/software/tdf/trunk/tdf/mp7/images.py $
# Last committed    : $Revision: 3982 $
# Last changed by   : $Author: arnold $
# Last changed date : $Date: 2015-05-22 12:00:28 +0200 (Fri, 22 May 2015) $
#

"""MP7 specific memory images.
"""

from tdf.core import TDF
from tdf.core.filereader import FileReader
from tdf.core.testvector import TestVector
from tdf.core.images import (
    GenericMemoryImage,
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

__version__ = '$Revision: 3982 $'

# Blocksize of 32 bit simulation and spy memories.
MEMORY_BLOCKSIZE = 4096

class SimSpyMemoryImage(ColumnMemoryImage):
    """Simulation/spy memory image."""

    # Calculate the memory column offsets.
    MuonOffset    = 0
    EgOffset      = MuonOffset + TDF.MUON.dwords * TDF.MUON.count
    TauOffset     = EgOffset   + TDF.EG.dwords   * TDF.EG.count
    JetOffset     = TauOffset  + TDF.TAU.dwords  * TDF.TAU.count
    EttOffset     = JetOffset  + TDF.JET.dwords  * TDF.JET.count
    HtOffset      = EttOffset  + TDF.ETT.dwords
    EtmOffset     = HtOffset   + TDF.HT.dwords
    HtmOffset     = EtmOffset  + TDF.ETM.dwords
    ExtCondOffset = HtmOffset  + TDF.HTM.dwords

    ObjectsOrdered = 'muon', 'eg', 'tau', 'jet', 'ett', 'ht', 'etm', 'htm', 'extcond'

    def __init__(self):
        super(SimSpyMemoryImage, self).__init__(MEMORY_BLOCKSIZE * 60, MEMORY_BLOCKSIZE)

    def muon(self, i, offset = 0):
        assert 0 <= i < TDF.MUON.count, "invalid muon index"
        values = self.extract(self.MuonOffset + TDF.MUON.dwords * i, TDF.MUON.dwords)[:TDF.ORBIT_LENGTH]
        return values[offset:] + values[:offset]

    def muons(self, offset = 0):
        """Retruns a list of all muon objects data. Provided for convenience."""
        return [self.muon(i, offset) for i in range(TDF.MUON.count)]

    def eg(self, i, offset = 0):
        assert 0 <= i < TDF.EG.count, "invalid e/g index"
        values = self.extract(self.EgOffset + TDF.EG.dwords * i, TDF.EG.dwords)[:TDF.ORBIT_LENGTH]
        return values[offset:] + values[:offset]

    def egs(self, offset = 0):
        """Retruns a list of all e/g objects data. Provided for convenience."""
        return [self.eg(i, offset) for i in range(TDF.EG.count)]

    def tau(self, i, offset = 0):
        assert 0 <= i < TDF.TAU.count, "invalid tau index"
        values = self.extract(self.TauOffset + TDF.TAU.dwords * i, TDF.TAU.dwords)[:TDF.ORBIT_LENGTH]
        return values[offset:] + values[:offset]

    def taus(self, offset = 0):
        """Retruns a list of all Tau objects data. Provided for convenience."""
        return [self.tau(i, offset) for i in range(TDF.TAU.count)]

    def jet(self, i, offset = 0):
        assert 0 <= i < TDF.JET.count, "invalid jet index"
        values = self.extract(self.JetOffset + TDF.JET.dwords * i, TDF.JET.dwords)[:TDF.ORBIT_LENGTH]
        return values[offset:] + values[:offset]

    def jets(self, offset = 0):
        """Retruns a list of all jet objects data. Provided for convenience."""
        return [self.jet(i, offset) for i in range(TDF.JET.count)]

    def ett(self, offset = 0):
        values = self.extract(self.EttOffset)[:TDF.ORBIT_LENGTH]
        return values[offset:] + values[:offset]

    def ht(self, offset = 0):
        values = self.extract(self.HtOffset)[:TDF.ORBIT_LENGTH]
        return values[offset:] + values[:offset]

    def etm(self, offset = 0):
        values = self.extract(self.EtmOffset)[:TDF.ORBIT_LENGTH]
        return values[offset:] + values[:offset]

    def htm(self, offset = 0):
        values = self.extract(self.HtmOffset)[:TDF.ORBIT_LENGTH]
        return values[offset:] + values[:offset]

    def extconds(self, offset = 0):
        values = self.extract(self.ExtCondOffset, TDF.EXTCOND.dwords)[:TDF.ORBIT_LENGTH]
        return values[offset:] + values[:offset]

    def dump(self, fs):
        fs.write(str(self))

    def read(self, fs):
        self.clear()

        reader = FileReader(fs, (
            ('muon', 'x{0}'.format(charcount(TDF.MUON.width)), TDF.MUON.count),
            ('eg',  'x{0}'.format(charcount(TDF.EG.width)), TDF.EG.count),
            ('tau', 'x{0}'.format(charcount(TDF.TAU.width)), TDF.TAU.count),
            ('jet', 'x{0}'.format(charcount(TDF.JET.width)), TDF.JET.count),
            ('ett', 'x{0}'.format(charcount(TDF.ETT.width))),
            ('ht',  'x{0}'.format(charcount(TDF.HT.width))),
            ('etm', 'x{0}'.format(charcount(TDF.ETM.width))),
            ('htm', 'x{0}'.format(charcount(TDF.HTM.width))),
            ('extcond', 'x{0}'.format(charcount(TDF.EXTCOND.width))),
        ))
        data = reader.read()

        # Populate memory image.
        for i, values in enumerate(data['muon']):
            self.inject(values, self.MuonOffset + TDF.MUON.dwords * i, TDF.MUON.dwords)
        for i, values in enumerate(data['eg']):
            self.inject(values, self.EgOffset + TDF.EG.dwords * i, TDF.EG.dwords)
        for i, values in enumerate(data['tau']):
            self.inject(values, self.TauOffset + TDF.TAU.dwords * i, TDF.TAU.dwords)
        for i, values in enumerate(data['jet']):
            self.inject(values, self.JetOffset + TDF.JET.dwords * i, TDF.JET.dwords)
        self.inject(data['ett'], self.EttOffset, TDF.ETT.dwords)
        self.inject(data['ht'], self.HtOffset, TDF.HT.dwords)
        self.inject(data['etm'], self.EtmOffset, TDF.ETM.dwords)
        self.inject(data['htm'], self.HtmOffset, TDF.HTM.dwords)
        self.inject(data['extcond'], self.ExtCondOffset, TDF.EXTCOND.dwords)

    def read_testvector(self, fs, uuid = None):
        self.clear()

        # Read data from vector file.
        testvector = TestVector()
        testvector.read(fs)

        # Make sure that the device menu UUID matches the test vector menu UUID.
        if uuid:
            if uuid != testvector.menu_uuid:
                raise RuntimeError("test vector does not match device menu UUID {uuid}".format(**locals()))

        # Populate memory image.
        for i, values in enumerate(testvector.muons()):
            self.inject(values, self.MuonOffset + TDF.MUON.dwords * i, TDF.MUON.dwords)
        for i, values in enumerate(testvector.egs()):
            self.inject(values, self.EgOffset + TDF.EG.dwords * i, TDF.EG.dwords)
        for i, values in enumerate(testvector.taus()):
            self.inject(values, self.TauOffset + TDF.TAU.dwords * i, TDF.TAU.dwords)
        for i, values in enumerate(testvector.jets()):
            self.inject(values, self.JetOffset + TDF.JET.dwords * i, TDF.JET.dwords)
        self.inject(testvector.ett(), self.EttOffset, TDF.ETT.dwords)
        self.inject(testvector.ht(), self.HtOffset, TDF.HT.dwords)
        self.inject(testvector.etm(), self.EtmOffset, TDF.ETM.dwords)
        self.inject(testvector.htm(), self.HtmOffset, TDF.HTM.dwords)
        self.inject(testvector.extconds(), self.ExtCondOffset, TDF.EXTCOND.dwords)

    def compare(self, image, offset = 0, size = TDF.ORBIT_LENGTH, outfile = sys.stdout):
        # ignore: number of BX to be ignored from start
        assert isinstance(image, SimSpyMemoryImage)
        errors = []
        stats = []

        class Analyzer:
            def __init__(self, offset, size, errors, stats):
                self.offset = offset
                self.size = size
                self.errors = errors
                self.stats = stats
            def check_objects(self, typename, a, b):
                if getattr(TDF, typename).count == 1:
                    a = [a, ]
                    b = [b, ]
                for i in range(getattr(TDF, typename).count):
                    all_, ok_, err_, bc50_ = 0, 0, 0, 0
                    for bx in range(self.size):
                        value_a = a[i][bx]
                        value_b = b[i][bx]
                        # Ignore zero/50bc data sets.
                        if value_a == value_b == 0:
                            continue
                        if '505050bc' in hex(value_a):
                            bc50_ += 1
                            continue
                        # Log mismatches.
                        if value_a != value_b:
                            err_ += 1
                            value_a_hex = getattr(TDF, typename).hexstr(value_a)
                            value_b_hex = getattr(TDF, typename).hexstr(value_b)
                            self.errors.append("\n".join((
                                "{typename}[{i}] object missmatch in BX {bx} with offset {self.offset}",
                                "mem: 0x{value_a_hex}",
                                "ref: 0x{value_b_hex}",
                            )).format(**locals()))
                        else:
                            ok_ += 1
                        all_ += 1
                    if all_:
                        if err_:
                            stats.append("{ok_}/{all_} {typename}[{i}] objects OK, {err_} MISMATCHES".format(**locals()))
                        else:
                            stats.append("{ok_}/{all_} {typename}[{i}] objects OK".format(**locals()))
                    else:
                        stats.append("no {typename}[{i}] objects in pattern".format(**locals()))
                    if bc50_:
                        stats.append("ignored {bc50_} `505050bc' matches for {typename}[{i}]".format(**locals()))

        check_objects = Analyzer(offset, size, errors, stats).check_objects
        check_objects('MUON', self.muons(offset), image.muons())
        check_objects('EG', self.egs(offset), image.egs())
        check_objects('TAU', self.taus(offset), image.taus())
        check_objects('JET', self.jets(offset), image.jets())
        check_objects('ETT', self.ett(offset), image.ett())
        check_objects('HT', self.ht(offset), image.ht())
        check_objects('ETM', self.etm(offset), image.etm())
        check_objects('HTM', self.htm(offset), image.htm())
        check_objects('EXTCOND', self.extconds(offset), image.extconds())

        outfile.write("\n".join(stats))
        outfile.write("\n")
        errors_total = len(errors)
        if errors_total:
            outfile.write("\n".join(errors))
            outfile.write("\n")
            outfile.write("Found {errors_total} SIMSPY mismatches by comparing a range of {size} BX with offset {offset}\n".format(**locals()))
        else:
            outfile.write("Success. No object data errors.\n")
        outfile.flush()

    def __str__(self):
        """Cast memory to hex string."""
        lines = []
        muons, egs, taus, jets = self.muons(), self.egs(), self.taus(), self.jets()
        ett, ht, etm, htm = self.ett(), self.ht(), self.etm(), self.htm()
        extconds = self.extconds()

        for i in range(TDF.ORBIT_LENGTH):
            line = []
            for muon in muons:
                line.append(TDF.MUON.hexstr(muon[i]))
            for eg in egs:
                line.append(TDF.EG.hexstr(eg[i]))
            for tau in taus:
                line.append(TDF.TAU.hexstr(tau[i]))
            for jet in jets:
                line.append(TDF.JET.hexstr(jet[i]))

            line.append(TDF.ETT.hexstr(ett[i]))
            line.append(TDF.HT.hexstr(ht[i]))
            line.append(TDF.ETM.hexstr(etm[i]))
            line.append(TDF.HTM.hexstr(htm[i]))

            line.append(TDF.EXTCOND.hexstr(extconds[i]))

            lines.append(' '.join(line))
        return '\n'.join(lines)

    def decode(self):
        """Decode objects attributes to JSON."""

        data = []
        muons, egs, taus, jets = self.muons(), self.egs(), self.taus(), self.jets()
        ett, ht, etm, htm = self.ett(), self.ht(), self.etm(), self.htm()
        extconds = self.extconds()

        for i in range(TDF.ORBIT_LENGTH):
            bx_data = {'bx': i}

            bx_data['muon'] = []
            for muon in muons:
                obj_data = TDF.MUON.decode(muon[i])
                obj_data['raw'] = TDF.MUON.hexstr(muon[i])
                bx_data['muon'].append(obj_data)

            bx_data['eg'] = []
            for eg in egs:
                obj_data = TDF.EG.decode(eg[i])
                obj_data['raw'] = TDF.EG.hexstr(eg[i])
                bx_data['eg'].append(obj_data)

            bx_data['tau'] = []
            for tau in taus:
                obj_data = TDF.TAU.decode(tau[i])
                obj_data['raw'] = TDF.TAU.hexstr(tau[i])
                bx_data['tau'].append(obj_data)

            bx_data['jet'] = []
            for jet in jets:
                obj_data = TDF.JET.decode(jet[i])
                obj_data['raw'] = TDF.JET.hexstr(jet[i])
                bx_data['jet'].append(obj_data)

            obj_data = TDF.ETT.decode(ett[i])
            obj_data['raw'] = TDF.ETT.hexstr(ett[i])
            bx_data['ett'] = obj_data

            obj_data = TDF.HT.decode(ht[i])
            obj_data['raw'] = TDF.HT.hexstr(ht[i])
            bx_data['ht'] = obj_data

            obj_data = TDF.ETM.decode(htm[i])
            obj_data['raw'] = TDF.HT.hexstr(htm[i])
            bx_data['etm'] = obj_data

            obj_data = TDF.HTM.decode(htm[i])
            obj_data['raw'] = TDF.HTM.hexstr(htm[i])
            bx_data['htm'] = obj_data

            data.append(bx_data)

        return json.dumps(data, sort_keys = True, indent = 2, separators = (',', ': '))

class AlgorithmMemoryImage(ColumnMemoryImage):
    """Memory for spied algorithms."""

    def __init__(self):
        super(AlgorithmMemoryImage, self).__init__(MEMORY_BLOCKSIZE * 16, MEMORY_BLOCKSIZE)

    def algorithms(self, offset = 0):
        """Return algorithms as list. Offset rotates values by BX. Provided for convenience."""
        values = self.merged()[:TDF.ORBIT_LENGTH]
        return values[offset:] + values[:offset]

    def read(self, fs):
        """Read from simple dump file."""
        self.clear()
        reader = FileReader(fs, fields = (('algorithms', 'x128'), ))
        self.inject(reader.read()['algorithms'], 0, TDF.ALGORITHM.dwords)

    def read_testvector(self, fs, uuid = None):
        """Read from test vector file."""
        self.clear()

        # Read data from vector file.
        testvector = TestVector()
        testvector.read(fs)

        # Make sure that the device menu UUID matches the test vector menu UUID.
        if uuid:
            if uuid != testvector.menu_uuid:
                raise RuntimeError("test vector does not match device menu UUID {uuid}".format(**locals()))

        # Populate memory image.
        self.inject(testvector.algorithms(), 0, TDF.ALGORITHM.dwords)

    def compare(self, image, offset = 0, size = TDF.ORBIT_LENGTH, outfile = sys.stdout):
        assert isinstance(image, AlgorithmMemoryImage), "can only compare two memory images of same type"
        errors = []
        a = self.algorithms(offset)
        b = image.algorithms()
        for bx in range(size):
            value_a = a[bx]
            value_b = b[bx]
            if value_a != value_b:
                bits_a = ",".join([str(n) for n, bit in enumerate(TDF.ALGORITHM.binstr(value_a)[::-1]) if bit == '1']) or "none"
                bits_b = ",".join([str(n) for n, bit in enumerate(TDF.ALGORITHM.binstr(value_b)[::-1]) if bit == '1']) or "none"
                value_a_hex = TDF.ALGORITHM.hexstr(value_a)
                value_b_hex = TDF.ALGORITHM.hexstr(value_b)
                errors.append("Algorithm missmatch in BX {bx} with offset {offset}\nmem: 0x{value_a_hex} : {bits_a}\nref: 0x{value_b_hex} : {bits_b}".format(**locals()))
        if errors:
            errors.append("Found {0} algorithm mismatches by comparing a range of {1} BX with offset {2}".format(len(errors), size, offset))
            outfile.write("\n".join(errors))
            outfile.write("\n")
        else:
            outfile.write("Success. No algorithm errors.\n")
        outfile.flush()

    def __str__(self):
        chars = charcount(self.columns * TDF.DATA_WIDTH)
        return '\n'.join(TDF.ALGORITHM.hexstr(value) for value in self.algorithms())

class FinorMemoryImage(ColumnMemoryImage):
    """Memory for spied algorithms."""

    def __init__(self):
        super(FinorMemoryImage, self).__init__(MEMORY_BLOCKSIZE * 1, MEMORY_BLOCKSIZE)

    def finors(self, offset = 0):
        """Return FINORs as list. Offset rotates values by BX. Provided for convenience."""
        values = [value & 0x1 for value in self.merged()[:TDF.ORBIT_LENGTH]]
        return values[offset:] + values[:offset]

    def read(self, fs):
        """Read from simple dump file."""
        reader = FileReader(fs, fields = (('finors', 'b1'), ))
        self.clear()
        self.inject(reader.read()['finors'], 0, TDF.FINOR.dwords)

    def read_testvector(self, fs, uuid = None):
        """Read from test vector file."""
        self.clear()

        # Read data from vector file.
        testvector = TestVector()
        testvector.read(fs)

        # Make sure that the device menu UUID matches the test vector menu UUID.
        if uuid:
            if uuid != testvector.menu_uuid:
                raise RuntimeError("test vector does not match device menu UUID {uuid}".format(**locals()))

        # Populate memory image.
        self.inject(testvector.finor(), 0, TDF.FINOR.dwords)

    def compare(self, image, offset = 0, size = TDF.ORBIT_LENGTH, outfile = sys.stdout):
        assert isinstance(image, FinorMemoryImage)
        errors = []
        a = self.finors()
        a = a[offset:] + a[:offset]
        b = image.finors()
        for bx in range(size):
            value_a = a[bx]
            value_b = b[bx]
            if value_a != value_b:
                value_a_hex = TDF.FINOR.hexstr(value_a)
                value_b_hex = TDF.FINOR.hexstr(value_b)
                errors.append("FINOR missmatch in BX {bx} with offset {offset}\n 0x{value_a_hex} <> 0x{value_b_hex}".format(**locals()))
        if errors:
            nr_errors = len(errors)
            errors.append("Found {nr_errors} FINOR mismatches by comparing a range of {size} BX with offset {offset}".format(**locals()))
            outfile.write("\n".join(errors))
            outfile.write("\n")
        else:
            outfile.write("Success. No FINOR errors.\n")
        outfile.flush()

    def __str__(self):
        return '\n'.join(TDF.FINOR.hexstr(value) for value in self.finors())

class AlgoBxMemoryImage(AlgorithmMemoryImage):
    """Memory for algorithm BX masks."""

    def __init__(self):
        super(AlgoBxMemoryImage, self).__init__()

    def setEnabled(self, enabled):
        """Enable or disable all algorithms of all BX."""
        self.clear(bitmask(TDF.DATA_WIDTH) if enabled else 0x0)

# TODO to be replaced by column based memory
class RopMemoryImage(GenericMemoryImage):
    """Memory for generic ROP records to be used with different modules.

        bbbbbbbbaaaaaaa
        ddddddddccccccc
    """

    RECORD_WIDTH = 64

    def __init__(self):
        super(RopMemoryImage, self).__init__(65536)

    def lines(self):
        """Returns all 64 bit lines of record."""
        data = []
        for i in range(0, self.size, 2):
            data.append(bitjoin(self.data[i:i + 2], TDF.DATA_WIDTH))
        return data

    def __str__(self):
        chars = charcount(self.RECORD_WIDTH)
        return '\n'.join('{0:0{1}x}'.format(value, chars) for value in self.lines())
