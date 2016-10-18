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

"""Buffer generator class for tx/rx buffer patterns.
"""

from tdf.core import binutils
from tdf.core.testvector import TestVector

# -----------------------------------------------------------------------------
#  Helpers.
# -----------------------------------------------------------------------------

def str_board(board):
    """Returns first header line."""
    return "Board {board}".format(**locals())

def str_quad(quad, channel):
    """Returns second header line."""
    return "   q{quad:02d}c{channel:01d}  ".format(**locals())

def str_link(link):
    """Returns third header line."""
    return "    {link:02d}    ".format(**locals())

def str_frame(frame):
    """Returns initial frame line."""
    return "Frame {frame:04d} :".format(**locals())

def str_value(value = 0, valid = True):
    """Returns a DWORD value with prepended valid flag.
        eg. "1vdeadbeef"
    """
    return "{valid:01d}v{value:08x}".format(**locals())

def counter_value(quad, channel, frame):
    """Returns object counter value.
    Format by HB, '0xXXYYZZZZ' where X is the lane, Y the object (0..5), Z the BX.
    """
    lane = (quad * 4 + channel) & binutils.bitmask(8)
    obj = (frame % 6) & binutils.bitmask(8)
    bx = (frame // 6) & binutils.bitmask(16) # 6 objects per bx in 240 Mz domain.
    return lane << 24 | obj << 16 | bx

def low(value):
    """Return lower DWORD of value."""
    return binutils.bitsplit(value, 2, 32)[0]

def high(value):
    """Return higher DWORD of value."""
    return binutils.bitsplit(value, 2, 32)[1]

# -----------------------------------------------------------------------------
#  Buffer generator class.
# -----------------------------------------------------------------------------

class Buffgen(object):
    """Generates buffer images using patterns or test vector files.

    Examples
    --------

        >>> buffgen = Buffgen('MP7_MYBOARD')

        Generates a HB counter pattern.
        >>> buffgen.counter(4, 1024) # Generates a HB counter pattern.

        Generates a buffer pattern from test vector file.
        >>> buffgen.fromTestVector('sample.txt', quads = 4, frames = 1024)

    """

    def __init__(self, board = None):
        self.board = board or 'MP7_GENERIC'

    def header(self, quads):
        """Returns a list of headder lines."""
        lines = []

        # Header line No1.
        lines.append(str_board(self.board))

        # Header line No2.
        line = [" Quad/Chan", ":"]
        for quad in range(quads):
            for channel in range(4):
                line.append(str_quad(quad, channel))
        lines.append(' '.join(line).rstrip())

        # Header line No3.
        line = ["      Link", ":"]
        for i in range(quads * 4):
            line.append(str_link(i))
        lines.append(' '.join(line).rstrip())

        return lines

    def zero(self, quads = 4, frames = 1024):
        lines = []
        for frame in range(frames):
            line = []
            line.append(str_frame(frame))
            for quad in range(quads):
                for channel in range(4):
                    line.append(str_value())
            lines.append(' '.join(line))
        # Resize if needed.
        return '\n'.join(self.header(quads) + lines[:frames])

    def counter(self, quads = 4, frames = 1024):
        lines = []
        for frame in range(frames):
            line = []
            line.append(str_frame(frame))
            for quad in range(quads):
                for channel in range(4):
                    line.append(str_value(counter_value(quad, channel, frame), True))
            lines.append(' '.join(line))
        # Resize if needed.
        return '\n'.join(self.header(quads) + lines[:frames])

    def fromTestVector(self, filename, quads = 4, frames = 1024):
        lines = []
        with open(filename) as fs:
            tv = TestVector(fs)
            for i in range(len(tv.extconds())):
                if len(lines) > frames:
                    break
                # Split external conditions into DWORDS (8 x 32 bit)
                extconds = binutils.bitsplit(tv.extconds()[i], 8, 32)
                #
                # Object mapping.
                #
                mapped_values = [
                    [0,                   0,                   0,                   0,                   tv.eg(0)[i], tv.eg(6)[i],  tv.jet(0)[i], tv.jet(6)[i],  tv.tau(0)[i], tv.tau(6)[i],  tv.ett()[i],    0, extconds[0], extconds[2], extconds[4], extconds[6], ],
                    [0,                   0,                   0,                   0,                   tv.eg(1)[i], tv.eg(7)[i],  tv.jet(1)[i], tv.jet(7)[i],  tv.tau(1)[i], tv.tau(7)[i],  tv.ht()[i],     0, extconds[1], extconds[3], extconds[5], extconds[7], ],
                    [low(tv.muon(0)[i]),  low(tv.muon(2)[i]),  low(tv.muon(4)[i]),  low(tv.muon(6)[i]),  tv.eg(2)[i], tv.eg(8)[i],  tv.jet(2)[i], tv.jet(8)[i],  tv.tau(2)[i], tv.tau(8)[i],  tv.etm()[i],    0, 0,           0,           0,           0,           ],
                    [high(tv.muon(0)[i]), high(tv.muon(2)[i]), high(tv.muon(4)[i]), high(tv.muon(6)[i]), tv.eg(3)[i], tv.eg(9)[i],  tv.jet(3)[i], tv.jet(9)[i],  tv.tau(3)[i], tv.tau(9)[i],  tv.htm()[i],    0, 0,           0,           0,           0,           ],
                    [low(tv.muon(1)[i]),  low(tv.muon(3)[i]),  low(tv.muon(5)[i]),  low(tv.muon(7)[i]),  tv.eg(4)[i], tv.eg(10)[i], tv.jet(4)[i], tv.jet(10)[i], tv.tau(4)[i], tv.tau(10)[i], tv.etmhf()[i],  0, 0,           0,           0,           0,           ],
                    [high(tv.muon(1)[i]), high(tv.muon(3)[i]), high(tv.muon(5)[i]), high(tv.muon(7)[i]), tv.eg(5)[i], tv.eg(11)[i], tv.jet(5)[i], tv.jet(11)[i], tv.tau(5)[i], tv.tau(11)[i], tv.htmhf()[i],  0, 0,           0,           0,           0,           ],
                ]
                # Convert to value format.
                for ii in range(len(mapped_values)):
                    mapped_values[ii] = [str_value(value) for value in mapped_values[ii]]
                for frame in range(6):
                    line = []
                    line.append(str_frame((i * 6)+ frame))
                    line.extend(mapped_values[frame])
                    line.extend([str_value(0)] * ((quads * 4) - (len(line) - 1)))
                    lines.append(' '.join(line[:(quads * 4) + 1]))
            # Resize if needed.
            return '\n'.join(self.header(quads) + lines[:frames])

    def toTestVector(self, filename):
        tv = TestVector()
