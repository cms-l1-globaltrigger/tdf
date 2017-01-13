
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
rateCntFinorPreview = read(args.device, "gt_mp7_gtlfdl.rate_cnt_finor_preview")
rateCntBeforePrescaler = blockread(args.device, "gt_mp7_gtlfdl.rate_cnt_before_prescaler")
rateCntAfterPrescalerPreview = blockread(args.device, "gt_mp7_gtlfdl.rate_cnt_after_prescaler_preview")
prescaleFactorPreview = blockread(args.device, "gt_mp7_gtlfdl.prescale_factor_preview")
prescaleSetIndexPreview = read(args.device, "gt_mp7_gtlfdl.prescale_factor_set_index_preview")
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
print ""
print "Prescale set index preview: %d" %prescaleSetIndexPreview
print "FinOR rate preview: {0:.1f} Hz".format(rateCntFinorPreview / LUMI_SEC)
print ""
print "                                       | Prescale |   Rate after   | Counts after |     "
print "      |   Rate before  | Counts before |  factor  |    prescales   |   prescales  |     "
print " Algo |    prescales   |   prescales   | preview  |     preview    |    preview   | Name"
print "------------------------------------------------------------------------------------------------------"
for i in range(min(MAX_ALGORITHMS, args.limit)):
    print " {0:4} | {1:11.1f} Hz | {2:13} | {3:7}x | {4:11.1f} Hz | {5:13}| {6} ".format(
        i,
        rateCntBeforePrescaler[i] / LUMI_SEC,
        rateCntBeforePrescaler[i],
        prescaleFactorPreview[i],
        rateCntAfterPrescalerPreview[i] / LUMI_SEC,
        rateCntAfterPrescalerPreview[i],
        names[i],
    )
