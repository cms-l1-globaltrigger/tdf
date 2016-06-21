# lumi_counter_monitor.py
# Monitors luminosity segment counter and orbit counter.
# Provided for debuggign purpose.
from tdf.extern import argparse
from tdf.core import binutils
from tdf.core import TDF
from collections import namedtuple
import uhal
import time
import sys

LumiSegement = namedtuple('LumiSegement', 'ls_number, rate_before_prescale, rate_after_prescale, err_det')

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
parser.add_argument('-i', dest='interval', metavar='<f>', type=float, default=5., help="time interval, default 5.0 sec")
parser.add_argument('--missmatches', action='store_true', help="enable checks for counter missmatches")
parser.add_argument('--stucked', action='store_true', help="enable checks for stucked counters")
parser.add_argument('--stucked-cache', metavar='<n>', type=int, default=3, help="number of cached luminosity segment, default 3")
parser.add_argument('--stucked-threshold', metavar='<n>', type=int, default=10, help="threshold for detecting stucked counters, default >= 10")
parser.add_argument('--dump', metavar='<file>', type=argparse.FileType('w'), help="dump recorded after prescale rate counters to CSV formatted file")
args = parser.parse_args(TDF_ARGS)
# sort the indices
args.index.sort()

TDF_NOTICE("hit CTRL + C to exit routine")

# Cache data over multiple luminosity segments
cache = []

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
    logger.write("| LumiSegNr | rate_before_prescale | rate_after_prescale  | algo | err_det |\n")
    try:
        while True:
            # Try not to exit on control hub read errors, try again...
            try:
                # Get current luminosity section
                current_ls = read_lumi_counter(args.device)

                # Do nothing until reaching a new luminosity segment
                if previous_ls != current_ls:
                    rate_cnt_before_prescaler = blockread(args.device, "gt_mp7_gtlfdl.rate_cnt_before_prescaler")
                    rate_cnt_after_prescaler = blockread(args.device, "gt_mp7_gtlfdl.rate_cnt_after_prescaler")
                    err_det = read(args.device, "gt_mp7_frame.rb.tcm_status.err_det")
                    # Append current data to cache
                    cache.append(
                        LumiSegement(
                            previous_ls,
                            rate_cnt_before_prescaler,
                            rate_cnt_after_prescaler,
                            err_det
                        )
                    )
                    # Record rates to CSV file
                    if args.dump:
                        args.dump.write(','.join([str(item) for item in [previous_ls] + rate_cnt_before_prescaler]))
                        args.dump.write("\n")
                    # Strip older cache entries
                    if len(cache) > args.stucked_cache:
                        cache = cache[-abs(args.stucked_cache):]
                    print "| LumiSegNr | rate_before_prescale | rate_after_prescale  | algo | err_det |"
                    for index in args.index:
                        before_cnt = rate_cnt_before_prescaler[index]
                        after_cnt = rate_cnt_after_prescaler[index]
                        print "| {previous_ls:>9} | {before_cnt:>20} | {after_cnt:>20} | {index:>4} | {err_det:>7} |".format(**locals())

                    # Test 1
                    # Compare before/after counter values, must match.
                    if args.missmatches:
                        for index in range(len(rate_cnt_before_prescaler)):
                            before_cnt = rate_cnt_before_prescaler[index]
                            after_cnt = rate_cnt_after_prescaler[index]
                            if before_cnt != after_cnt:
                                message = "before/after counter values not equal: {before_cnt} != {after_cnt}".format(**locals())
                                TDF_WARNING(message)
                                logger.write(message)
                                logger.write("\n")
                                message = "| {previous_ls:>9} | {before_cnt:>20} | {after_cnt:>20} | {index:>4} | {err_det:>7} | COUNTER MISSMATCH".format(**locals())
                                print message
                                logger.write(message)
                                logger.write("\n")

                    # Test 2
                    # Try to detect "stucked" counter values, over multiple past luminosity segements.
                    if args.stucked:
                        # Wait for cache to build up
                        if len(cache) >= args.stucked_cache:
                            # Check every algorithm
                            for index in range(len(rate_cnt_after_prescaler)):
                                # Fetch rate counters history for algorithm <index>
                                history = [entry.rate_after_prescale[index] for entry in cache]
                                # Test for same values
                                if history == ([history[0]] * len(history)): # scheme [42,42,42] == ([42] * 3)
                                    if history[0] >= args.stucked_threshold:
                                        message = "detected potential stucked rate counters, algorithm {index}, const. values {history}, over past {args.stucked_cache} lumi segments.".format(**locals())
                                        TDF_WARNING(message)
                                        logger.write(message)
                                        logger.write("\n")
                                        for entry in cache:
                                            ls_number = entry.ls_number
                                            before_cnt = entry.rate_before_prescale[index]
                                            after_cnt = entry.rate_after_prescale[index]
                                            err_det = entry.err_det
                                            message = "| {ls_number:>9} | {before_cnt:>20} | {after_cnt:>20} | {index:>4} | {err_det:>7} | STUCKED COUNTER?".format(**locals())
                                            print message
                                            logger.write(message)
                                            logger.write("\n")

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
