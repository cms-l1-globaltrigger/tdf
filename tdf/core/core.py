#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Bernhard Arnold <bernahrd.arnold@cern.ch>
#
# Repository path   : $HeadURL: svn://heros.hephy.oeaw.ac.at/GlobalTriggerUpgrade/software/tdf/trunk/tdf/core/core.py $
# Last committed    : $Revision: 4010 $
# Last changed by   : $Author: arnold $
# Last changed date : $Date: 2015-05-28 16:50:01 +0200 (Thu, 28 May 2015) $
#

"""
"""

import uhal
import subprocess
import logging
import inspect
import tempfile
import time
import sys, os

from tdf.core.settings import TDF
from tdf.core import binutils
from tdf.core.cfgreader import ConfigFileReader
from tdf.core.translator import ItemTranslator
from tdf.extcond.images import *
from tdf.mp7.images import *
from tdf.core.images import GenericMemoryImage
from tdf.mp7.buffgen import Buffgen

from tdf.core.testvector import TestVector
from tdf.core.filereader import FileReader
from tdf.core.binutils import charcount
from tdf.core.scripts import ScriptRunner
from tdf.core.logger import *

__all__ = ['TDFCore', '__doc__', '__version__', ]
__version__ = '$Revision: 4010 $'

MP7_EXECUTABLE = 'mp7butler.py'
"""Executable name for the MP7 butler software."""

def DEBUG_API(frame = inspect.currentframe()):
    """Inspect function call and pass details to debug logger.
    >>> DEBUG_API(inspect.currentframe())
    """
    cls = frame.f_locals['self'].__class__.__name__
    attr = inspect.getframeinfo(frame)[2]
    args, _, _, values = inspect.getargvalues(frame)
    arglist = ', '.join(("{0}='{1}'".format(arg, values[arg]) for arg in args if arg != 'self'))
    debug("{cls}.{attr}( {arglist} )".format(**locals()))

def toImage(node):
    """Factory convert node to empty memory image object."""
    parameters = node.getParameters()
    if 'class' in parameters.keys():
        class_ = parameters['class']
        if class_ in globals().keys():
            image = globals()[class_]()
            return image
    image = GenericMemoryImage(node.getSize())
    return image

class TDFCore(object):
    """TDF core API class."""

    def __init__(self, connections, verbose = 0):
        DEBUG_API(inspect.currentframe())
        self.connections = connections
        self.connectionManager = uhal.ConnectionManager(connections)
        self.translator = ItemTranslator()
        self.verbose = verbose
        self.stdout = sys.stdout

        info("TDF.ROOT_DIR:", TDF.ROOT_DIR)
        info("TDF.L1MENU_DIR:", TDF.L1MENU_DIR)
        info("TDF.MP7_ROOT_DIR:", TDF.MP7_ROOT_DIR)
        info("XML connections file:", self.connections)

    def _getNode(self, device, item):
        device = self.connectionManager.getDevice(device)
        return device.getNode(item)

    def read(self, device, item, translate = False):
        DEBUG_API(inspect.currentframe())
        node = self._getNode(device, item)
        if translate:
            # Auto translate item defined by type paramater.
            parameters = node.getParameters()
            #type_ = 'default'
            #if 'type' in parameters: type_ = parameters['type']
            #info("auto translating complex item type: <{type_}>".format(**locals()))
            #node = self._getNode(device, item)
            if node.getSize() > 1:
                payload = self.blockread(device, item)
            else:
                payload = self.read(device, item)
            return self.translator.translate(node, payload)
        value = node.read()
        node.getClient().dispatch()
        info("read 0x{value:0x} from {device}:{item}".format(**locals()))
        return int(value)

    def write(self, device, item, value, verify = False):
        DEBUG_API(inspect.currentframe())
        value = binutils.integer(value)
        node = self._getNode(device, item)
        node.write(value)
        node.getClient().dispatch()
        info("written 0x{value:0x} to {device}:{item}".format(**locals()))
        if verify and node.getPermission() == uhal.NodePermission.READWRITE:
            readback = node.read()
            node.getClient().dispatch()
            if readback != value:
                assert readback == value, "write(): verification mismatch: {device} {item} write=0x{value:08x} read=0x{readback:08x}".format(**locals())

    def blockread(self, device, item, count = None):
        DEBUG_API(inspect.currentframe())
        node = self._getNode(device, item)
        if count is None:
            count = node.getSize()
        info("reading {count} dwords from {device}:{item}".format(**locals()))
        values = node.readBlock(count)
        node.getClient().dispatch()
        return [int(value) for value in values]

    def blockwrite(self, device, item, values, verify = False):
        DEBUG_API(inspect.currentframe())
        node = self._getNode(device, item)
        count = len(values)
        info("writing {count} dwords from {device}:{item}".format(**locals()))
        # Convert from string inputs...
        values = [binutils.integer(value) for value in values]
        node.writeBlock(values)
        node.getClient().dispatch()
        if verify and node.getPermission() == uhal.NodePermission.READWRITE:
            readbacks = self.blockread(device, item)
            for i, value in enumerate(values):
                readback = readbacks[i]
                assert readback == value, "blockwrite(): verification mismatch: {device} {item} offset={i} write=0x{value:08x} read=0x{readback:08x}".format(**locals())

    def configure(self, device, filename, verify = False):
        """Configure device from configuration file. If *verify* is set to
        *True* every write access is verified by reading back the value. This
        applies only for r+w items.
        """
        DEBUG_API(inspect.currentframe())
        filename = os.path.abspath(filename)
        info("loading configuration file: {filename}".format(**locals()))
        config = ConfigFileReader(filename)
        # Get valid device nodes to check configuration file compatibility.
        valid_names = self.connectionManager.getDevice(device).getNodes()
        for item, value in config.items():
            if item not in valid_names:
                raise RuntimeError("Failed to configure from file {filename}\n"
                    "No such item {item}\n"
                    "Configuration file may not match device type?".format(**locals()))
            self.write(device, item, value, verify)
        info("done.")

    def dump(self, device, item, raw = False, decode = False, outfile = None):
        DEBUG_API(inspect.currentframe())
        node = self._getNode(device, item)
        bytes_ = node.getSize()*4
        values = self.blockread(device, item)
        parameters = node.getParameters()
        image = toImage(node) if not raw else GenericMemoryImage(node.getSize())
        info("decoding memory content".format(**locals()))
        image.deserialize(values)
        if outfile:
            if isinstance(outfile, str):
                outfile = os.path.abspath(outfile)
                info("writing formatted data to file: {outfile}".format(**locals()))
            with (open(outfile, 'wb') if isinstance(outfile, str) else outfile) as fp:
                if decode and hasattr(image, 'decode'):
                    fp.write(image.decode())
                else:
                    fp.write(str(image))
                fp.flush()
        return image

    def load(self, device, item, source, verify = False):
        DEBUG_API(inspect.currentframe())
        node = self._getNode(device, item)
        parameters = node.getParameters()
        image = toImage(node)
        if source == ':counter':
            image.fill_counter()
        elif source == ':random':
            image.fill_random()
        else:
            try:
                image.read(open(source, 'rb'))
            except ValueError:
                image.read_testvector(open(source, 'rb'))
        values = image.serialize()
        self.blockwrite(device, item, values, verify)

    def clear(self, device, item, verify = False):
        DEBUG_API(inspect.currentframe())
        node = self._getNode(device, item)
        self.blockwrite(device, item, [0x0] * node.getSize(), verify)

    def compare(self, device, item, dump, pattern, offset = 0, size = TDF.ORBIT_LENGTH, outfile = sys.stdout):
        DEBUG_API(inspect.currentframe())
        node = self._getNode(device, item)
        image = toImage(node)
        image.read(open(dump, 'rb') if isinstance(dump, str) else dump)
        #print >>open('a', 'wb'), str(image)
        reference = toImage(node)
        if not hasattr(reference, 'read_testvector'):
            reference.read(open(pattern, 'rb') if isinstance(pattern, str) else pattern)
        else:
            reference.read_testvector(open(pattern, 'rb') if isinstance(pattern, str) else pattern)
        #print >>open('b', 'wb'), str(reference)
        image.compare(reference, offset, size, outfile)

    def wait(self, device, item, value = 0, timeout = 10.0, interval = 0.25):
        """Wait for item until it contains requested *value* or fail after
        *timeout* in seconds, shows optional *message* on timeout. Argument
        *interval* defines the interval for reading *item*.
        """
        DEBUG_API(inspect.currentframe())
        t = time.time()
        while self.read(device, item) != value:
            if time.time() > t + timeout:
                raise RuntimeError("Timeout waiting for `{item}' to be `0x{value:0x}' on device `{device}'.".format(**locals()))
            time.sleep(interval)

    def buffgen(self, pattern, quads = 18, frames = 1024, board = 'MP7_GENERIC', outfile = sys.stdout):
        DEBUG_API(inspect.currentframe())
        # Using MP7 tx/rx buffer generator.
        buffgen = Buffgen(board)
        if isinstance(outfile, str): #TODO
            outfile = open(outfile, 'wr')

        # Generate generic patterns.
        if pattern.startswith(":"):
            if pattern in (':zero', ):
                print >>outfile, buffgen.zero(quads, frames)
                return TDF.EXIT_SUCCESS
            elif pattern in (':counter', ):
                print >>outfile, buffgen.counter(quads, frames)
                return TDF.EXIT_SUCCESS
            raise RuntimeError("no such pattern `{pattern}', try `:zero' or `:counter' instead".format(**locals()))

        # Else load the test vector file.
        else:
            print >>outfile, buffgen.fromTestVector(pattern, quads, frames)
            return TDF.EXIT_SUCCESS

    def mp7butler(self, *args, **kwargs):
        """Execute a MP7 butler command. Optional positional argument list
        *args* is forwared to the MP7 butler call. Take note that the following
        command line options are preprended to any given arguments: *-q* to
        disable the branding and *-c* to set the connections file used by TDF.

        For capturing *stdout* use the *stdout* named argument writing to a
        spooled tempfile:

        >>> import tempfile
        >>> tmp = tempfile.SpooledTemporaryFile()
        >>> mp7butler(..., stdout = tmp)
        >>> tmp.seek(0)
        >>> result = tmp.read()
        >>> tmp.close()
        """
        DEBUG_API(inspect.currentframe())
        command = [MP7_EXECUTABLE, '-q', '-c', self.connections]
        if self.verbose:
            command.append('-v')
        command.extend([str(arg) for arg in args])
        debug(*command)
        info("calling:", *command)
        # Not working: capturing the stderr disables mp7butler logging outputs :(
        #f = tempfile.SpooledTemporaryFile()
        #subprocess.check_call(command, stderr = f, bufsize = 1)
        #f.seek(0)
        #print f.read()
        stdout = kwargs.get('stdout', None)
        subprocess.check_call(command, stdout = stdout)

    def unittest(self, device, test):
        """Execute a device specific unittest. Argument *device* is the ID of
        the device specified in the address table, argument *test* is the name
        of the unittest to be executed.

        Note the naming notation for device IDs *<module>.<slot>*
        """
        DEBUG_API(inspect.currentframe())
        return ScriptRunner(self).run_unittest(device, test)

    def run(self, routine, *args):
        """Execute a routine script. Argument *routine* is the name of the
        routine to be executed. Optional positional argument list *args* is the
        argument list forwared to the routine.

        >>> run("read_item", "ctrl.id")
        """
        DEBUG_API(inspect.currentframe())
        # ...create a temporary run environemnt/area, then move to
        return ScriptRunner(self).run_routine(routine, *args)
