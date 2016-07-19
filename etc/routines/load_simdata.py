# load_simdata.py
# Load data from test vector and configure MUX.
# This script can be used to produce some rates while runningthe SWATCh cell.
from tdf.extern import argparse
from tdf.core import TDF
import sys, os


parser = argparse.ArgumentParser()
parser.add_argument('device', nargs='+', help="devices to be configured")
parser.add_argument('testvector')
args = parser.parse_args(TDF_ARGS)

for device in args.device:
    load(device, 'gt_mp7_frame.simspymem', args.testvector)
    configure(device, os.path.join(TDF.ROOT_DIR, 'etc/config/gt_mp7/cfg-140/mp7-spy-SIM.cfg'))
