# dump_prescale_factors.py
# HB 2022-03-11: created
# dumping prescale factors

from tdf.extern import argparse

MAX_ALGORITHMS = 512

# -----------------------------------------------------------------------------
#  Parse arguments
# -----------------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument('device')
parser.add_argument('-l', '--limit', metavar='<n>', type=int, default=MAX_ALGORITHMS, help="limit number of displayed algorithms (default {0})".format(MAX_ALGORITHMS))
args = parser.parse_args(TDF_ARGS)

masks = blockread(args.device, "gt_mp7_gtlfdl.prescale_factor")

for i in range(min(MAX_ALGORITHMS, args.limit)):
    print "| {0:4} | {1:08x}".format(i,masks[i])
