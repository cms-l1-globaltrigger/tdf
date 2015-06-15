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

from tdf.core import TDF
import uhal
from tdf.extern import yaml
import os
from tdf.core.types import *

#
# Functions
#

#
# Prototypes
#

def slot_number(device):
    if '.' in device:
        return int(device.split('.')[1])
    return 0

def device_type(device):
    return device.split('.')[0]

def sort_devices(devices):
    return sorted(devices, key = lambda device: slot_number(device))

STATES = enum('UNKNOWN_DEVICE', 'DEVICE_PRESENT', 'DEVICE_NOT_CONFIGURED', 'DEVICE_NOT_PRESENT')

def cratescan(tdf):

    chk_present = 'chk_present'
    chk_configured = 'chk_configured'

    class DeviceState(object):
        def __init__(self, device, state):
            self._device = device
            self._state = state
        @property
        def device(self): return self._device
        @property
        def state(self): return self._state
        @property
        def state_str(self): return STATES.reverse_mapping[self.state]
        @property
        def slot(self): return slot_number(self.device)
        @property
        def type(self): return device_type(self.device)

    config = yaml.load(open(os.path.join(TDF.SETTINGS_DIR, 'cratescan.yml')).read())

    states = []

    for device in sort_devices(tdf.connectionManager.getDevices()):
        state = STATES.UNKNOWN_DEVICE
        for device_type_ in config.keys():
            if device_type(device) == device_type_:
                if chk_present in config.get(device_type_):
                    try:
                        tdf.read(device, config.get(device_type_).get(chk_present))
                        state = STATES.DEVICE_PRESENT
                        if chk_configured in config.get(device_type_):
                            try:
                                tdf.read(device, config.get(device_type_).get(chk_configured))
                            except uhal._core.exception:
                                state = STATES.DEVICE_NOT_CONFIGURED
                    except uhal._core.exception:
                        state = STATES.DEVICE_NOT_PRESENT
                break
        states.append(DeviceState(device, state))
    return states

#print "Crate scan..."
#for state in states:
    #str_state = STATES.reverse_mapping[state.state]
    #print "device={state.device:<18} slot={state.slot:<3} type={state.type:<15} state={str_state:<21} ({state.state})".format(**locals())
