#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013-2015 Bernhard Arnold <bernahrd.arnold@cern.ch>
#

from distutils.core import setup
from distutils.command.build import build
import importlib
import glob, re, os.path
import subprocess

def load_version(module):
    """Returns __version__ from python module."""
    module = importlib.import_module('tdf')
    return module.__version__

def glob_dirs(needle):
    """Returns list of subdirectories looked up by search needle."""
    return list(set([os.path.dirname(filename) for filename in glob.glob(needle)]))

def glob_files(targetdir, *needles):
    """Returns list of tuples for distutils data_files looked up by multiple search needles."""
    data_files = []
    for needle in needles:
        for dirname in glob_dirs(needle):
            data_files.append((
                os.path.join(targetdir, dirname),
                glob.glob(os.path.join(dirname, os.path.basename(needle)))
            ))
    return data_files

class build_hook(build):
    """Custom build command performing pre and post build operations."""

    def run(self):
        self.pre_build()
        build.run(self)
        self.post_build()

    def pre_build(self):
        # Calling the makefile.
        subprocess.check_call('make')

    def post_build(self):
        pass

setup(
    cmdclass = {'build' : build_hook, },
    name = 'tdf',
    version = load_version('tdf'),
    description = "TDF - Global Trigger Test and Development Framework",
    author = "Bernhard Arnold",
    author_email = "bernhard.arnold@cern.ch",
    url = "http://www.hephy.oeaw.ac.at/",
    packages = ['tdf', 'tdf.core', 'tdf.extern', 'tdf.mp7', 'tdf.widgets'],
    data_files = glob_files('/opt/tdf',
        'etc/uhal/*.xml', # connection files.
        'etc/config/*/*.cfg', # device configurations.
        'etc/routines/*.py', # routine scripts.
        'etc/unittest/*/*.py', # unittests.
    ),
    scripts = (
        'bin/tdf',
        'bin/tdf-analyze',
        'bin/tdf-control',
    ),
    setup_requires = [],
    install_requires = [],
    provides = ['tdf', ],
)
