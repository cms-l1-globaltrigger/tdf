import logging
from tdf.extern.ansistrm import ColorizingStreamHandler

__all__ = ('info', 'warning', 'error', 'critical', 'debug')

_logger = logging.getLogger()
_logger.setLevel(logging.DEBUG)
_logger.addHandler(ColorizingStreamHandler())

def info(*args):
    logging.info("INFO     | TDF | " + " ".join((str(arg) for arg in args)))

def warning(*args):
    logging.warning("WARNING  | TDF | " + " ".join((str(arg) for arg in args)))

def error(*args):
    logging.error("ERROR    | TDF | " + " ".join((str(arg) for arg in args)))

def critical(*args):
    logging.critical("CRITICAL | TDF | " + " ".join((str(arg) for arg in args)))

def debug(*args):
    logging.debug("DEBUG    | TDF | " + " ".join((str(arg) for arg in args)))
