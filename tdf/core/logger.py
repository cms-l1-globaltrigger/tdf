# -*- coding: utf-8 -*-
#
# Copyright 2013-2016 Bernhard Arnold <bernahrd.arnold@cern.ch>
#

"""Custom logger module providing a set of logging functions dedicated to
different logging levels.

>>> from tdf.core.logger import logger
>>> logger.info("an informative message")
>>> logger.notice("a more important message")
>>> logger.warning("a warning message")
>>> logger.error("an error message")
>>> logger.critical("a very critial error message")

"""

import logging
from tdf.extern.ansistrm import ColorizingStreamHandler

__all__ = ('info', 'warning', 'error', 'critical', 'debug')

_logger = logging.getLogger()
_logger.setLevel(logging.DEBUG)
_logger.addHandler(ColorizingStreamHandler())

# Extend by NOTICE level messages
logging.addLevelName(25, 'NOTICE')

def info(*args):
    logging.log(logging.INFO, "INFO     | TDF | " + " ".join((str(arg) for arg in args)))

def notice(*args):
    logging.log(logging.getLevelName('NOTICE'), "NOTICE   | TDF | " + " ".join((str(arg) for arg in args)))

def warning(*args):
    logging.log(logging.WARNING, "WARNING  | TDF | " + " ".join((str(arg) for arg in args)))

def error(*args):
    logging.log(logging.ERROR, "ERROR    | TDF | " + " ".join((str(arg) for arg in args)))

def critical(*args):
    logging.log(logging.CRITICAL, "CRITICAL | TDF | " + " ".join((str(arg) for arg in args)))

def debug(*args):
    logging.log(logging.DEBUG, "DEBUG    | TDF | " + " ".join((str(arg) for arg in args)))
