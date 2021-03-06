# Tx_buffer function test
# for MP7 firmware >= 1.6.0
# BA 2015-05-27 adaptions for esums commissioning

from tdf.extern import argparse
from tdf.core.testvector import TestVector
import os, re
import time
import datetime

DEFAULT_INPUT_DELAY = 11
DEFAULT_GTL_LATENCY = 6
DEFAULT_SIZE = 170
DEFAULT_RX_LINKS = '0-15'
DEFAULT_TX_LINKS = '0-3'
DEFAULT_CAP = 0

def result_area():
    from datetime import datetime
    dirname = "{0}_{1}".format(TDF_NAME, datetime.strftime(datetime.now(), "%Y-%m-%dT%H-%M-%S"))
    return dirname

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
parser.add_argument('--pattern', default = ':counter', metavar = '<source>', help = "source test vector to be loaded into the TX buffers (or ':counter' for generic counter, default)")
parser.add_argument('--delay', default = DEFAULT_INPUT_DELAY, metavar = '<n>', type = int, help = "delay in BX for incomming data in spy memory, default is '{DEFAULT_INPUT_DELAY}'".format(**locals()))
parser.add_argument('--clksrc', choices = ("external", "internal"), default = "internal", help = "clock source, default is 'internal'")
parser.add_argument('--rx-links', '--links', default = DEFAULT_RX_LINKS, metavar = '<n-m>', help = "RX links to be configured, default is '{DEFAULT_RX_LINKS}'".format(**locals()))
parser.add_argument('--tx-links', default = DEFAULT_TX_LINKS, metavar = '<n-m>', help = "TX links to be configured, default is '{DEFAULT_TX_LINKS}'".format(**locals()))
parser.add_argument('--gtl-latency', default = DEFAULT_GTL_LATENCY, metavar = '<n>', type = int, help = "set latency for GTL logic in BX, default is '{DEFAULT_GTL_LATENCY}'".format(**locals()))
parser.add_argument('--size', default = DEFAULT_SIZE, metavar = '<n>', type = int, help = "number of BX to be compared, default is '{DEFAULT_SIZE}'".format(**locals()))
parser.add_argument('--algo-bx-mask', default = None, metavar = '<file>', help = "load algorithm BX mask from file")
parser.add_argument('--capture-buffers', action = 'store_true')
parser.add_argument('--run-unittests', action = 'store_true')
parser.add_argument('-o', '--output-dir', default = result_area(), help = "name of output directory")
parser.add_argument('--comp-pattern', default = None, metavar = '<source>', help = "source test vector to compare the results")
parser.add_argument('--cap', default = DEFAULT_CAP, metavar = '<n>', type = int, help = "delay in BX for capturing the tx buffer output, default is '{DEFAULT_CAP}'".format(**locals()))
args = parser.parse_args(TDF_ARGS)

args.pattern = os.path.abspath(args.pattern)
args.comp_pattern = os.path.abspath(args.comp_pattern)

if not os.path.isdir(args.output_dir):
    print "creating result area directory:", args.output_dir
    os.makedirs(args.output_dir)
    os.chdir(args.output_dir)

# Reset link's logic
mp7butler("reset", args.device, "--clksrc", args.clksrc)

# Run unittests to RESET and verify integrity.
if args.run_unittests:
    os.makedirs(args.output_dir)
    os.chdir(args.output_dir)

# Setup for loopback or cable mode.
#if args.loopback:
    #mp7butler("mgts", args.device, "--loopback", "--enablelinks", args.rx_links, "--align-to", args.align_to or "9,5")
#else:
    #mp7butler("mgts", args.device, "--enablelinks", args.rx_links, "--align-to", args.align_to or "38,5")

#data_filename = TDF_NAME + "_in.dat" # Returns "tagged" filename tdf_simple_buffer_loopback_in.dat
#buffgen(args.pattern, board = args.device, outfile = data_filename)
data_filename = args.pattern

mp7butler("buffers", args.device, "algoPlay", "--e", args.rx_links, "--inject", "file://{data_filename}".format(**locals()))

if args.capture_buffers:
    mp7butler("buffers", args.device, "captureRxTxStb")   # buffer setting
    mp7butler("capture", args.device)                  # buffer capture

# Reset and setup the GT logic.
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/reset.cfg")

# Clear the memories.
clear(args.device, "gt_mp7_frame.simspymem")
clear(args.device, "gt_mp7_frame.spymem2_algos")
clear(args.device, "gt_mp7_frame.spymem2_finor")

# Setup GTL algorithm masks.
if args.algo_bx_mask:
    run_routine("load_bx_masks", args.device, args.algo_bx_mask)
else:
    run_routine("enable_algo_bx_mem", args.device)

# Start spy
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/spy_next.cfg")

# Dump the memories.
dump(args.device, "gt_mp7_frame.simspymem", outfile = TDF_NAME + "_simspymem.dat")
algo_dump = dump(args.device, "gt_mp7_frame.spymem2_algos", outfile = TDF_NAME + "_spymem2_algos.dat")
dump(args.device, "gt_mp7_frame.spymem2_finor", outfile = TDF_NAME + "_spymem2_finor.dat")

if args.comp_pattern:
    # Compare the dumps.
    compare(args.device, "gt_mp7_frame.simspymem", TDF_NAME + "_simspymem.dat", args.comp_pattern, offset = args.delay, size = args.size)
    compare(args.device, "gt_mp7_frame.spymem2_algos", TDF_NAME + "_spymem2_algos.dat", args.comp_pattern, offset = args.delay + args.gtl_latency, size = args.size)
    compare(args.device, "gt_mp7_frame.spymem2_finor", TDF_NAME + "_spymem2_finor.dat", args.comp_pattern, offset = args.delay + args.gtl_latency, size = args.size)

    # Read in test vector.
    tv = TestVector(open(args.comp_pattern))

    # Overall delay.
    delay_all = args.delay + args.gtl_latency

    # Read the emulator log file if available (for active algorithms and names).
    logfile = args.comp_pattern.replace(".txt", ".log")
    if os.path.isfile(logfile):
        lines = open(logfile).readlines()
        for i in range(len(lines)):
            if lines[i].strip() == "=========== Summary of results ==========":
                print lines[i].strip()
                print "bit\tL1A/tv\tL1A/hw\tresult\tname\t(tv=testvector, hw=hardware readout)"
                for line in lines[i:]:
                    result = re.match("^\s+(\d+)\s+(\d+)\s+(L1_[a-zA-Z0-9_]+)", line)
                    if result:
                        bit, l1a, name = result.groups()
                        index = int(bit)
                        l1a_hw = 0
                        for algorithm in algo_dump.algorithms()[delay_all:delay_all+args.size]:
                            l1a_hw += (algorithm >> index) & 0x1
                        l1a_tv = 0
                        for algorithm in tv.algorithms()[:args.size]:
                            l1a_tv += (algorithm >> index) & 0x1
                        result = "OK" if l1a_tv == l1a_hw else "ERROR"
                        print "{bit}\t{l1a_tv}\t{l1a_hw}\t{result}\t{name}".format(**locals())
                break

# Dumping TX buffer content
mp7butler("buffers", args.device, "captureTx", "--e",  args.tx_links, "--cap", args.cap)
mp7butler("capture", args.device, "--e", args.tx_links, "--outputpath", "tx_buffer_dump")
