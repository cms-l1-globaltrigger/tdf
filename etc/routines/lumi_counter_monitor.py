# lumi_counter_monitor.py
# Monitors luminosity segment counter and orbit counter.
# Provided for debuggign purpose.
from tdf.extern import argparse
from tdf.core import binutils
from tdf.core import TDF
import time
import sys

def read_lumi_counter(device):
    return read(device, "gt_mp7_frame.rb.tcm_status.luminosity_seg_nr")

def read_orbit_counter(device):
    return binutils.bitjoin([
            read(args.device, "gt_mp7_frame.rb.tcm_status.orbit_nr_l"),
            read(args.device, "gt_mp7_frame.rb.tcm_status.orbit_nr_h"),
        ], TDF.DATA_WIDTH)

parser = argparse.ArgumentParser()
parser.add_argument('device')
parser.add_argument('index', metavar='<n>', nargs='+', type=int, help="algorithm indicis to monitor (can be multiple)")
parser.add_argument('-i', dest='interval', metavar='<f>', type=float, default=4., help="time interval, default 4.0 sec")
args = parser.parse_args(TDF_ARGS)
# sort the indices
args.index.sort()

TDF_NOTICE("hit CTRL + C to exit routine")

# Get initial luminosity section
previous_ls = read_lumi_counter(args.device)
print "waiting for next luminosity section..."

with open("{0}.log".format(TDF_NAME), "w") as logger:
    TDF_NOTICE("start writing to log file", logger.name)
    logger.write("start logging counter missmatches...\n")
    logger.write("| LumiSegNr | rate_before_prescale | rate_after_prescale  | algo | err_det |\n")
    try:
        while True:
            # Get current luminosity section
            current_ls = read_lumi_counter(args.device)
            # Do nothing until reachibng a new luminosity section
            if previous_ls != current_ls:
                rate_cnt_before_prescaler = blockread(args.device, "gt_mp7_gtlfdl.rate_cnt_before_prescaler")
                rate_cnt_after_prescaler = blockread(args.device, "gt_mp7_gtlfdl.rate_cnt_after_prescaler")
                err_det = read(args.device, "gt_mp7_frame.rb.tcm_status.err_det")
                print "| LumiSegNr | rate_before_prescale | rate_after_prescale  | algo | err_det |"
                for index in args.index:
                    before_cnt = rate_cnt_before_prescaler[index]
                    after_cnt = rate_cnt_after_prescaler[index]
                    print "| {previous_ls:>9} | {before_cnt:>20} | {after_cnt:>20} | {index:>4} | {err_det:>7} |".format(**locals())
                # Compare counter values -- must match, else issue an error
                # Logging (do for all algorithms, just to get sure... who knows...)
                for i in range(len(rate_cnt_before_prescaler)):
                    before_cnt = rate_cnt_before_prescaler[i]
                    after_cnt = rate_cnt_after_prescaler[i]
                    if before_cnt != after_cnt:
                        TDF_ERROR("before/after counter values not equal: {before_cnt} != {after_cnt}".format(**locals()))
                        logger.write("| {previous_ls:>9} | {before_cnt:>20} | {after_cnt:>20} | {i:>4} | {err_det:>7} |\n".format(**locals()))
            previous_ls = current_ls
            # throttle monitoring rate
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.write("stopped logging.\n")
        TDF_NOTICE("stoped writing to log file", logger.name)
        sys.exit(0)
