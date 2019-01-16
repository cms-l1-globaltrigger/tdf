#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Copyright 2013-2015 Bernhard Arnold <bernhard.arnold@cern.ch>
#

"""This module contains classes for translating values to formatted strings
defined in the uHAL address table using an item's 'type' parameter.

  '<node id="timestamp" ... parameters="type=timestamp"/>'
  can use ItemTranslator.tr_timestamp()

"""

from tdf.core import TDF
from tdf.core import binutils
from tdf.extern import yaml
import datetime
import os

__all__ = ['ItemTranslator', 'OptItemTranslator', '__doc__', ]

ENUMS_FILENAME = os.path.join(TDF.SETTINGS_DIR, 'enumerations.yml')

class BaseTranslator(object):
    """Base translator class implementing a translator method call-by-name.
    """

    tr_prefix = 'tr_'
    """Translator attributes must start with the prefix."""

    def get_translator(self, tr_type):
        """Returns translator method by *tr_type* name. Returns None if no
        translator of *tr_type* defined.
        """
        tr_name = '{self.tr_prefix}{tr_type}'.format(**locals())
        if hasattr(self, tr_name):
            return getattr(self, tr_name)

class BaseItemTranslator(BaseTranslator):
    """Base traslator vor uHAL item values.
    """

    type_key = 'type'
    """Type key used in the uHAL address table items's paramters list."""

    tr_type_default = 'default'
    """Default translator to be called."""

    enumerations_filename = os.path.join(TDF.SETTINGS_DIR, 'enumerations.yml')
    """Path to YAML enumerations configuration file."""

    def __init__(self):
        self.enumerations = {}
        if os.path.isfile(ENUMS_FILENAME):
            # Note: take care, yaml.load() returns `None' if opened file/string is empty!
            self.enumerations = yaml.load(open(self.enumerations_filename).read()) or {}

    def translate(self, node, values):
        """Translate by *node* type. Define methods named tr_<type> to extend
        type translations. Attribute *values* is a list of values to be passed
        to the translatior method.
        """
        if isinstance(values, int):
            values = [values, ]
        values = [binutils.integer(value) for value in values]
        params = node.getParameters()
        tr_type = params.setdefault(self.type_key, self.tr_type_default)
        # Enumerations.
        enums = self.get_enumeration(tr_type)
        if values[0] in enums.keys():
            return enums[values[0]]
        # Use method to convert values.
        return (self.get_translator(tr_type) or self.get_translator(self.tr_type_default))(node, values)

    def get_enumeration(self, tr_type):
        """Lookup enumerations for translator type. Returns dictionary indexed
        by integer values, eg. {0x0: 'UNDEFINDED'}.
        """
        if tr_type in self.enumerations.keys():
            # Cast values to integer and return dictionary.
            return dict([(binutils.integer(value), key) for key, value in self.enumerations.get(tr_type).items()])
        return {}

    def tr_default(self, node, values):
        """Default translator used if requested translator does not exist."""
        if node.getSize() > 1:
            return "\n".join(('0x{value:08x}'.format(**locals()) for value in values))
        return '0x{values[0]:08x}'.format(**locals())

class ItemTranslator(BaseItemTranslator):
    """Traslator vor uHAL item values. An item type can be assigned adding a
    'type' entry to the item's parameters list in the address table.
    """

    def tr_uuid(self, node, values):
        """Translate value list to UUID."""
        return binutils.uuiddecode(values)

    def tr_string(self, node, values):
        """Translate value list to string."""
        if not type(values) in (tuple, list):
            values = [values, ]
        return binutils.hexdecode(values)

    def tr_version(self, node, values):
        """Translate value to version number."""
        return '{2}.{1}.{0}'.format(*binutils.bitsplit(values[0], n=3, width=8))

    def tr_timestamp(self, node, values):
        """Translate value from UNIX timestamp to ISO represnatation."""
        return datetime.datetime.fromtimestamp(values[0]).isoformat()

    def tr_signed(self, node, values):
        """Translate value to signed integer."""
        return format(values[0], 'd')

    def tr_boolean(self, node, values):
        """Translate value to boolean."""
        return 'TRUE' if values[0] else 'FALSE'

    def tr_hex(self, node, values):
        """Translate value to hex value."""
        return '0x{0:08x}'.format(values[0])
