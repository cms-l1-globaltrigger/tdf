# lumi_counter_monitor.py
# Monitors luminosity segment counter and orbit counter.
# Provided for debuggign purpose.
from tdf.extern import argparse
from tdf.core import binutils
from tdf.core import TDF
import time

def read_lumi_counter(device):
    return read(device, "gt_mp7_frame.rb.tcm_status.luminosity_seg_nr")

def read_orbit_counter(device):
    return binutils.bitjoin([
            read(args.device, "gt_mp7_frame.rb.tcm_status.orbit_nr_l"),
            read(args.device, "gt_mp7_frame.rb.tcm_status.orbit_nr_h"),
        ], TDF.DATA_WIDTH)

parser = argparse.ArgumentParser()
parser.add_argument('device')
parser.add_argument('index', metavar='<n>', type=int, help="algorithm index to monitor")
parser.add_argument('-i', metavar='<f>', type=float, default=4., help="time interval, default 4.0 sec")
args = parser.parse_args(TDF_ARGS)

TDF_WARNING("note: hit CTRL + C to exit routine")

previous_ls = read_lumi_counter(args.device)
rate_cnt_before_prescaler = blockread(args.device, "gt_mp7_gtlfdl.rate_cnt_before_prescaler")
print "| LumiSegNr | rate_before_prescale |"
print "| {0:>9} | {1:>20} |".format(previous_ls, rate_cnt_before_prescaler[args.index])

try:
    while True:
        current_ls = read_lumi_counter(args.device)
        if previous_ls != current_ls:
            rate_cnt_before_prescaler = blockread(args.device, "gt_mp7_gtlfdl.rate_cnt_before_prescaler")
            print "| LumiSegNr | rate_before_prescale |"
            print "| {0:>9} | {1:>20} |".format(current_ls, rate_cnt_before_prescaler[args.index])
            previous_ls = current_ls
        # throttle monitoring rate
        time.sleep(args.i)
except KeyboardInterrupt:
    pass