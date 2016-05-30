# -*- coding: utf-8 -*-
#
# Copyright 2013-2016 Bernhard Arnold <bernahrd.arnold@cern.ch>
#                     Johannes Wittmann <johannes.wittmann@cern.ch>
#
# Repository path   : $HeadURL$
# Last committed    : $Revision$
# Last changed by   : $Author$
# Last changed date : $Date$
#

"""This module provides a very basic XML menu reader making use of lmxl etree.
This class can be used for diagnostic output of algorithm params in TDF routines.
"""

import sys, os
from settings import TDF

try:
    from lxml import etree
except ImportError:
    raise RuntimeError("package lxml is missing, run \"sudo yum install python-lxml\" to install it")

__all__ = [ 'XmlMenu', '__doc__', '__version__' ]
__version__ = '$Revision$'

def fast_iter(context, func, *args, **kwargs):
    """
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
    def __init__(self, index, name, expression, module_id=0, module_index=0):
        self.index = index
        self.name = name
        self.expression = expression
        self.module_id = module_id
        self.module_index = module_index
    def __repr__(self):
        return "Algorithm(index={self.index}, " \
               "name=\"{self.name}\", " \
               "expression=\"{self.expression}\", " \
               "module(id={self.module_id}, index={self.module_index}))".format(**locals())

class AlgorithmContainer(list):
    """List container with extended lookup methods."""
    def byIndex(self, index):
        return (filter(lambda algorithm: algorithm.index == index, self) or [None])[0]
    def byModuleId(self, id):
        return (filter(lambda algorithm: algorithm.module_id == id, self) or [None])[0]
    def byModuleIndex(self, index):
        return (filter(lambda algorithm: algorithm.module_index == index, self) or [None])[0]
    def byName(self, name):
        return (filter(lambda algorithm: algorithm.name == name, self) or [None])[0]

class XmlMenu(object):
    """Container holding some information of the XML menu.
    Menu attributes:
    *filename* holds the filename the menu was read from
    *name* is the menu's name
    *uuid_menu* is the menu's UUID
    *uuid_firmware* is the menu's firmware UUID (set by the VHDL producer)
    *algorithms* holds an instance of type AlgorithmContainer permitting a
    convenient access to the loaded algorithms.
    """

    def __init__(self, filename = None):
        self.filename = None
        self.name = None
        self.uuid_menu = None
        self.uuid_firmware = None
        self.algorithms = AlgorithmContainer()
        if filename: self.read(filename)

    def read(self, filename):
        self.filename = os.path.abspath(filename)
        self.algorithms = AlgorithmContainer()
        with open(self.filename, 'rb') as fp:
            # Access static elements
            context = etree.parse(fp)
            self.name = context.xpath('name/text()')[0]
            self.uuid_menu = context.xpath('uuid_menu/text()')[0]
            self.uuid_firmware = context.xpath('uuid_firmware/text()')[0]
            # Access list of algorithms
            fp.seek(0)
            context = etree.iterparse(fp, tag='algorithm')
            fast_iter(context, self._read_algorithm)

    def _read_algorithm(self, elem):
        """Fetch information from an algorithm tag and appends it to the list of algorithms."""
        def get(path, fmt=str):
            """Easy access using etree elem xpath method."""
            return fmt(elem.xpath('{path}/text()'.format(path=path))[0])
        name = get('name')
        index = get('index', int)
        expression = get('expression')
        module_id = get('module_id', int)
        module_index = get('module_index', int)
        algorithm = Algorithm(index, name, expression, module_id, module_index)
        self.algorithms.append(algorithm)
