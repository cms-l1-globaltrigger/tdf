# find_l1a_latency_delay.py
# Find correct L1a latency delay
# Enable a single algorithm in a single BX, increament l1a_latency_delay item
# wait two lumi sections and check the post deadtime counter for the algorithm.
#
# Note: this will only work at P5 together with TCDS
#

from tdf.extern import argparse
from tdf.core.testvector import TestVector
from tdf.mp7.images import AlgoBxMemoryImage
import sys, os
import time

DEFAULT_INPUT_DELAY = 9
DEFAULT_GTL_DELAY = 6
DEFAULT_TTC_BC0_BX = 3539

def tcm_orbit_nr(device):
    """Returns 64 bit orbit number."""
    orbit_nr_l = read(device, 'gt_mp7_frame.rb.tcm_status.orbit_nr_l')
    orbit_nr_h = read(device, 'gt_mp7_frame.rb.tcm_status.orbit_nr_h')
    return (orbit_nr_h << 32) | orbit_nr_l

def tcm_luminosity_seg_nr(device):
    """Returns luminosity segment number."""
    return read(device, 'gt_mp7_frame.rb.tcm_status.luminosity_seg_nr')

def seconds_left(orbit_nr):
    LhcClockFrequency = 40.07897e6
    OrbitsPerLuminositySegment = 2 ** 18
    MaximumCounts = 3564 * OrbitsPerLuminositySegment
    LuminositySegmentInSeconds = MaximumCounts / LhcClockFrequency
    return LuminositySegmentInSeconds * (1. - (orbit_nr % OrbitsPerLuminositySegment) / float(OrbitsPerLuminositySegment))

def wait_next_lumi(device):
    orbit_nr = tcm_orbit_nr(device)
    seconds = seconds_left(orbit_nr)
    print "waiting for next luminosity segment (in {seconds} sec)...".format(**locals()),
    verbose_wait(seconds)
    print

def verbose_wait(seconds, step=1.0):
    timeout = float(seconds)
    while timeout >= 0.0:
        sys.stdout.write('.')
        sys.stdout.flush()
        time.sleep(step)
        timeout = timeout - step

parser = argparse.ArgumentParser()
parser.add_argument('device')
parser.add_argument('testvector', metavar='<file>', type=os.path.abspath, help="test vector to be loaded into the TX buffers")
parser.add_argument('--clksrc', choices = ("external", "internal"), default = "external", help = "clock source, default is 'external'")
parser.add_argument('--delay', default=DEFAULT_INPUT_DELAY, metavar='<n>', type=int, help="delay in BX for incomming data in spy memory, default is '{DEFAULT_INPUT_DELAY}'".format(**locals()))
parser.add_argument('--ttc-bc0-bx', default=DEFAULT_TTC_BC0_BX, metavar='<n>', type=int, help="TTC_BC0_BX value, default is '{DEFAULT_TTC_BC0_BX}'".format(**locals()))
parser.add_argument('--offset', type=int, default=0, help="offset for incrementing l1a_latency")
parser.add_argument('--algorithm', required=True, type=int, help="manual set algorithm index")
parser.add_argument('--bx', required=True, type=int, help="manual set bunch crossing position")
parser.add_argument('--skip-setup', action='store_true', help="skip reset and configuration of device")
args = parser.parse_args(TDF_ARGS)

if not args.skip_setup:
    # Reset link's logic
    mp7butler("reset", args.device, "--clksrc", args.clksrc, '--clkcfg', 'default-ext')

    # Loopback
    mp7butler("txmgts", args.device, "--loopback", "--e", "0-15", "--pattern", "std")
    mp7butler("rxmgts", args.device, "--e", "0-15")
    mp7butler("rxalign", args.device, "--e", "0-15", "--to-bx", "9,5")

    # Load buffers
    data_filename = TDF_NAME + "_in.dat"
    buffgen(args.testvector, board = args.device, outfile = data_filename)
    mp7butler("buffers", args.device, "loopPlay", "--e", "8,4", "--inject", "file://{data_filename}".format(**locals()))

    # Reset and setup the GT logic.
    configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-reset.cfg")
    configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-mux-tx-buffer.cfg")
    configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-delay-manager-values.cfg")

# Create new memory image.
image = AlgoBxMemoryImage()
image.setEnabled(False)

# Enable single event
image.set(args.algorithm, args.bx, 1)

# Write memory to firmware.
blockwrite(args.device, "gt_mp7_gtlfdl.algo_bx_mem", image.serialize())

lumiseg = tcm_luminosity_seg_nr(args.device)
TDF_NOTICE("current luminosity segment is:", lumiseg)
TDF_NOTICE("starting to increment l1a_latency_delay at next luminosity segment")
wait_next_lumi(args.device)

for delay in range(args.offset, 0xffff):
    print '-' * 80
    lumiseg = tcm_luminosity_seg_nr(args.device)
    write(args.device, 'gt_mp7_gtlfdl.l1a_latency_delay', delay)
    TDF_NOTICE("algorithm         :", args.algorithm)
    TDF_NOTICE("bx                :", args.bx)
    TDF_NOTICE("l1a_latency_delay :", delay)
    TDF_NOTICE("current lumi seg. :", lumiseg)

    wait_next_lumi(args.device)

    lumiseg_new = tcm_luminosity_seg_nr(args.device)

    before_prescale_rate = blockread(args.device, 'gt_mp7_gtlfdl.rate_cnt_before_prescaler')
    after_prescale_rate = blockread(args.device, 'gt_mp7_gtlfdl.rate_cnt_after_prescaler')
    post_dead_time_rate = blockread(args.device, 'gt_mp7_gtlfdl.rate_cnt_post_dead_time')

    TDF_NOTICE("current lumi seg. :", lumiseg_new)
    TDF_INFO(" => before prescaler rate counter:", before_prescale_rate[args.algorithm])
    TDF_INFO(" => after prescale rate counter:", after_prescale_rate[args.algorithm])
    TDF_NOTICE(" => post dead time rate counter:", post_dead_time_rate[args.algorithm])
    if post_dead_time_rate[args.algorithm]:
        TDF_NOTICE("found rate with l1a_latency_delay of:", delay)
    print
