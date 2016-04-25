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

""" code review required
"""

from tdf.core import TDF
from tdf.core import toolbox
from tdf.core import logger
import os

# -----------------------------------------------------------------------------
#  Script file runner.
# -----------------------------------------------------------------------------

class BaseScriptRunner(object):

    script_extension = '.py'
    """Script extension for routines and unittests."""

class ScriptRunner(BaseScriptRunner):

    def __init__(self, api):
        """Core is an TDF core API object used to execute the commands."""
        self.success = True
        self.recursion_depth = 0
        self.report = []
        self.core_api = {
            'read': api.read,
            'write': api.write,
            'blockread': api.blockread,
            'blockwrite': api.blockwrite,
            'configure': api.configure,
            'dump': api.dump,
            'load': api.load,
            'clear': api.clear,
            'wait': api.wait,
            'compare': api.compare,
            'mp7butler': api.mp7butler,
            'buffgen': api.buffgen,
            'TDF_INFO': logger.info,
            'TDF_WARNING': logger.warning,
            'TDF_ERROR': logger.error,
            'TDF_CRITICAL': logger.critical,
        }

    def run_unittest(self, device, test):
        logger.info("running unittest", test, "on device", device)
        self.recursion_depth += 1
        root_dir = TDF.ROOT_DIR
        # Construct absolute unittest filename.
        filename = ''.join((test, self.script_extension))
        filename = os.path.join(TDF.UNITTEST_DIR, toolbox.device_type(device), filename)
        base_msg = " => {test} on {device}".format(**locals())
        global_vars = {
            'TDF': TDF,
            'TDF_NAME': test,
            'TDF_FILENAME': filename,
            'TDF_ARGS': [],
            'TDF_DEVICE': device,
            'run_unittest': self.run_unittest,
            'run_routine': self.run_routine,
        }
        global_vars.update(self.core_api)
        try:
            execfile(filename, global_vars)
        except AssertionError, message:
            state = "[\033[31mFAILED\033[0m]"
            self.report.append("{base_msg:<50} {state}".format(**locals()))
            self.report.append(" *** {message}".format(**locals()))
            self.success = False
        else:
            if not self.success and self.recursion_depth <= 1:
                state = "[\033[31mFAILED\033[0m]"
                self.report.append("{base_msg:<50} {state}".format(**locals()))
                self.report.append(" *** one or more subcalls failed".format(**locals()))
            else:
                state = "[  \033[32mOK\033[0m  ]"
                self.report.append("{base_msg:<50} {state}".format(**locals()))
        self.recursion_depth -= 1
        if self.recursion_depth < 1:
            print "\n".join(self.report)
            self.report = []
        return self.success

    def run_routine(self, name, *args):
        logger.info("running routine", name, *args)
        self.recursion_depth += 1
        # Construct absolute routine filename.
        filename = ''.join((name, self.script_extension))
        filename = os.path.join(TDF.ROUTINES_DIR, filename)
        global_vars = {
            'TDF': TDF,
            'TDF_NAME': name,
            'TDF_FILENAME': filename,
            'TDF_ARGS': args,
            'run_unittest': self.run_unittest,
            'run_routine': self.run_routine,
        }
        global_vars.update(self.core_api)
        try:
            execfile(filename, global_vars)
        except:
            self.success = False
            self.recursion_depth -= 1
            raise
        self.recursion_depth -= 1
        return self.success
