#
# Makefile for TDF
#
# Copyright 2013-2014 Bernhard Arnold <bernahrd.arnold@cern.ch>
#                     Johannes Wittmann <johannes.wittmann@cern.ch>
#
# Repository path   : $HeadURL: svn://heros.hephy.oeaw.ac.at/GlobalTriggerUpgrade/software/tdf/trunk/Makefile $
# Last committed    : $Revision: 3622 $
# Last changed by   : $Author: arnold $
# Last changed date : $Date: 2015-01-09 12:30:00 +0100 (Fri, 09 Jan 2015) $
#

# Package
PKG_NAME = tdf

# Directories
PKG_DIR = lib/$(PKG_NAME)
BUILD_DIR = build
DEB_DIST_DIR = deb_dist
RPM_DIST_DIR = dist
SPHINX_DIR = doc/sphinx

# Executables
PYTHON = python
SETUP = $(PYTHON) setup.py
REMOVE = rm -rfv

.PHONY: all build deb rpm doc clean distclean

all: build

build:

rpm: build
	# Requires custom RPM install script to handle (auto) bytecompiled side files correctly.
	$(SETUP) bdist_rpm --install-script install.spec

doc:
	cd $(SPHINX_DIR) && make clean
	cd $(SPHINX_DIR) && make html

clean:
	$(REMOVE) $(BUILD_DIR)

distclean: clean
	$(REMOVE) $(DEB_DIST_DIR) $(RPM_DIST_DIR)
	$(REMOVE) MANIFEST
