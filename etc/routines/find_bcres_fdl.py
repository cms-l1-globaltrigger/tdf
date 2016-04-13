# find_bcres_fdl.py
# Determine bcres FDL delay by iterating until a marker algorithm turns up correct.
from tdf.extern import argparse
from tdf.mp7.images import AlgoBxMemoryImage
from tdf.core.testvector import TestVector
import sys, os

DEFAULT_INPUT_DELAY = 9
DEFAULT_GTL_DELAY = 6
DEFAULT_RX_LINKS = '0-15'
DEFAULT_TX_LINKS = '0-3'
DEFAULT_TTC_BC0_BX = 3539

parser = argparse.ArgumentParser()
parser.add_argument('device')
parser.add_argument('testvector', metavar='<file>', type=os.path.abspath, help="test vector to be loaded into the TX buffers")
parser.add_argument('--clksrc', choices = ("external", "internal"), default = "internal", help = "clock source, default is 'internal'")
parser.add_argument('--delay', default=DEFAULT_INPUT_DELAY, metavar='<n>', type=int, help="delay in BX for incomming data in spy memory, default is '{DEFAULT_INPUT_DELAY}'".format(**locals()))
parser.add_argument('--ttc-bc0-bx', default=DEFAULT_TTC_BC0_BX, metavar='<n>', type=int, help="TTC_BC0_BX value, default is '{DEFAULT_TTC_BC0_BX}'".format(**locals()))

args = parser.parse_args(TDF_ARGS)

# Reset link's logic
mp7butler("reset", args.device, "--clksrc", args.clksrc)

# Loopback
mp7butler("txmgts", args.device, "--loopback", "--e", "0-15", "--pattern", "std")
mp7butler("rxmgts", args.device, "--e", "0-15")
mp7butler("rxalign", args.device, "--e", "0-15", "--to-bx", "8,4")

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

# Enable single event
image.set(valid_algo, valid_bx, 1)

# Write memory to firmware.
blockwrite(args.device, "gt_mp7_gtlfdl.algo_bx_mem", image.serialize())

## HB 2016-01-19: bcres_delay for FDL (= 25 [3564-3539 from mp7_ttc_decl.vhd] + 1 [bcres sync.] + "--delay" + 1 [algo-bx-mem output] + 1 [algo spy mem input])
write(args.device, "gt_mp7_frame.rb.dm.delay_bcres_fdl", 3564-args.ttc_bc0_bx + 1 + args.delay + 1 + 1)

# SPY2
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-spy.cfg")

# Dump FinOR memory
finor_dump = dump(args.device, "gt_mp7_frame.spymem2_finor")
# Apply logic offset to data
offset = DEFAULT_GTL_DELAY+args.delay
finor_values = finor_dump.data[offset:] + finor_dump.data[:offset] # compensate logic delay

print "found valid delay_bcres_fdl values:", ', '.join([str(i) for i, value in enumerate(finor_values) if value])

print "expected bx:", valid_bx, "(algorithm index {0})".format(valid_algo)
print "determinded bx:", finor_values.index(1)
print "delay_bcres_fdl:", read(args.device, "gt_mp7_frame.rb.dm.delay_bcres_fdl")
if valid_bx != finor_values.index(1):
    TDF_ERROR("offset", valid_bx - finor_values.index(1))
