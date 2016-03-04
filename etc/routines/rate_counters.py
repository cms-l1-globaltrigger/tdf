# rate_counters.py
# BA 2015-05-28: created
# dumping rate counters and prescales

from tdf.extern import argparse

MAX_ALGORITHMS = 512
LUMI_SEC = 23.312

parser = argparse.ArgumentParser()
parser.add_argument('device')
parser.add_argument('--limit', type=int, default=MAX_ALGORITHMS, help="limit number of displayed algorithms (default {0})".format(MAX_ALGORITHMS))
args = parser.parse_args(TDF_ARGS)

rateCntBeforePrescaler = blockread(args.device, "gt_mp7_gtlfdl.rate_cnt_before_prescaler")
#rateCntAfterPrescaler = read(args.device, "gt_mp7_gtlfdl.rate_cnt_after_prescaler")
prescaleFactor = blockread(args.device, "gt_mp7_gtlfdl.prescale_factor")
masks = blockread(args.device, "gt_mp7_gtlfdl.masks")

print "| Algo | Rate before prescales | Rate before prescales (Hz) | Prescale factor | FINOR mask | Veto |"
for i in range(min(MAX_ALGORITHMS, args.limit)):
    print "| {0:4} | {1:21} | {2:26} | {3:15} | {4:10} | {5:4} |".format(
        i, rateCntBeforePrescaler[i], int(rateCntBeforePrescaler[i] / LUMI_SEC), prescaleFactor[i], masks[i] & 0x1, masks[i] & 0x2
    )
