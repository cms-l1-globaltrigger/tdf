# load_simdata.py
# Load data from test vector.
# This script can be used to produce some rates while runningthe SWATCH cell.

from tdf.extern import argparse
from tdf.core import TDF
import sys, os


parser = argparse.ArgumentParser()
parser.add_argument('device', nargs='+', help="devices to be configured")
parser.add_argument('testvector')
args = parser.parse_args(TDF_ARGS)

for device in args.device:
    load(device, 'gt_mp7_frame.simspymem', args.testvector)
