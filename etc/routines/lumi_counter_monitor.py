# lumi_counter_monitor.py
# Monitors luminosity segment counter and orbit counter.
# Provided for debuggign purpose.
from tdf.extern import argparse
from tdf.core import binutils
from tdf.core import TDF
from tdf.core.xmlmenu import XmlMenu
from collections import namedtuple
import uhal
import time
import sys

MAX_ALGORITHMS = 512
LUMI_SEC = 23.312

# Holds luminosity segment number and associated counters.
class LumiSegment(namedtuple('LumiSegment', 'ls_number, rates_before_prescaler, rates_after_prescaler, deadtime_counters, err_det')):

    header = "| LumiSegNr | Rate before prescale | Rate after prescale  | Post dead time | err_det | Index | Name"

    def row(self, index, name=""):
        """Returns table row for algorithm of *index*."""
        number = self.ls_number
        before = self.rates_before_prescaler[index]
        after = self.rates_after_prescaler[index]
        deadtime = self.deadtime_counters[index]
        err_det = self.err_det
        return "| {number:>9} | {before:>20} | {after:>20} | {deadtime:>14} | {err_det:>7} | {index:>5} | {name}".format(**locals())

def read_lumi_counter(device):
    """Returns current luminosity segment number."""
    return read(device, "gt_mp7_frame.rb.tcm_status.luminosity_seg_nr")

def read_orbit_counter(device):
    """Returns 64 bit orbit counter."""
    return binutils.bitjoin([
            read(args.device, "gt_mp7_frame.rb.tcm_status.orbit_nr_l"),
            read(args.device, "gt_mp7_frame.rb.tcm_status.orbit_nr_h"),
        ], TDF.DATA_WIDTH)

def read_segment_counters(device, ls_number):
    """Read counters and returns LumiSegment tuple."""
    return LumiSegment(
        ls_number=ls_number,
        rates_before_prescaler=blockread(device, "gt_mp7_gtlfdl.rate_cnt_before_prescaler"),
        rates_after_prescaler=blockread(device, "gt_mp7_gtlfdl.rate_cnt_after_prescaler"),
        deadtime_counters=blockread(device, "gt_mp7_gtlfdl.rate_cnt_post_dead_time"),
        err_det=read(args.device, "gt_mp7_frame.rb.tcm_status.err_det")
    )

parser = argparse.ArgumentParser()
parser.add_argument('device')
parser.add_argument('index', metavar='<n>', nargs='+', type=int, help="algorithm indicis to monitor (can be multiple)")
parser.add_argument('-i', dest='interval', metavar='<f>', type=float, default=5., help="time interval, default 5.0 sec")
parser.add_argument('-m', '--menu', metavar='<file>', help="read XML menu to list algorithm names")
parser.add_argument('--missmatches', action='store_true', help="enable checks for counter missmatches")
parser.add_argument('--stucked', action='store_true', help="enable checks for stucked counters")
parser.add_argument('--stucked-cache-size', metavar='<n>', type=int, default=3, help="number of cached luminosity segment, default 3")
parser.add_argument('--stucked-threshold', metavar='<n>', type=int, default=10, help="threshold for detecting stucked counters, default >= 10")
parser.add_argument('--dump', metavar='<file>', type=argparse.FileType('w'), help="dump recorded after prescale rate counters to CSV formatted file")
args = parser.parse_args(TDF_ARGS)

# Sort the indices
args.index.sort()

# Fetch algorithm names (optional)
algorithm_names = [''] * MAX_ALGORITHMS
if args.menu:
    menu = XmlMenu(args.menu)
    for i in range(len(algorithm_names)):
        algorithm = menu.algorithms.byIndex(i)
        if algorithm:
            algorithm_names[i] = algorithm.name

TDF_NOTICE("hit CTRL + C to exit routine")

# Cache for multiple luminosity segments
lumi_segment_cache = []

# Get initial luminosity section
previous_ls = read_lumi_counter(args.device)
print "waiting for next luminosity segment..."

# Record to CSV file
if args.dump:
    args.dump.write(','.join([str(item) for item in ["lumi_segment/algo_rate"]+range(512)]))
    args.dump.write("\n")

with open("{0}.log".format(TDF_NAME), "w") as logger:
    TDF_NOTICE("start writing to log file", logger.name)
    logger.write("start logging counter missmatches...\n")
    logger.write(LumiSegment.header + "\n")
    try:
        while True:
            # Try not to exit on control hub read errors, try again...
            try:
                # Get current luminosity section
                current_ls = read_lumi_counter(args.device)

                # Do nothing until reaching a new luminosity segment
                if previous_ls != current_ls:

                    # Read all counters
                    lumi_segment = read_segment_counters(args.device, ls_number=previous_ls)
                    # Append counters to cache
                    lumi_segment_cache.append(lumi_segment)
                    # Record rates to CSV file
                    if args.dump:
                        args.dump.write(','.join([str(item) for item in [previous_ls] + lumi_segment.rates_before_prescaler]))
                        args.dump.write("\n")
                    # Strip older cache entries
                    if len(lumi_segment_cache) > args.stucked_cache_size:
                        lumi_segment_cache = lumi_segment_cache[-abs(args.stucked_cache_size):]

                    # Print table header
                    print LumiSegment.header
                    # List counters for selected algorithms
                    for index in args.index:
                        print lumi_segment.row(index, algorithm_names[index])

                    # Test 1
                    # Compare before/after counter values, must match.
                    if args.missmatches:
                        for index in range(len(lumi_segment.rates_before_prescaler)):
                            before_cnt = lumi_segment.rates_before_prescaler[index]
                            after_cnt = lumi_segment.rates_after_prescaler[index]
                            if before_cnt != after_cnt:
                                message = "before/after counter values not equal: {before_cnt} != {after_cnt}".format(**locals())
                                TDF_WARNING(message)
                                logger.write(message + "\n")
                                print lumi_segment.row(index, algorithm_names[index])
                                logger.write(lumi_segment.row(index, algorithm_names[index]) + "\n")

                    # Test 2
                    # Try to detect "stucked" counter values, over multiple past luminosity segements.
                    if args.stucked:
                        # Wait for cache to build up
                        if len(lumi_segment_cache) >= args.stucked_cache_size:
                            # Check every algorithm
                            for index in range(len(lumi_segment_cache[0].rates_after_prescaler)):
                                # Fetch rate counters history for algorithm <index>
                                history = [segment.rates_after_prescaler[index] for segment in lumi_segment_cache]
                                # Test for same values
                                if history == ([history[0]] * len(history)): # scheme [42,42,42] == ([42] * 3)
                                    if history[0] >= args.stucked_threshold:
                                        message = "detected potential stucked rate counters, algorithm {index}, const. values {history}, over past {args.stucked_cache_size} lumi segments.".format(**locals())
                                        TDF_WARNING(message)
                                        logger.write(message + "\n")
                                        for segment in lumi_segment_cache:
                                            print segment.row(index, algorithm_names[index])
                                            logger.write(segment.row(index, algorithm_names[index]) + "\n")

                # Store current luminosity segment number
                previous_ls = current_ls
                # Throttle monitoring rate
                time.sleep(args.interval)

            except uhal._core.exception, e:
                TDF_ERROR(e, "retrying...")
                time.sleep(1.)

    except KeyboardInterrupt:
        logger.write("stopped logging.\n")
        TDF_NOTICE("stoped writing to log file", logger.name)
        sys.exit(0)
