# -*- coding: utf-8 -*-
#
# Copyright 2013-2015 Bernhard Arnold <bernahrd.arnold@cern.ch>
#
# Repository path   : $HeadURL: svn://heros.hephy.oeaw.ac.at/GlobalTriggerUpgrade/software/tdf/trunk/tdf/mp7/unpacker.py $
# Last committed    : $Revision: 3751 $
# Last changed by   : $Author: arnold $
# Last changed date : $Date: 2015-02-13 15:13:07 +0100 (Fri, 13 Feb 2015) $
#

"""
Record unpacker
===============

The unpacker module provides a set of classes to validate a GT readout record.

Usage examples
==============

Simple usage example.

>>> data = RecordFileReader(open('sample.dat')).read()
>>> record = ReadoutRecord(data)
>>> print record

Validating content.

>>> for error in record.run_tests():
...     print error

Validating data using a reference test vector (pattern file).

>>> pattern = TestVectorReader(open('pattern.txt'))
>>> record = ReadoutRecord(data, pattern)

Validating using a L1-Trigger menu to fetch algorithm names.

>>> menu = l1triggermenu.l1tm_factory(open('menu.xml').read())
>>> record = ReadoutRecord(data, pattern, menu)

"""

from tdf.core.binutils import bitmask
from tdf.core.unpacker import RecordSection

from datetime import datetime
import re, sys

__version__ = '$Revision: 3751 $'

TTY_WIDTH = 128
TTY_HR_CHAR = '-'

RECORD_EOL = '\n'
RECORD_WIDTH = 64

# -----------------------------------------------------------------------------
#  Helper functions.
# -----------------------------------------------------------------------------

def bxrange(n):
    """Calcualtes the multi BX range for multiple records.

    >>> bxrange(5)
    [-2, -1, 0, 1, 2]

    """
    return range(-(n / 2), n / 2 + 1)

def eventrange(n):
    """Calcualtes the encoded event range. negative BX offsets are using two's
    complement representation. Maximum event range *n* < 32.

    >>> eventrange(5)
    [0xe, 0xf, 0x0, 0x1, 0x2]

    """
    assert n < 32, "eventrange(n): maximum eventrange must be between 0 <= n < 32"
    return [range(16)[i] for i in bxrange(n)]

def bit_diff(n, value, reference):
    """Compares two values, returns a list of tuples containing missmatching bit
    positions, value and reference bit value.

    >>> bit_diff(8, 0x1f, 0x0f)
    [(4, 1, 0)]

    """
    differences = []
    for i in range(n):
        val_bit = value >> i & 1
        ref_bit = reference >> i & 1
        if val_bit != ref_bit:
            differences.append((i, val_bit, ref_bit))
    return differences

# -----------------------------------------------------------------------------
#  Record data section class.
# -----------------------------------------------------------------------------

class RecordDataSection(RecordSection):

    def __init__(self, data, name, bx_offset):
        super(RecordDataSection, self).__init__(data, name)
        self.bx_offset = bx_offset
        self.name = "{self.name}[BX {self.bx_offset:}]".format(**locals())

# -----------------------------------------------------------------------------
#  Implementation of record sections.
# -----------------------------------------------------------------------------

class AmcHeaderSection(RecordSection):
    """Record header consisting of two words."""

    def __init__(self, data):
        super(AmcHeaderSection, self).__init__(data, "amc_header")

        self.unpack_line(
            "AmcNo[63:60]",
            "LV1_id[55:32]",
            "BX_id[31:20]",
            "Data_lgth[19:0]",
        )

        self.unpack_line(
            "OrN[31:16]",
            "BoardID[15:0]",
        )

class PayloadSection(RecordSection):
    """The payload section starts with a header consisting of four words
    containing information about the size of the following payload data.

    *total_bx_in_event_decision* contains the count of algorithm sections.
    *total_bx_in_event_ext_cond* contains the count of external condition sections.
    *total_bx_in_event_gmt* contains the count of GMT data section.
    *total_bx_in_event_gct* contains the count of calorimeter data sections.
    """

    def __init__(self, data):
        super(PayloadSection, self).__init__(data, "gt_data_payload")

        self.unpack_line(
            "VERSION[63:32]",
            "total_bx_in_event_decision[31:28]",
            "total_bx_in_event_ext_cond[27:24]",
            "total_bx_in_event_gmt[23:20]",
            "total_bx_in_event_gct[19:16]",
            "prescale_factor_set_index[7:0]",
        )
        self.unpack_line(
            "trigger_nr[63:0]",
        )
        self.unpack_line(
            "orbit_nr[63:16]",
            "bx_nr[15:0]",
        )
        self.unpack_line(
            "luminosity_seg_nr[63:32]",
            "gt_internal_event_nr[31:0]",
        )

class AlgorithmSection(RecordDataSection):
    """Algorithm section consisting of 25 words in total, one header word
    followed by three data sections consisting of eight words in total resembling a
    512 bit little-endian value.
    """

    def __init__(self, data, bx_offset):
        super(AlgorithmSection, self).__init__(data, "algorithm_trigger_decision", bx_offset)

        self.unpack_line(
            "orbit_nr[63:32]",
            "bx_nr[31:16]",
            "bx_in_event[7:4]",
            "final_ors[3:0]",
        )

        self.unpack_line("algo_before_pre[0][63:0]")
        self.unpack_line("algo_before_pre[1][63:0]")
        self.unpack_line("algo_before_pre[2][63:0]")
        self.unpack_line("algo_before_pre[3][63:0]")
        self.unpack_line("algo_before_pre[4][63:0]")
        self.unpack_line("algo_before_pre[5][63:0]")
        self.unpack_line("algo_before_pre[6][63:0]")
        self.unpack_line("algo_before_pre[7][63:0]")

        self.unpack_line("algo_after_pre[0][63:0]")
        self.unpack_line("algo_after_pre[1][63:0]")
        self.unpack_line("algo_after_pre[2][63:0]")
        self.unpack_line("algo_after_pre[3][63:0]")
        self.unpack_line("algo_after_pre[4][63:0]")
        self.unpack_line("algo_after_pre[5][63:0]")
        self.unpack_line("algo_after_pre[6][63:0]")
        self.unpack_line("algo_after_pre[7][63:0]")

        self.unpack_line("algo_after_mask[0][63:0]")
        self.unpack_line("algo_after_mask[1][63:0]")
        self.unpack_line("algo_after_mask[2][63:0]")
        self.unpack_line("algo_after_mask[3][63:0]")
        self.unpack_line("algo_after_mask[4][63:0]")
        self.unpack_line("algo_after_mask[5][63:0]")
        self.unpack_line("algo_after_mask[6][63:0]")
        self.unpack_line("algo_after_mask[7][63:0]")

class ExternalsSection(RecordDataSection):
    """External conditions section consisting of five words in total, one header word
    followed by a data sections consisting of four words in total resembling a
    256 bit little-endian value.
    """

    def __init__(self, data, bx_offset):
        super(ExternalsSection, self).__init__(data, "external_conditions", bx_offset)

        self.unpack_line(
            "orbit_nr[63:32]",
            "bx_nr[31:16]",
            "bx_in_event[7:4]",
        )

        self.unpack_line("external_condition[0][63:0]")
        self.unpack_line("external_condition[1][63:0]")
        self.unpack_line("external_condition[2][63:0]")
        self.unpack_line("external_condition[3][63:0]")

class MuonSection(RecordDataSection):
    """Muon data section consisting of nine words in total, one header word
    followed by a data sections consisting of eight data words.
    """

    def __init__(self, data, bx_offset):
        super(MuonSection, self).__init__(data, "global_muon_objects", bx_offset)

        self.unpack_line(
            "orbit_nr[63:32]",
            "bx_nr[31:16]",
            "bx_in_event[7:4]",
            "final_ors[3:0]",
        )

        self.unpack_line("muon_data[0][63:0]")
        self.unpack_line("muon_data[1][63:0]")
        self.unpack_line("muon_data[2][63:0]")
        self.unpack_line("muon_data[3][63:0]")
        self.unpack_line("muon_data[4][63:0]")
        self.unpack_line("muon_data[5][63:0]")
        self.unpack_line("muon_data[6][63:0]")
        self.unpack_line("muon_data[7][63:0]")

class CalorimeterSection(RecordDataSection):
    """Calorimter data section consisting of 17 words in total, one header word
    followed by three data sections consisting of six (eg), four (tau) and again
    six (jet) words. Each data section contains a list of 32-bit values (two
    values in each record word).
    """

    def __init__(self, data, bx_offset):
        super(CalorimeterSection, self).__init__(data, "global_calo_objects", bx_offset)

        self.unpack_line(
            "orbit_nr[63:32]",
            "bx_nr[31:16]",
            "bx_in_event[7:4]",
            "final_ors[3:0]",
        )

        self.unpack_line("eg_data[0][31:0]", "eg_data[1][63:32]")
        self.unpack_line("eg_data[2][31:0]", "eg_data[3][63:32]")
        self.unpack_line("eg_data[4][31:0]", "eg_data[5][63:32]")
        self.unpack_line("eg_data[6][31:0]", "eg_data[7][63:32]")
        self.unpack_line("eg_data[8][31:0]", "eg_data[9][63:32]")
        self.unpack_line("eg_data[10][31:0]", "eg_data[11][63:32]")

        self.unpack_line("tau_data[0][31:0]", "tau_data[1][63:32]")
        self.unpack_line("tau_data[2][31:0]", "tau_data[3][63:32]")
        self.unpack_line("tau_data[4][31:0]", "tau_data[5][63:32]")
        self.unpack_line("tau_data[6][31:0]", "tau_data[7][63:32]")

        self.unpack_line("jet_data[0][31:0]", "jet_data[1][63:32]")
        self.unpack_line("jet_data[2][31:0]", "jet_data[3][63:32]")
        self.unpack_line("jet_data[4][31:0]", "jet_data[5][63:32]")
        self.unpack_line("jet_data[6][31:0]", "jet_data[7][63:32]")
        self.unpack_line("jet_data[8][31:0]", "jet_data[9][63:32]")
        self.unpack_line("jet_data[10][31:0]", "jet_data[11][63:32]")

class AmcTrailerSection(RecordSection):
    """Record trailer consisting of a single word."""

    def __init__(self, data):
        super(AmcTrailerSection, self).__init__(data, "amc_trailer")

        self.unpack_line(
            "CRC_32[63:32]",
            "LV1_id[31:24]",
            "Data_lgth[19:0]",
        )

# -----------------------------------------------------------------------------
#  Readout record container and consistency tests.
# -----------------------------------------------------------------------------


class ReadoutRecord(object):

    VERSION = __version__

    def __init__(self, data, pattern = None, menu = None):
        self._data = data
        self._sections = []
        self._timestamp = datetime.now()

        # Optional reference pattern/menu.
        self._reference_pattern = pattern
        self._menu = menu

        # Record sections.
        self.add_section(AmcHeaderSection, 'header')
        self.add_section(PayloadSection, 'payload')
        self.add_repeating_section(AlgorithmSection, 'algorithms', self.payload.total_bx_in_event_decision.value)
        self.add_repeating_section(ExternalsSection, 'externals', self.payload.total_bx_in_event_ext_cond.value)
        self.add_repeating_section(MuonSection, 'muons', self.payload.total_bx_in_event_gmt.value)
        self.add_repeating_section(CalorimeterSection, 'calos', self.payload.total_bx_in_event_gct.value)
        self.add_section(AmcTrailerSection, 'trailer')

    def add_section(self, cls, name, *args):
        section = cls(self._data, *args)
        self._sections.append(section)
        setattr(self, name, section)
        return section

    def add_repeating_section(self, cls, name, count):
        """For multiple bx range sections."""
        sections = []
        for i in range(count):
            sections.append(self.add_section(cls, name, bxrange(count)[i]))
        setattr(self, name, sections)
        return sections

    def run_tests(self):
        """Executes all methods starting with test_*."""
        errors = []
        for attr in dir(self):
            if attr.startswith("test_"):
                attr_handle = getattr(self, attr)
                if hasattr(attr_handle, '__call__'):
                    errors.extend(filter(lambda result: result != None, attr_handle()))
        return errors

    def test_100_data_length(self):
        return (
            self.header.Data_lgth.compare(self.trailer.Data_lgth),
        )

    def test_110_length(self):
        return (
            self.header.Data_lgth.compare(self._data.pos),
        )

    def test_120_level1_id(self):
        return (
            self.header.LV1_id.compare(self.trailer.LV1_id, bitmask(8)),
        )

    def test_130_bx_id(self):
        return (
            self.header.BX_id.compare(self.payload.bx_nr, bitmask(12)),
        )

    def test_200_algorithm_orbit_nr(self):
        return [
            item.orbit_nr.compare(self.payload.orbit_nr)
            for i, item in enumerate(self.algorithms)
        ]

    def test_210_algorithm_bx_nr(self):
        return [
            item.bx_nr.compare(self.payload.bx_nr.value + bxrange(len(self.algorithms))[i])
            for i, item in enumerate(self.algorithms)
        ]

    def test_220_algorithm_bx_in_event(self):
        req_events = eventrange(len(self.algorithms))
        return [
            item.bx_in_event.compare(req_events[i])
            for i, item in enumerate(self.algorithms)
        ]

    def test_230_algorithm_data(self):
        """
        Note: `algo_after_pre' and `algo_after_mask' can not be checked!
        """

        # Execute only if pattern data avalable.
        if not self._reference_pattern:
            return []

        errors = []
        for item in self.algorithms:

            algorithm = item.algo_before_pre.join_value()
            reference = self._reference_pattern[item.bx_nr.value]['algorithm']

            if algorithm != reference:
                offset = item.bx_nr.value - self.payload.bx_nr.value
                line = item.algo_before_pre[0].line
                message = [
                    "ERROR: mismatch in algorithms [BX {offset}] in bx {item.bx_nr.value} (record != pattern) at address 0x{line:04x}".format(**locals()),
                    "{algorithm:0128x}".format(**locals()),
                    "{reference:0128x}".format(**locals()),
                ]
                for diff in bit_diff(item.algo_before_pre.join_size(), algorithm, reference):
                    name = ''
                    if self._menu:
                        algorithm_item =  self._menu.algorithms.findIndex(diff[0])
                        name = ':{0}'.format(algorithm_item.name) if algorithm_item else ':<no such algorithm>'
                    message.append(" - algorithm[{diff[0]}]{name}:    record={diff[1]} <> pattern={diff[2]}".format(**locals()))
                errors.append(RECORD_EOL.join(message))
        return errors

    def test_300_external_orbit_nr(self):
        """Compares external's orbit number with payload header."""
        return [
            item.orbit_nr.compare(self.payload.orbit_nr)
            for i, item in enumerate(self.externals)
        ]

    def test_310_external_bx_nr(self):
        """Compares external's BX number (with offsets) with payload header."""
        return [
            item.bx_nr.compare(self.payload.bx_nr.value + bxrange(len(self.externals))[i])
            for i, item in enumerate(self.externals)
        ]

    def test_320_external_bx_in_event(self):
        """Check external's BX offset (e f 0 1 2)."""
        return [
            item.bx_in_event.compare(eventrange(len(self.externals))[i])
            for i, item in enumerate(self.externals)
        ]

    def test_330_external_data(self):

        # Execute only if pattern data avalable.
        if not self._reference_pattern:
            return []

        errors = []
        for i, item in enumerate(self.externals):

            external = item.external_condition.join_value()
            reference = self._reference_pattern[item.bx_nr.value]['ext_con']

            if external != reference:
                offset = item.bx_nr.value - self.payload.bx_nr.value
                line = item.external_condition[0].line
                message = [
                    "ERROR: mismatch in external_condition [BX {offset}] in bx {item.bx_nr.value} (record != pattern) at address 0x{line:04x}".format(**locals()),
                    "{external:064x}".format(**locals()),
                    "{reference:064x}".format(**locals()),
                ]
                for diff in bit_diff(item.external_condition.join_size(), external, reference):
                    message.append(" - external_condition[{diff[0]}]    record={diff[1]} <> pattern={diff[2]}".format(**locals()))
                errors.append(RECORD_EOL.join(message))
        return errors

    def test_400_muon_data(self):
        errors = []

        for i, muon in enumerate(self.muons):

            errors.append(muon.orbit_nr.compare(self.payload.orbit_nr))
            errors.append(muon.bx_nr.compare(self.payload.bx_nr.value + bxrange(len(self.muons))[i]))
            errors.append(muon.bx_in_event.compare(eventrange(len(self.muons))[i]))

            if self._reference_pattern:
                for i_data, data in enumerate(muon.muon_data):
                    errors.append(data.compare(self._reference_pattern[muon.bx_nr.value]['muon'][i_data]))

        return errors

    def test_500_calorimeter_data(self):
        errors = []

        for i, calo in enumerate(self.calos):

            errors.append(calo.orbit_nr.compare(self.payload.orbit_nr))
            errors.append(calo.bx_nr.compare(self.payload.bx_nr.value + bxrange(len(self.calos))[i]))
            errors.append(calo.bx_in_event.compare(eventrange(len(self.calos))[i]))

            # Validate data if reference pattern is available.
            if self._reference_pattern:

                # Validate e/g data.
                for i_data, data in enumerate(calo.eg_data):
                    errors.append(data.compare(self._reference_pattern[calo.bx_nr.value]['eg'][i_data]))

                # Validate tau data.
                for i_data, data in enumerate(calo.tau_data):
                    errors.append(data.compare(self._reference_pattern[calo.bx_nr.value]['tau'][i_data]))

                # Validate jet data.
                for i_data, data in enumerate(calo.jet_data):
                    errors.append(data.compare(self._reference_pattern[calo.bx_nr.value]['jet'][i_data]))

        return errors

    def error_report(self):
        """Returns a detailed error report string."""
        buf = []
        errors = self.run_tests()

        if errors:
            count = len(errors)
            buf.extend([
                RECORD_EOL,
                " consistency error report ".center(TTY_WIDTH, TTY_HR_CHAR),
                RECORD_EOL,
            ])

            for i, error in enumerate(errors):
                buf.extend([
                    " error {i:d} ".format(**locals()).center(TTY_WIDTH, TTY_HR_CHAR),
                    str(error),
                ])

            buf.extend([
                TTY_HR_CHAR * TTY_WIDTH,
                "{count} consistency errors found.".format(**locals()),
                TTY_HR_CHAR * TTY_WIDTH,
            ])
        else:
            buf.extend([
                "No errors found. Valid record."
            ])
        return RECORD_EOL.join(buf)

    def __str__(self):
        report = [
            " Readout Record Report ".center(TTY_WIDTH, TTY_HR_CHAR),
            "Record size: {self._data.pos} lines",
            "Date/Time: {self._timestamp}",
            "Unpacker version: {self.VERSION}",
        ]
        report.extend(str(section) for section in self._sections)
        report.append(TTY_HR_CHAR * TTY_WIDTH)
        return '\n'.join(report).format(**locals())
