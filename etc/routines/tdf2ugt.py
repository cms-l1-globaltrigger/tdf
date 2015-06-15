# TDF to uGT
#
# This routine sets up data transfere from a TDF MP7 module (source) to a uGT
# MP7 module (target).
#
# *Prerequisites*
#   Connect the 1:1 pstched MTP48 conenction from TDF TX1 to uGT RX1
#

from tdf.extern import argparse
from tdf.core import binutils
import sys, os

# -----------------------------------------------------------------------------
#  Constants
# -----------------------------------------------------------------------------

DEFAULT_SOURCE = 'tdf_mp7.6'
DEFAULT_TARGET = 'gt_mp7.1'
DEFAULT_PATTERN = ':counter'
DEFAULT_INPUT_DELAY = 11
DEFAULT_GTL_LATENCY = 6
DEFAULT_LINKS = '0-15'
MODEL = 'xe'

# -----------------------------------------------------------------------------
#  Parsing arguments
# -----------------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument('--source', default = DEFAULT_SOURCE, help = "source TDF device name, default is `tdf_mp7.6'")
parser.add_argument('--target', default = DEFAULT_TARGET, help = "target uGT device name, default is `gt_mp7.1'")
parser.add_argument('--pattern', default = DEFAULT_PATTERN, help = "pattern file or :counter, :random pattern, default is `:counter'")
parser.add_argument('--links', default = DEFAULT_LINKS, help = "number of links to be configured")
parser.add_argument('--delay', default = DEFAULT_INPUT_DELAY, type = int, help = "input delay")
parser.add_argument('--gtl-latency', default = DEFAULT_GTL_LATENCY, metavar = '<n>', type = int, help = "set latency for GTL logic (for analysis only)")
parser.add_argument('--fix-latency', nargs = 2, action = 'append', metavar = '<n>', help = "set latency for a range of links (links, latency)")
parser.add_argument('--bcres-delay', metavar = '<n>', type = binutils.integer, help = "overwrite BC_RES delay applied by configuration files")
parser.add_argument('--size', default = 170, type = int, help = "number of BX to be compared")
args = parser.parse_args(TDF_ARGS)

# -----------------------------------------------------------------------------
#  Enable clocks on AMC13
# -----------------------------------------------------------------------------
configure("amc13_k7.13", os.path.join(TDF.ROOT_DIR, "etc/config/amc13xg/default_k7.cfg"))

# -----------------------------------------------------------------------------
#  Reset devices to use external clock
# -----------------------------------------------------------------------------
mp7butler("reset", args.source, "--clksrc", "external", "-m", MODEL)
mp7butler("reset", args.target, "--clksrc", "external", "-m", MODEL)

# -----------------------------------------------------------------------------
#  Run unittests to RESET and verify integrity.
# -----------------------------------------------------------------------------
run_unittest(args.source, "clk40_locked")
run_unittest(args.source, "bc0_locked")
run_unittest(args.target, "clk40_locked")
run_unittest(args.target, "bc0_locked")
run_unittest(args.target, "sw_reset")
run_unittest(args.target, "tcm_locked")

# -----------------------------------------------------------------------------
#  Setup TDF device, load pattern and run algoPlay
# -----------------------------------------------------------------------------
configure(args.source, os.path.join(TDF.ROOT_DIR, "etc/config/tdf_mp7/tdf.cfg"))
load(args.source, "tdf_mp7.simspymem", args.pattern)
mp7butler("buffers", args.source, "algoPlay", "--enablelinks", args.links, "-m", MODEL)

# -----------------------------------------------------------------------------
#  Align GT links (twice to trick powerup problems...)
# -----------------------------------------------------------------------------
for i in range(2):
    if args.fix_latency:
        # Apply fixed latencies.
        for links, latency in args.fix_latency:
            mp7butler("mgts", args.target, "--forcepattern", "--fix-latency", latency, "--enablelinks", args.links, "-m", MODEL)
    else:
        mp7butler("mgts", args.target, "--forcepattern", "--enablelinks", args.links, "-m", MODEL)

# -----------------------------------------------------------------------------
#  Setup GT logic
# -----------------------------------------------------------------------------
configure(args.target, os.path.join(TDF.ROOT_DIR, "etc/config/gt_mp7/cfg-140/mp7-reset.cfg"))
configure(args.target, os.path.join(TDF.ROOT_DIR, "etc/config/gt_mp7/cfg-140/mp7-mux-tx-buffer.cfg"))
configure(args.target, os.path.join(TDF.ROOT_DIR, "etc/config/gt_mp7/cfg-140/mp7-delay-manager-values.cfg"))
# Overwrite BC_res delay on demand.
if args.bcres_delay is not None:
    TDF_WARNING("overwriting BCRES_DELAY:", args.bcres_delay, "BX")
    write(args.target, 'gt_mp7_frame.rb.dm.delay_bcres', args.bcres_delay)

# -----------------------------------------------------------------------------
#  Clear the memories
# -----------------------------------------------------------------------------
clear(args.target, "gt_mp7_frame.simspymem")
clear(args.target, "gt_mp7_frame.spymem2_algos")
clear(args.target, "gt_mp7_frame.spymem2_finor")

# -----------------------------------------------------------------------------
#  Start spy
# -----------------------------------------------------------------------------
configure(args.target, os.path.join(TDF.ROOT_DIR, "etc/config/gt_mp7/cfg-140/mp7-spy.cfg"))

# -----------------------------------------------------------------------------
#  Dump input data
# -----------------------------------------------------------------------------
dump(args.target, "gt_mp7_frame.simspymem", outfile = TDF_NAME + "_simspymem.dat")

# Bail out on :counter or :zero pattern.
if args.pattern.startswith(':'):
    TDF_WARNING("no data comparison for", args.pattern, "pattern available")
    sys.exit()

# -----------------------------------------------------------------------------
#  Dump output data
# -----------------------------------------------------------------------------
dump(args.target, "gt_mp7_frame.spymem2_algos", outfile = TDF_NAME + "_spymem2_algos.dat")
dump(args.target, "gt_mp7_frame.spymem2_finor", outfile = TDF_NAME + "_spymem2_finor.dat")

# -----------------------------------------------------------------------------
#  Compare the dumps
# -----------------------------------------------------------------------------
compare(args.target, "gt_mp7_frame.simspymem", TDF_NAME + "_simspymem.dat", args.pattern, offset = args.delay, size = args.size)
compare(args.target, "gt_mp7_frame.spymem2_algos", TDF_NAME + "_spymem2_algos.dat", args.pattern, offset = args.delay + args.gtl_latency, size = args.size)
compare(args.target, "gt_mp7_frame.spymem2_finor", TDF_NAME + "_spymem2_finor.dat", args.pattern, offset = args.delay + args.gtl_latency, size = args.size)

# -----------------------------------------------------------------------------
#  Dump TX buffers
# -----------------------------------------------------------------------------
mp7butler("buffers", args.target, "captureTx", "--enablelinks", "0-3", "-m", MODEL)
mp7butler("capture", args.target,"-m", MODEL)
TDF_WARNING("see data/tx_summary.txt for algorithm/finor data")
