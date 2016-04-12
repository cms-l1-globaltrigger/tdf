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

"""
Configuration device reader.

Format of configuration files:
------------------------------

<full.item.name> <value>

Values can be any values or boolean expressions. Using value base prefixes like
0x42 or 0b10010011 is possible.

Empty lines and lines beginning with #, ! or * (comments) are ignored.

"""

__all__ = ['ConfigFileReader', '__doc__', '__version__', ]
__version__ = '$Revision$'

class ConfigFileReader(object):
    """Configuration file reader. Throws runtime errors.

    Usage example
    -------------

    >>> config = ConfigFileReader("sample.cfg")
    >>> for name, value in config.items():
    ....    print name, value

    """

    def __init__(self, filename = None):
        self._data = []
        if filename:
            self.read(filename)

    def read(self, filename):
        """Read (name, value) pairs from configuration file. Configurations are
        handled as sequences in given order.
        """
        with open(filename, 'rb') as configfile:
            for i, line in enumerate(configfile):
                line = line.strip() # Strip newlines from line.
                lineno = i + 1 # Define line number.
                if not len(line): continue # Skip empty lines.
                if line[0] in "#!*": continue # skip comments.
                try:
                    name, value = line.split()
                    self._data.append( (name, self.convert(value)) ) # Auto convert value.
                except (ValueError, RuntimeError):
                    raise RuntimeError("parsing error in file {filename} on line {lineno}\n*** {line}".format(**locals()))

    def convert(self, value):
        """Auto convert different types of values."""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            if value.lower() == 'true':
                return True
            if value.lower() == 'false':
                return False
            if value.lower().startswith('0b'):
                return int(value, 2)
            if value.lower().startswith('0o'):
                return int(value, 8)
            if value.lower().startswith('0x'):
                return int(value, 16)
            return int(value, 10)
        raise ValueError()

    def get(self, name):
        """Retrun values for item *name*."""
        return filter(lambda pair: pair[0] == name, self._data)

    def items(self):
        """Return (name, value) pairs of all items."""
        return [pair for pair in self._data]
