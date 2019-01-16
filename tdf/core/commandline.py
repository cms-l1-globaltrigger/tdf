#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK (tag required by argcomplete, DO NOT REMOVE)
#
# Copyright 2013-2014 Bernhard Arnold <bernahrd.arnold@cern.ch>
#

import sys, os
import uhal
from glob import glob
import subprocess

from tdf.extern import argparse
from tdf.extern import argcomplete
from tdf.core import TDF
from tdf.core import TDFCore
from tdf.core import binutils
from tdf.core.logger import *
import logging

def branding():
    lines = (
        "  _____ ___   _____",
        " /_  _// _ \ / ___/   Global Trigger's",
        "  / / / // // __/    Test and Development Framework CLI",
        " /_/ /____//_/      version {TDF.VERSION}".format(**globals()),
        "",
    )
    for line in lines:
        logging.info(line)

def getConnectionsFile(crate=os.getenv('TDF_DEFAULT_CRATE', "vienna_testing")):
    root = TDF.ROOT_DIR
    return "file://{root}/etc/uhal/connections_{crate}.xml".format(**locals())

def DevicesCompleter(prefix, **kwargs):
    crate = kwargs['parsed_args'].crate
    connections = kwargs['parsed_args'].connections
    if crate:
        connections = getConnectionsFile(crate)
    return (device for device in uhal.ConnectionManager(connections).getDevices())

def ItemsCompleter(prefix, **kwargs):
    crate = kwargs['parsed_args'].crate
    connections = kwargs['parsed_args'].connections
    device = str(kwargs['parsed_args'].device)
    if crate:
        connections = getConnectionsFile(crate)
    cm = uhal.ConnectionManager(connections)
    nodes = cm.getDevice(device).getNodes()
    candidates = []
    for candidate in [node for node in nodes if node.startswith(prefix)]:
        end = candidate[len(prefix):].split('.')
        if len(end) == 1:
            candidates.append(prefix + end[0])
        else:
            candidates.append(prefix + end[0] + '.' + end[1])
    return (node for node in candidates)

def UnittestsCompleter(prefix, **kwargs):
    device_base = str(kwargs['parsed_args'].device).split('.')[0]
    filenames = glob(os.path.join(TDF.ROOT_DIR, "etc/unittest", device_base, "*.py"))
    return (os.path.basename(os.path.splitext(filename)[0]) for filename in filenames)

def RoutinesCompleter(prefix, **kwargs):
    filenames = glob(os.path.join(TDF.ROOT_DIR, "etc/routines", "*.py"))
    return (os.path.basename(os.path.splitext(filename)[0]) for filename in filenames)

class TDFCommandLine(object):
    """Command line interface for the TDF core API."""

    def parse(self):
        parser = argparse.ArgumentParser(prog='tdf', description="Test and Development Framework - Command Line Interface", )
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--crate', metavar='<id>', help="set crate environment (eg. vienna_testing)")
        group.add_argument('-c', '--connections', metavar='<url>', default=getConnectionsFile(), help="use custom connections file")
        parser.add_argument('-v', '--verbose', action='count', help="prints addional information what is going on")
        parser.add_argument('-V', '--version', action='version', version="%(prog)s {0}".format(TDF.VERSION))
        command = parser.add_subparsers()

        # Read command parser.
        sub = command.add_parser('read', help="read from a single item")
        sub.add_argument('device', help="device defined in connections file").completer = DevicesCompleter
        sub.add_argument('item', help="item defined in address table").completer = ItemsCompleter
        sub.add_argument('-t', '--translate', action='store_true', help="auto translate item defined by type paramater")
        sub.set_defaults(func=self.cmd_read)

        # Write command parser.
        sub = command.add_parser('write', help="write to a single item")
        sub.add_argument('device', help="device defined in connections file").completer = DevicesCompleter
        sub.add_argument('item', help="item defined in address table").completer = ItemsCompleter
        sub.add_argument('value', type=binutils.integer, help="value to be written (dec or bin/hex with prefix)")
        sub.add_argument('--verify', action='store_true', help="read back values to verify")
        sub.set_defaults(func=self.cmd_write)

        # Blockread command parser.
        sub = command.add_parser('blockread', help="read from a memory item")
        sub.add_argument('device', help="device defined in connections file").completer = DevicesCompleter
        sub.add_argument('item', help="item defined in address table").completer = ItemsCompleter
        sub.add_argument('count', nargs='?', type=int, help="number of registers to be read")
        sub.set_defaults(func=self.cmd_blockread)

        # Blockwrite command parser.
        sub = command.add_parser('blockwrite', help="write to a memory item")
        sub.add_argument('device', help="device defined in connections file").completer = DevicesCompleter
        sub.add_argument('item', help="item defined in address table").completer = ItemsCompleter
        sub.add_argument('value', nargs='+', help="values to be written (dec or hex with prefix)")
        sub.add_argument('--verify', action='store_true', help="read back values to verify")
        sub.set_defaults(func=self.cmd_blockwrite)

        # Configure command parser.
        sub = command.add_parser('configure', help="sequence a configuration file to a device")
        sub.add_argument('device', help="device defined in connections file").completer = DevicesCompleter
        sub.add_argument('filename', help="configuration file (name or URI) to sequence (*.cfg)")
        sub.add_argument('--verify', action='store_true', help="read back values to verify")
        sub.set_defaults(func=self.cmd_configure)

        # Memory dump command parser.
        sub = command.add_parser('dump', help="dump formatted memory")
        sub.add_argument('device', help="device defined in connections file").completer = DevicesCompleter
        sub.add_argument('item', help="memory item defined in address table").completer = ItemsCompleter
        group = sub.add_mutually_exclusive_group()
        group.add_argument('--decode', action='store_true', help="decode to JSON")
        group.add_argument('--raw', action='store_true', help="return raw data format")
        sub.add_argument('-o', '--outfile', metavar='<file>', default=sys.stdout, help="write output to file, default is stdout")
        sub.set_defaults(func=self.cmd_dump)

        # Memory load command parser.
        sub = command.add_parser('load', help="load memory from test vector or dump")
        sub.add_argument('device', help="device defined in connections file").completer = DevicesCompleter
        sub.add_argument('item', help="memory item defined in address table").completer = ItemsCompleter
        sub.add_argument('filename', help="pattern (:counter, :zero) or dump file to be loaded")
        sub.add_argument('--verify', action='store_true', help="read back memory to verify")
        sub.set_defaults(func=self.cmd_load)

        # Memory clear command parser.
        sub = command.add_parser('clear', help="clear memory")
        sub.add_argument('device', help="device defined in connections file").completer = DevicesCompleter
        sub.add_argument('item', help="memory item defined in address table").completer = ItemsCompleter
        sub.add_argument('--verify', action='store_true', help="read back memory to verify")
        sub.set_defaults(func=self.cmd_clear)

        sub = command.add_parser('compare', help="compare memory dumps with test vector file")
        sub.add_argument('device', help="device defined in connections file").completer = DevicesCompleter
        sub.add_argument('item', help="memory item defined in address table").completer = ItemsCompleter
        sub.add_argument('dump',  type=argparse.FileType('rb'), help="memory dump file")
        sub.add_argument('testvector',  help="emulator test vector file")
        sub.add_argument('--offset', metavar='<bx>', default=0, type=int, help="data offset to compare, default is 0")
        sub.add_argument('--size', metavar='<bx>', default=TDF.ORBIT_LENGTH, type=int, help="number of bx to compare")
        sub.add_argument('-o', '--outfile', metavar='<file>', default=sys.stdout, type=argparse.FileType('w'), help="write output to file")
        sub.set_defaults(func=self.cmd_compare)

        sub = command.add_parser('wait', help="wait for item until it contains value or timeout")
        sub.add_argument('device', help="device defined in connections file").completer = DevicesCompleter
        sub.add_argument('item', help="memory item defined in address table").completer = ItemsCompleter
        sub.add_argument('value', type=binutils.integer, help="value to be tested (dec or bin/hex with prefix), default is 0")
        sub.add_argument('--timeout', default=10.0, type=float, help="timeout in seconds, default is10.0")
        sub.add_argument('--interval', default=0.25, type=float, help="interval in seconds, default is 0.25")
        sub.set_defaults(func=self.cmd_wait)

        sub = command.add_parser('buffgen', help="generate MP7 240 MHz algorithm buffer patterns")
        sub.add_argument('pattern', default=':counter', nargs='?', help="type of generated pattern (:zero, :counter) or a test vector file, default is `:counter'")
        sub.add_argument('-q', '--quads', metavar='<n>', default=18, type=int, help="number of quads, default 18")
        sub.add_argument('-f', '--frames', metavar='<n>', default=1024, type=int, help="number of frames, default 1024")
        sub.add_argument('-b', '--board', metavar='<id>', default='MP7_TEST', help="board ID, default MP7_TEST")
        sub.add_argument('-o', '--outfile', metavar='<file>', default=sys.stdout, type=argparse.FileType('w'), help="write output to file")
        sub.set_defaults(func=self.cmd_buffgen)

        sub = command.add_parser('mp7butler', help="wrapper to execute MP7 butler software")
        sub.add_argument('args', nargs=argparse.REMAINDER, help="mp7butler specific arguments")
        sub.set_defaults(func=self.cmd_mp7butler)

        sub = command.add_parser('amc502butler', help="wrapper to execute AMC502 butler software")
        sub.add_argument('args', nargs=argparse.REMAINDER, help="amc502butler specific arguments")
        sub.set_defaults(func=self.cmd_amc502butler)

        # Unittest command parser.
        sub = command.add_parser('unittest', help="run a device's unittest")
        sub.add_argument('device', help="device defined in connections file").completer = DevicesCompleter
        sub.add_argument('test', help = "name of the unittest").completer = UnittestsCompleter
        sub.set_defaults(func=self.cmd_unittest)

        # Script runner command parser.
        sub = command.add_parser('run', help="execute a test or routine script")
        sub.add_argument('routine', help="name or URL of the script/routine to run").completer = RoutinesCompleter
        sub.add_argument('args', nargs=argparse.REMAINDER, help="additional test specific argument")
        sub.set_defaults(func=self.cmd_run)

        # Enable tab auto completion.
        argcomplete.autocomplete(parser)

        args = parser.parse_args()

        # Set connections file if selected by crate name.
        if args.crate:
            args.connections = getConnectionsFile(args.crate)

        return args

    def cmd_read(self, args):
        if args.translate:
            print self.core.read(args.device, args.item, translate=True)
        else:
            print "0x{0:08x}".format(self.core.read(args.device, args.item, translate=False))

    def cmd_write(self, args):
        self.core.write(args.device, args.item, args.value, args.verify)

    def cmd_blockread(self, args):
        values = self.core.blockread(args.device, args.item, args.count)
        for value in values:
            print "0x{value:08x}".format(**locals())

    def cmd_blockwrite(self, args):
        self.core.blockwrite(args.device, args.item, args.value, verify=args.verify)

    def cmd_configure(self, args):
        self.core.configure(args.device, args.filename, args.verify)

    def cmd_dump(self, args):
        self.core.dump(args.device, args.item, args.raw, args.decode, args.outfile)

    def cmd_load(self, args):
        self.core.load(args.device, args.item, args.filename, args.verify)

    def cmd_clear(self, args):
        self.core.clear(args.device, args.item, args.verify)

    def cmd_compare(self, args):
        self.core.compare(args.device, args.item, args.dump, args.testvector, args.offset, args.size, args.outfile)

    def cmd_wait(self, args):
        self.core.wait(args.device, args.item, args.value, args.timeout, args.interval)

    def cmd_buffgen(self, args):
        self.core.buffgen(args.pattern, args.quads, args.frames, args.board, args.outfile)

    def cmd_mp7butler(self, args):
        try:
            self.core.mp7butler(*args.args)
        except subprocess.CalledProcessError, e:
            critical("*** Failed to execute MP7 butler software:")
            critical(" command:", " ".join(e.cmd))
            critical(" returncode:", e.returncode)
            sys.exit(TDF.EXIT_FAIL)

    def cmd_amc502butler(self, args):
        try:
            self.core.amc502butler(*args.args)
        except subprocess.CalledProcessError, e:
            critical("*** Failed to execute AMC502 butler software:")
            critical(" command:", " ".join(e.cmd))
            critical(" returncode:", e.returncode)
            sys.exit(TDF.EXIT_FAIL)

    def cmd_unittest(self, args):
        info("executing unittest", args.test)
        self.core.unittest(args.device, args.test)

    def cmd_run(self, args):
        info("executing routine", args.routine)
        self.core.run(args.routine, *args.args)

    def exec_(self):
        """Execute TDF application using the given command line arguments."""
        args = self.parse()

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        if args.verbose > 1:
            logger.setLevel(logging.DEBUG)

        branding()

        # Show only on high verbose level.
        if args.verbose <= 2:
            uhal.disableLogging()

        try:
            self.core = TDFCore(args.connections, args.verbose)
            args.func(args)
        except Exception, e:
            for line in str(e).strip().split("\n"):
                critical(line)
            raise
        else:
            info("done.")
        return TDF.EXIT_SUCCESS
