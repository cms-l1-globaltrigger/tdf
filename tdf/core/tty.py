#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Copyright 2013-2017 Bernhard Arnold <bernahrd.arnold@cern.ch>
#
# Repository path   : $HeadURL: https://svn.cern.ch/reps/cactus/trunk/cactusprojects/ugt/tdf/tdf/core/core.py $
# Last committed    : $Revision: 49552 $
# Last changed by   : $Author: arnold $
# Last changed date : $Date: 2017-08-22 16:22:41 +0200 (Tue, 22 Aug 2017) $
#

"""
TTY colors and control sequences.

Example:

>>> from tdf.core import tty
>>> style = tty.White + tty.BackgroundBlue + tty.Bold
>>> print style, "NO-body expects the Spanish Inquisition!", tty.Reset

"""

import sys

class TTYCtrlSeq(object):
    """TTY control sequence."""

    TTYCtrlSeqTemplate = '\033[{0}m'

    def __init__(self, sequence, description=None, stream=sys.stdout):
        self.sequence = sequence if isinstance(sequence, list) else [sequence]
        self.description = description or ""
        self.stream = stream

    def __add__(self, other):
        """Add two control sequences."""
        assert isinstance(other, TTYCtrlSeq)
        sequence = self.sequence + other.sequence
        description = "{0}, {1}".format(self.description, other.description)
        return TTYCtrlSeq(sequence, description, self.stream)

    def __str__(self):
        """Print control sequences only on TTYs."""
        if self.stream.isatty():
            sequence = [format(code) for code in self.sequence]
            return self.TTYCtrlSeqTemplate.format(';'.join(sequence))
        return ''

# Modifiers
Reset = TTYCtrlSeq(0, "reset")
Bold = TTYCtrlSeq(1, "bold")
Dark = TTYCtrlSeq(2, "dark")
Italic = TTYCtrlSeq(3, "italic")
Underline = TTYCtrlSeq(4, "underline")
Invert = TTYCtrlSeq(4, "invert")
Hidden = TTYCtrlSeq(8, "hidden")
Strikethrough = TTYCtrlSeq(8, "strikethrough")

# Forground colors
Black = TTYCtrlSeq(30, "foreground black")
Red = TTYCtrlSeq(31, "foreground red")
Green = TTYCtrlSeq(32, "foreground green")
Yellow = TTYCtrlSeq(33, "foreground yellow")
Blue = TTYCtrlSeq(34, "foreground blue")
Magenta = TTYCtrlSeq(35, "foreground magenta")
Cyan = TTYCtrlSeq(36, "foreground cyan")
White = TTYCtrlSeq(37, "foreground white")
Gray = TTYCtrlSeq(38, "foreground gray")

# backgroudn colors
BackgroundBlack = TTYCtrlSeq(40, "background black")
BackgroundRed = TTYCtrlSeq(41, "background red")
BackgroundGreen = TTYCtrlSeq(42, "background green")
BackgroundYellow = TTYCtrlSeq(43, "background yellow")
BackgroundBlue = TTYCtrlSeq(44, "background blue")
BackgroundMagenta = TTYCtrlSeq(45, "background magenta")
BackgroundCyan = TTYCtrlSeq(46, "background cyan")
BackgroundWhite = TTYCtrlSeq(47, "background white")
BackgroundGray = TTYCtrlSeq(48, "background gray")

Colors = (
    Black,
    Red,
    Green,
    Yellow,
    Blue,
    Magenta,
    Cyan,
    White,
    Gray,
)

BackgroundColors = (
    BackgroundBlack,
    BackgroundRed,
    BackgroundGreen,
    BackgroundYellow,
    BackgroundBlue,
    BackgroundMagenta,
    BackgroundCyan,
    BackgroundWhite,
    BackgroundGray,
)

if __name__ == '__main__':

    for color in Colors:
            print color, color.description, Reset

    for color in Colors:
        for background in BackgroundColors:
            style = color + background
            print style, style.description, Reset
