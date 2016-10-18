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

"""This module provides a column file reader with field formatting (like numpy)."""

__all__ = ['FileReader', '__doc__', '__version__', ]
__version__ = '$Revision$'

import csv
import re

class FileReader(object):
    """Column data file reader with field formatting (like numpy) using the csv
    reader class.

    Usage example
    -------------

    >>> f = StringIO('0001 aaa bbb ccc')
    >>> reader = FileReader(f, fields = (('index', 'd4'), ('values', 'x3', 3)))
    >>> reader.next()
    {'index' : 0, 'values' : [2730, 3003, 3276]}

    Field formatting
    ----------------

    Fields: ( (<key>, <fs>, [count, [proc]]), ... )

    Format strings (fs): "<b|o|d|x|s><chars>"

    Where 'b' stands for binary, 'o' for octal, 'd' for decimal, 'x' for hex and
    's' for string, representing a none integer value.

    *proc* can be a function or class that requires a single attribute, so the
    value is processed/casted to another type for eg.

    For example 'x16' requires a 16 digit hex value (128 bit integer).
    """

    # Integer bases for numeric values (int(value, base)).
    FORMAT_BASE = {'b' : 2, 'o' : 8, 'd' : 10, 'x' : 16, 's' : None, }
    # Regular expression for format string.
    FORMAT_REGEX = re.compile(r'([bodxs])(\d+)')

    def __init__(self, csvfile, fields, delimiter = ' ', *args, **kwds):
        """Attribute *csvfile* can be any object which supports the iterator
        protocol and returns a string each time its next() method is called -
        file objects and list objects are both suitable.
        """
        self._reader = csv.reader(csvfile, delimiter = delimiter, *args, **kwds)
        self._fields = fields
        self._comments = '!|#' # Skips lines starting with..
        self._lineno = 1

    def __iter__(self):
        return self

    def lineno(self):
        """Returns current line number."""
        return self._lineno

    def next(self):
        """Return the next row of the reader’s iterable object as a list, parsed
        according to the current field format strings.
        """
        data = {}
        items = self._reader.next()
        self._lineno += 1

        # HACK: no empty lines allowed.
        if not items:
            raise ValueError("invalid format, empty row in line {self._lineno}".format(**locals()))

        # Strip comments.
        while items[0][0:1] in self._comments:
            items = self._reader.next()
            self._lineno += 1

        for field in self._fields:
            name, base, chars, count, proc = self._fmt(field)
            values = []
	    #print "==================="
	    #print name, base, chars, count, proc

            if name in data:
                raise KeyError("multiple declaration of field '{name}' in line {self._lineno}".format(**locals()))

            for i in range(count):
                item = items.pop(0)
		#print i, item

                if len(item) != chars:
		    #print len(item)
                    raise ValueError("invalid format, field '{name}' requires '{chars}' characters in line {self._lineno}".format(**locals()))

                # Cast to integer if base is given, else store as string.
                value = int(item, self.FORMAT_BASE[base]) if base else item
                # Optional post process value with function/class proc.
                if proc:
                    value = proc(value)

                values.append(value)

            # Do not return tuple for single occurrences.
            data[name] = tuple(values) if len(values) > 1 else values[0]

        return data

    def _fsplit(self, fmtstring):
        """Split format string into tuple containing integer base and character
        count.
        """
        match = self.FORMAT_REGEX.match(fmtstring)
        if not match:
            raise ValueError("invalid format string '{fmtstring}' in line {self._lineno}".format(**locals()))
        base, chars = match.groups()
        return base, int(chars)


    def _fmt(self, field):
        """Returns field specification as tuple containing name, integer base,
        character count, and occurrence count.
        Attribute *field* must be at tuple of format (<name>, <format>[, <count>])
        """
        name = field[0]
        base, chars = self._fsplit(field[1])
        count = int(field[2]) if len(field) > 2 else 1
        proc = field[3] if len(field) > 3 else None
        return name, base, chars, count, proc

    def str_formats(self):
        """Returns string format templates."""
        templates = {}
        for field in self._fields:
            name, base, chars, count, proc = self._fmt(field)
            fill = '0' if base else ' '
            templates[name] = '{{{name}:{fill}{chars}{base}}}'.format(**locals())
        return templates

    def _row_to_str(self, row):
        """Helper, converts fetched row data to string defined representations."""
        str_formats = self.str_formats()
        for key, value in row.items():
            # Process multi entries { 'key' :  (value, value, ...) }
            if type(value) in (list, tuple):
                row[key] = [str_formats[key].format(**{key : v}) for v in value]
            # Process single entries { 'key' :  value }
            else:
                row[key] = str_formats[key].format(**{key : value})
        return row

    def read(self, lines = None):
        """Reading entire file or number of *lines* of stream and returning its
        content. Provided for convenience.
        """
        data = {}
        # Populate initial columns.
        for field in self._fields:
            key = field[0]
            if len(field) > 2:
                data[key] = [[] for _ in range(field[2])]
            else:
                data[key] = []
        for line, row in enumerate(self):
            if lines and line >= lines:
                break
            for key, values in row.items():
                if isinstance(values, list) or isinstance(values, tuple):
                    for i, value in enumerate(values):
                        data[key][i].append(value)
                else:
                    data[key].append(values)
        return data
