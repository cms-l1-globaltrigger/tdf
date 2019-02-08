#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Copyright 2013-2017 Bernhard Arnold <bernahrd.arnold@cern.ch>
#

"""
TTY colors and control sequences.



Example:

>>> from tdf.core import tty
>>> style = tty.White + tty.BackgroundBlue + tty.Bold
>>> print style, "NO-body expects the Spanish Inquisition!", tty.Reset

"""

import sys

class CSICode(object):
    """CSI code for TTY."""

    PrivateMode = '\033['
    TrailingIntermediate = ''

    def __init__(self, sequence, description=None, stream=sys.stdout):
        self.sequence = sequence if isinstance(sequence, list) else [sequence]
        self.description = description or ""
        self.stream = stream

    def __add__(self, other):
        """Add two CSI codes."""
        assert isinstance(other, CSICode)
        sequence = self.sequence + other.sequence
        description = "{0}, {1}".format(self.description, other.description)
        return self.__class__(sequence, description, self.stream)

    def __str__(self):
        """Print control sequences only on TTYs."""
        if self.stream.isatty():
            sequence = [format(code) for code in self.sequence]
            return '{0}{1}{2}'.format(self.PrivateMode, ';'.join(sequence), self.TrailingIntermediate)
        return ''

class ANSICtrlCode(CSICode):
    """ANSI control code."""

    def __init__(self, n, trailing, description=None, stream=sys.stdout):
        super(ANSICtrlCode, self).__init__(n, description, stream)
        self.TrailingIntermediate = trailing

class SGRParam(CSICode):
    """SGR (Select Graphic Rendition) parameter."""

    TrailingIntermediate = 'm'

# ANSI control codes
def CursorUp(n): return ANSICtrlCode(n, 'A', "CUU cursor up {0}".format(n))
def CursorDown(n): return ANSICtrlCode(n, 'B', "CUD cursor down {0}".format(n))
def CursorForward(n): return ANSICtrlCode(n, 'C', "CUF cursor forward {0}".format(n))
def CursorBack(n): return ANSICtrlCode(n, 'D', "CUB cursor back {0}".format(n))
def CursorNextLine(n): return ANSICtrlCode(n, 'E', "CNL cursor next line(s) {0}".format(n))
def CursorPreviousLine(n): return ANSICtrlCode(n, 'F', "CPL cursor previous line(s) {0}".format(n))
def CursorHorizontalAbsolute(n): return ANSICtrlCode(n, 'G', "CHA cursor to column {0}".format(n))

# SGR modifiers
Reset = SGRParam(0, "reset")
Bold = SGRParam(1, "bold")
Faint = SGRParam(2, "faint")
Italic = SGRParam(3, "italic")
Underline = SGRParam(4, "underline")
BlinkSlow = SGRParam(5, "blink slow")
BlinkFast = SGRParam(6, "blink fast")
Inverse = SGRParam(7, "inverse")
Conceal = SGRParam(8, "conceal")
CrossedOut = SGRParam(9, "crossed out")

# SGR forground colors
Black = SGRParam(30, "foreground black")
Red = SGRParam(31, "foreground red")
Green = SGRParam(32, "foreground green")
Yellow = SGRParam(33, "foreground yellow")
Blue = SGRParam(34, "foreground blue")
Magenta = SGRParam(35, "foreground magenta")
Cyan = SGRParam(36, "foreground cyan")
White = SGRParam(37, "foreground white")
Extended = SGRParam(38, "foreground extended (rgb)")
Default = SGRParam(39, "foreground default")

def ColorCode(n): return Extended + SGRParam([5, n]) # 0...255
def RGB(r, g, b): return Extended + SGRParam([2, r, g, b])

# SGR background colors
BackgroundBlack = SGRParam(40, "background black")
BackgroundRed = SGRParam(41, "background red")
BackgroundGreen = SGRParam(42, "background green")
BackgroundYellow = SGRParam(43, "background yellow")
BackgroundBlue = SGRParam(44, "background blue")
BackgroundMagenta = SGRParam(45, "background magenta")
BackgroundCyan = SGRParam(46, "background cyan")
BackgroundWhite = SGRParam(47, "background white")
BackgroundExtended = SGRParam(48, "background extended (rgb)")
BackgroundDefault = SGRParam(49, "background default")

def BackgroundColorCode(n): return BackgroundExtended + SGRParam([5, n]) # 0...255
def BackgroundRGB(r, g, b): return BackgroundExtended + SGRParam([2, r, g, b])

# aixterm forground colors (not in standard)
HighBlack = SGRParam(90, "high intensity foreground black (aixterm)")
HighRed = SGRParam(91, "high intensity foreground red (aixterm)")
HighGreen = SGRParam(92, "high intensity foreground green (aixterm)")
HighYellow = SGRParam(93, "high intensity foreground yellow (aixterm)")
HighBlue = SGRParam(94, "high intensity foreground blue (aixterm)")
HighMagenta = SGRParam(95, "high intensity foreground magenta (aixterm)")
HighCyan = SGRParam(96, "high intensity foreground cyan (aixterm)")
HighWhite = SGRParam(97, "high intensity foreground white (aixterm)")

# aixterm ackground colors (not in standard)
HighBackgroundBlack = SGRParam(100, "high intensity background black (aixterm)")
HighBackgroundRed = SGRParam(101, "high intensity background red (aixterm)")
HighBackgroundGreen = SGRParam(102, "high intensity background green (aixterm)")
HighBackgroundYellow = SGRParam(103, "high intensity background yellow (aixterm)")
HighBackgroundBlue = SGRParam(104, "high intensity background blue (aixterm)")
HighBackgroundMagenta = SGRParam(105, "high intensity background magenta (aixterm)")
HighBackgroundCyan = SGRParam(106, "high intensity background cyan (aixterm)")
HighBackgroundWhite = SGRParam(107, "high intensity background white (aixterm)")

Colors = (
    Black,
    Red,
    Green,
    Yellow,
    Blue,
    Magenta,
    Cyan,
    White,
    Default,
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
    BackgroundDefault,
)

HighColors = (
    HighBlack,
    HighRed,
    HighGreen,
    HighYellow,
    HighBlue,
    HighMagenta,
    HighCyan,
    HighWhite,
)

HighBackgroundColors = (
    HighBackgroundBlack,
    HighBackgroundRed,
    HighBackgroundGreen,
    HighBackgroundYellow,
    HighBackgroundBlue,
    HighBackgroundMagenta,
    HighBackgroundCyan,
    HighBackgroundWhite,
)

if __name__ == '__main__':

    for color in Colors:
            print color, color.description, Reset

    for color in Colors:
        for background in BackgroundColors:
            style = color + background
            print style, style.description, Reset

    for color in HighColors:
            print color, color.description, Reset

    for color in HighColors:
        for background in HighBackgroundColors:
            style = color + background
            print style, style.description, Reset

    print " ...bar", CursorHorizontalAbsolute(1), "foo"

    for r in range(0, 256, 25):
        for g in range(0, 256, 25):
            for b in range(0, 256, 25):
                print "{}{}{}".format(RGB(r, g, b), "X", Reset),
            print
