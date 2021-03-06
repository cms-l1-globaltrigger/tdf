# -*- coding: utf-8 -*-
#
# Copyright 2013-2017 Bernhard Arnold <bernahrd.arnold@cern.ch>
#                     Johannes Wittmann <johannes.wittmann@cern.ch>
#

"""This module provides a very basic XML menu reader making use of lmxl etree.

This class can be used for diagnostic output of algorithm params in TDF routines.

Load a menu from XML file:

>>> from xmlmenu import XmlMenu
>>> menu = XmlMenu("sample.xml")

Access menu meta information:

>>> menu.name
'L1Menu_Sample'
>>> menu.comment
'NO one expects the spanish inquisition!'

Iterate over algorithms:

>>> for algorithm in menu.algorithms:
...     print algorithm.index, algorithm.name

Filter algorithms by attributes:

>>> for module in range(menu.n_modules):
...     for algorithm in menu.algorithms.byModule(module):
...         do_something(...)

To reduce execution time it is possible to disable parsing for algorithms and/or
external signals by using flags. To read only menu meta data disable parsing:

>>> from xmlmenu import XmlMenu
>>> menu = XmlMenu("sample.xml", parse_algorithms=False, parse_externals=False)

"""

import sys, os

try:
    from lxml import etree
except ImportError:
    raise RuntimeError("package lxml is missing, please install \"python-lxml\" by using your package manager")

__all__ = [ 'XmlMenu', '__doc__' ]

def filter_first(function, sequence):
    """Retruns first match of filter() result or None if nothing was found."""
    return list(filter(function, sequence) or [None])[0]

def get_xpath(elem, path, fmt=str, default=None):
    """Easy access using etree elem xpath method. Returns value of 'default' if
    element was not found (default is 'None').
    """
    results = elem.xpath('{path}/text()'.format(path=path))
    if results:
        return fmt(results[0])
    return default

def fast_iter(context, func, *args, **kwargs):
    """Fast XML iterator for huge XML files.
    http://lxml.de/parsing.html#modifying-the-tree
    Based on Liza Daly's fast_iter
    http://www.ibm.com/developerworks/xml/library/x-hiperfparse/
    See also http://effbot.org/zone/element-iterparse.htm
    """
    for event, elem in context:
        func(elem, *args, **kwargs)
        # It's safe to call clear() here because no descendants will be
        # accessed
        elem.clear()
        # Also eliminate now-empty references from the root node to elem
        for ancestor in elem.xpath('ancestor-or-self::*'):
            while ancestor.getprevious() is not None:
                del ancestor.getparent()[0]
    del context

class Algorithm(object):
    """Algorithm container class."""
    def __init__(self, index, name, expression, module_id=0, module_index=0, comment=None):
        self.index = index
        self.name = name
        self.expression = expression
        self.module_id = module_id
        self.module_index = module_index
        self.comment = comment or ""
    def __repr__(self):
        return "Algorithm(index={self.index}, " \
               "name=\"{self.name}\", " \
               "expression=\"{self.expression}\", " \
               "module(id={self.module_id}, index={self.module_index}))".format(**locals())

class ExternalSignal(object):
    """External signal container class."""
    def __init__(self, name, system, cable, channel, description=None, label=None):
        self.name = name
        self.system = system
        self.cable = cable
        self.channel = channel
        self.description = description or ""
        self.label = label or ""
    def __repr__(self):
        return \
            "ExternalSignal(name=\"{self.name}\", " \
            "system=\"{self.system}\", " \
            "cable={self.cable}, " \
            "channel={self.channel})".format(**locals())

class AlgorithmContainer(list):
    """List container with extended lookup methods for content."""
    def byIndex(self, index):
        """Retruns algorithm by index or None if not found."""
        return filter_first(lambda algorithm: algorithm.index == index, self)
    def byModuleId(self, id):
        """Returns list of algorithms assigned to module id or empty list if none found."""
        return filter(lambda algorithm: algorithm.module_id == id, self)
    def byModuleIndex(self, index):
        """Returns list of algorithms assigned to module index or empty list if none found."""
        return filter(lambda algorithm: algorithm.module_index == index, self)
    def byName(self, name):
        """Retruns algorithm by name or None if not found."""
        return filter_first(lambda algorithm: algorithm.name == name, self)

class ExternalSignalContainer(list):
    """External signal list container with extended lookup methods."""
    def byName(self, name):
        """Retruns external signal by name or None if not found."""
        return filter_first(lambda signal: signal.name == name, self)
    def bySystem(self, system):
        """Returns list of external signals assigned to system or empty list if none found."""
        return filter(lambda signal: signal.system == system, self)
    def byCable(self, cable):
        """Returns list of external signals assigned to cable or empty list if none found."""
        return filter(lambda signal: signal.cable == cable, self)

class XmlMenu(object):
    """Container holding some information of the XML menu.
    Menu attributes:
    *filename* holds the filename the menu was read from
    *name* is the menu's name
    *uuid_menu* is the menu's UUID
    *uuid_firmware* is the menu's firmware UUID (set by the VHDL producer)
    *algorithms* holds an instance of type AlgorithmContainer permitting a
    convenient access to the loaded algorithms
    *externals* holds an instance of type ExternalSignalContainer permitting a
    convenient access to the loaded external signals.

    Example:
    >>> menu = XmlMenu("sample.xml")
    >>> menu.name
    'L1Menu_Sample'
    >>> menu.algorithms.byModule(2)
    [...]
    """

    def __init__(self, filename=None, parse_algorithms=True, parse_externals=True):
        self.filename = None
        self.name = None
        self.uuid_menu = None
        self.uuid_firmware = None
        self.grammar_version = ""
        self.is_valid = False
        self.is_obsolete = False
        self.n_modules = 0
        self.comment = ""
        self.ext_signal_set = ""
        self.algorithms = AlgorithmContainer()
        self.externals = ExternalSignalContainer()
        # Override parinsing options
        self.parse_algorithms = parse_algorithms
        self.parse_externals = parse_externals
        if filename: self.read(filename)

    def read(self, filename):
        """Read XML from file and parse its content."""
        self.filename = os.path.abspath(filename)
        self.algorithms = AlgorithmContainer()
        self.externals = ExternalSignalContainer()
        with open(self.filename, 'rb') as fp:
            # Access meta data
            context = etree.parse(fp)
            self.name = get_xpath(context, 'name')
            self.uuid_menu = get_xpath(context, 'uuid_menu')
            self.uuid_firmware = get_xpath(context, 'uuid_firmware')
            self.grammar_version = get_xpath(context, 'grammar_version')
            self.is_valid = get_xpath(context, 'is_valid', bool)
            self.is_obsolete = get_xpath(context, 'is_obsolete', bool)
            self.n_modules = get_xpath(context, 'n_modules', int)
            self.comment = get_xpath(context, 'comment', default="")
            self.ext_signal_set = get_xpath(context, 'ext_signal_set/name', default="")
            if self.parse_algorithms:
                # Access list of algorithms
                fp.seek(0) # Seek begin of file
                context = etree.iterparse(fp, tag='algorithm')
                fast_iter(context, self._load_algorithm)
            if self.parse_externals:
                # Access list of external signals
                fp.seek(0) # Seek begin of file
                context = etree.iterparse(fp, tag='ext_signal')
                fast_iter(context, self._load_external)

    def _load_algorithm(self, elem):
        """Fetch information from an algorithm tag and appends it to the list of algorithms."""
        name = get_xpath(elem, 'name')
        index = get_xpath(elem, 'index', int)
        expression = get_xpath(elem, 'expression')
        module_id = get_xpath(elem, 'module_id', int)
        module_index = get_xpath(elem, 'module_index', int)
        comment = get_xpath(elem, 'comment', default="")
        algorithm = Algorithm(index, name, expression, module_id, module_index, comment)
        self.algorithms.append(algorithm)

    def _load_external(self, elem):
        """Fetch information from an algorithm tag and appends it to the list of algorithms."""
        name = get_xpath(elem, 'name')
        system = get_xpath(elem, 'system')
        cable = get_xpath(elem, 'cable', int)
        channel = get_xpath(elem, 'channel', int)
        description = get_xpath(elem, 'description', default="")
        label = get_xpath(elem, 'label', default="")
        external = ExternalSignal(name, system, cable, channel, description, label)
        self.externals.append(external)

if __name__ == '__main__':
    """Basic unittest..."""

    import logging
    logging.getLogger().setLevel(logging.DEBUG)

    filename = sys.argv[1]

    import time
    t1 = time.time()
    menu = XmlMenu(filename)
    t2 = time.time()

    logging.info("menu.filename      : \"%s\"", menu.filename)
    logging.info("menu.name          : \"%s\"", menu.name)
    logging.info("menu.uuid_menu     : %s", menu.uuid_menu)
    logging.info("menu.uuid_firmware : %s", menu.uuid_firmware)
    logging.info("menu.n_modules     : %s", menu.n_modules)
    logging.info("menu.is_valid      : %s", menu.is_valid)
    logging.info("menu.is_obsolete   : %s", menu.is_obsolete)
    if menu.comment:
        logging.info("menu.comment       : \"%s\"", menu.comment)

    logging.info("menu.ext_signal_set : \"%s\"", menu.ext_signal_set)

    for algorithm in menu.algorithms:
        logging.info("algorithm.name         : \"%s\"", algorithm.name)
        logging.info("algorithm.index        : %s", algorithm.index)
        logging.info("algorithm.module_id    : %s", algorithm.module_id)
        logging.info("algorithm.module_index : %s", algorithm.module_index)
        if algorithm.comment:
            logging.info("algorithm.comment      : \"%s\"", algorithm.comment)

    for external in menu.externals:
        logging.info("ext_signal.name        : \"%s\"", external.name)
        logging.info("ext_signal.system      : \"%s\"", external.system)
        logging.info("ext_signal.cable       : %s", external.cable)
        logging.info("ext_signal.channel     : %s", external.channel)
        if external.label:
            logging.info("ext_signal.label       : \"%s\"", external.label)
        if external.description:
            logging.info("ext_signal.description : \"%s\"", external.description)

    logging.info("XML parsed in %.03f seconds.", (t2 - t1))
