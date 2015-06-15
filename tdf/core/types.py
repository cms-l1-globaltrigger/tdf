#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Bernhard Arnold <bernahrd.arnold@cern.ch>
#
# Repository path   : $HeadURL: svn://heros.hephy.oeaw.ac.at/GlobalTriggerUpgrade/software/tdf/trunk/lib/tdf/core/api.py $
# Last committed    : $Revision: 3752 $
# Last changed by   : $Author: arnold $
# Last changed date : $Date: 2015-02-13 16:36:26 +0100 (Fri, 13 Feb 2015) $
#

"""
#NOTE clean up
"""

import pprint

#
# Type factories
#

def enum(*sequential, **named):
    """Enumeration factory."""
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)

def struct(**kwargs):
    """Reserved keywords are: get_keys"""
    class struct_t(object):
        def __repr__(self): return pprint.pformat(self.__dict__)
    result = struct_t()
    for key, value in kwargs.items():
        if isinstance(value, dict):
            setattr(result, key, struct(**value))
        else:
            setattr(result, key, value)
    return result
