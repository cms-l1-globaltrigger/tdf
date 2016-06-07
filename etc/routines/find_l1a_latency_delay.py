# find_l1a_latency_delay.py
# Find correct L1a latency delay
# Enable a single algorithm in a single BX, increament l1a_latency_delay item
# wait two lumi sections and check the post deadtime counter for the algorithm.
from tdf.extern import argparse
from tdf.core.testvector import TestVector
from tdf.mp7.images import AlgoBxMemoryImage
import sys, os
import time

DEFAULT_INPUT_DELAY = 9
DEFAULT_GTL_DELAY = 6
DEFAULT_TTC_BC0_BX = 3539

parser = argparse.ArgumentParser()
parser.add_argument('device')
parser.add_argument('testvector', metavar='<file>', type=os.path.abspath, help="test vector to be loaded into the TX buffers")
parser.add_argument('--clksrc', choices = ("external", "internal"), default = "external", help = "clock source, default is 'external'")
parser.add_argument('--delay', default=DEFAULT_INPUT_DELAY, metavar='<n>', type=int, help="delay in BX for incomming data in spy memory, default is '{DEFAULT_INPUT_DELAY}'".format(**locals()))
parser.add_argument('--ttc-bc0-bx', default=DEFAULT_TTC_BC0_BX, metavar='<n>', type=int, help="TTC_BC0_BX value, default is '{DEFAULT_TTC_BC0_BX}'".format(**locals()))
parser.add_argument('--offset', type=int, default=0, help="offset for incrementing l1a_latency")
parser.add_argument('--algorithm', type=int)
parser.add_argument('--bx', type=int)
parser.add_argument('--skip-setup', action='store_true')
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

  # Clear memories.
  clear(args.device, "gt_mp7_frame.spymem2_algos")
  clear(args.device, "gt_mp7_frame.spymem2_finor")

# Create new memory image.
image = AlgoBxMemoryImage()
image.setEnabled(False)

# Find first valid bx in testvector
tv = TestVector(args.testvector)
valid_bx = None
for bx, value in enumerate(tv.finor()):
    if value:
        valid_bx = bx
        break
if valid_bx is None:
    TDF_ERROR("no FinOR found in testvector", args.testvector)

# Get first event of bx (cast to binary string, find first '1')
valid_algo = "{0:0512b}".format(tv.algorithms()[valid_bx])[::-1].index('1')

if args.algorithm is not None:
    valid_algo = args.algorithm
if args.bx is not None:
    valid_bx = args.bx

# Enable single event
image.set(valid_algo, valid_bx, 1)

# Write memory to firmware.
blockwrite(args.device, "gt_mp7_gtlfdl.algo_bx_mem", image.serialize())

print "masking algo:", valid_algo, ", bx:", valid_bx

for delay in range(args.offset, 0xffff):
    print " => l1a_latency_delay:", delay
    write(args.device, 'gt_mp7_gtlfdl.l1a_latency_delay', delay)

    lumisec = read(args.device, 'gt_mp7_frame.rb.tcm_status.luminosity_seg_nr')
    print "current lumi section is:", lumisec
    print "waiting for start of next lumi section"

    while read(args.device, 'gt_mp7_frame.rb.tcm_status.luminosity_seg_nr') <= lumisec:
        time.sleep(22/4.)
    print

    lumisec = read(args.device, 'gt_mp7_frame.rb.tcm_status.luminosity_seg_nr')
    print "current lumi section is:", lumisec
    print "starting counting..."

    while read(args.device, 'gt_mp7_frame.rb.tcm_status.luminosity_seg_nr') <=	lumisec:
       	time.sleep(22/4.)
    print

    rate = blockread(args.device, 'gt_mp7_gtlfdl.rate_cnt_post_dead_time')
    print " => post dead time rate counter:", rate#, "for algo:", valid_algo

    rate = blockread(args.device, 'gt_mp7_gtlfdl.rate_cnt_after_prescaler')
    print " => after prescale rate counter:", rate#, "for algo:", valid_algo

    rate = blockread(args.device, 'gt_mp7_gtlfdl.rate_cnt_before_prescaler')
    print " => before prescaler rate counter:", rate#, "for algo:", valid_algo

    print "END"
    print
