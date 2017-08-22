#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Bernhard Arnold <bernahrd.arnold@cern.ch>
#
# Repository path   : $HeadURL$
# Last committed    : $Revision$
# Last changed by   : $Author$
# Last changed date : $Date$
#

"""Utility functions.
"""

from collections import namedtuple
import os

#
# Functions
#

def slot_number(device):
    if '.' in device:
        return int(device.split('.')[1])
    return 0

def device_type(device):
    return device.split('.')[0]

def sort_devices(devices):
    return sorted(devices, key=lambda device: slot_number(device))

def to_namedtuple(d, classname='struct'):
    """Convert a dict into a namedtuple.
    http://stackoverflow.com/questions/35898270/trying-to-make-a-dict-behave-like-a-clean-class-method-structure
    """
    if not isinstance(d, dict):
        raise ValueError("Can only convert dicts into namedtuple")
    for k,v in d.iteritems():
        if isinstance(v, dict):
            d[k] = to_namedtuple(v)
    return namedtuple(classname, d.keys())(**d)
