# rate_counters.py
# BA 2015-05-28: created
# dumping rate counters and prescales

from tdf.core.xmlmenu import XmlMenu
from tdf.extern import argparse

MAX_ALGORITHMS = 512
LUMI_SEC = 23.312

# -----------------------------------------------------------------------------
#  Parse arguments
# -----------------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument('device')
parser.add_argument('-l', '--limit', metavar='<n>', type=int, default=MAX_ALGORITHMS, help="limit number of displayed algorithms (default {0})".format(MAX_ALGORITHMS))
parser.add_argument('-m', '--menu', metavar='<file>', help="read XML menu to list algorithm names")
args = parser.parse_args(TDF_ARGS)


# -----------------------------------------------------------------------------
#  Dump counters
# -----------------------------------------------------------------------------
rateCntFinor = read(args.device, "gt_mp7_gtlfdl.rate_cnt_finor")
rateCntL1A = read(args.device, "gt_mp7_gtlfdl.rate_cnt_l1a")
rateCntBeforePrescaler = blockread(args.device, "gt_mp7_gtlfdl.rate_cnt_before_prescaler")
rateCntAfterPrescaler = blockread(args.device, "gt_mp7_gtlfdl.rate_cnt_after_prescaler")
prescaleFactor = blockread(args.device, "gt_mp7_gtlfdl.prescale_factor")
masks = blockread(args.device, "gt_mp7_gtlfdl.masks")

# -----------------------------------------------------------------------------
#  Fetch algorithm names (optional)
# -----------------------------------------------------------------------------
names = [''] * MAX_ALGORITHMS
if args.menu:
    menu = XmlMenu(args.menu)
    for i in range(len(names)):
        algorithm = menu.algorithms.byIndex(i)
        if algorithm:
            names[i] = algorithm.name

# -----------------------------------------------------------------------------
#  Print table
# -----------------------------------------------------------------------------
print "FinOR rate: {0:.1f} Hz".format(rateCntFinor / LUMI_SEC)
print "L1A rate: {0:.1f} Hz".format(rateCntL1A / LUMI_SEC)
print ""
print "| Algo | Rate before prescales | Rate after prescales | Prescale factor | FINOR mask | Veto | Name"
for i in range(min(MAX_ALGORITHMS, args.limit)):
    print "| {0:4} | {1:18.1f} Hz | {2:17.1f} Hz | {3:14}x | {4:10} | {5:4} | {6}".format(
        i,
        rateCntBeforePrescaler[i] / LUMI_SEC,
        rateCntAfterPrescaler[i] / LUMI_SEC,
        prescaleFactor[i],
        masks[i] & 0x1,
        masks[i] & 0x2,
        names[i],
    )
