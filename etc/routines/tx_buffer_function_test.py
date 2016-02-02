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
DEFAULT_HW_DELAY = 0
DEFAULT_TTC_BC0_BX = 3539

def result_area():
    from datetime import datetime
    dirname = "{0}_{1}".format(TDF_NAME, datetime.strftime(datetime.now(), "%Y-%m-%dT%H-%M-%S"))
    return dirname

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
parser.add_argument('--loopback', action = 'store_true', help = "run internal loopback mode (without cable)")
parser.add_argument('--pattern', default = ':counter', metavar = '<source>', help = "source test vector to be loaded into the TX buffers (or ':counter' for generic counter, default)")
parser.add_argument('--delay', default = DEFAULT_INPUT_DELAY, metavar = '<n>', type = int, help = "delay in BX for incomming data in spy memory, default is '{DEFAULT_INPUT_DELAY}'".format(**locals()))
parser.add_argument('--hw-delay', default = DEFAULT_HW_DELAY, metavar = '<n>', type = int, help = "delay in BX for incomming data, default is '{DEFAULT_HW_DELAY}'".format(**locals()))
parser.add_argument('--clksrc', choices = ("external", "internal"), default = "internal", help = "clock source, default is 'internal'")
parser.add_argument('--rx-links', '--links', default = DEFAULT_RX_LINKS, metavar = '<n-m>', help = "RX links to be configured, default is '{DEFAULT_RX_LINKS}'".format(**locals()))
parser.add_argument('--tx-links', default = DEFAULT_TX_LINKS, metavar = '<n-m>', help = "TX links to be configured, default is '{DEFAULT_TX_LINKS}'".format(**locals()))
parser.add_argument('--gtl-latency', default = DEFAULT_GTL_LATENCY, metavar = '<n>', type = int, help = "set latency for GTL logic in BX, default is '{DEFAULT_GTL_LATENCY}'".format(**locals()))
parser.add_argument('--size', default = DEFAULT_SIZE, metavar = '<n>', type = int, help = "number of BX to be compared, default is '{DEFAULT_INPUT_DELAY}'".format(**locals()))
parser.add_argument('--align-to', default = None, help = "overwrite link alignment eg. 38,5 (bx, cycle)")
parser.add_argument('--algo-bx-mask', default = None, metavar = '<file>', help = "load algorithm BX mask from file")
parser.add_argument('--finor-veto-masks', default = None, metavar = '<file>', help = "load finor veto masks from file")
parser.add_argument('--ttc-bc0-bx', default = DEFAULT_TTC_BC0_BX, metavar = '<n>', type = int, help = "TTC_BC0_BX value, default is '{DEFAULT_TTC_BC0_BX}'".format(**locals()))
parser.add_argument('--capture-buffers', action = 'store_true')
parser.add_argument('--configure-amc13', action = 'store_true')
parser.add_argument('--run-unittests', action = 'store_true')
parser.add_argument('-o', '--output-dir', default = result_area(), help = "name of output directory")
parser.add_argument('--cap', default = DEFAULT_CAP, metavar = '<n>', type = int, help = "delay in BX for capturing the tx buffer output, default is '{DEFAULT_CAP}'".format(**locals()))
args = parser.parse_args(TDF_ARGS)

args.pattern = os.path.abspath(args.pattern)

if not os.path.isdir(args.output_dir):
    print "creating result area directory:", args.output_dir
    os.makedirs(args.output_dir)
    os.chdir(args.output_dir)

### Enable clocks on AMC13
if args.configure_amc13:
    configure("amc13_k7.13", os.path.join(TDF.ROOT_DIR, "etc/config/amc13xg/default_k7.cfg"))

# Reset link's logic
mp7butler("reset", args.device, "--clksrc", args.clksrc)

# Run unittests to RESET and verify integrity.
if args.run_unittests:
    os.makedirs(args.output_dir)
    os.chdir(args.output_dir)

# Setup for loopback or cable mode.
if args.loopback:
    mp7butler("mgts", args.device, "--loopback", "--e", args.rx_links, "--align-to", args.align_to or "8,5")
else:
    mp7butler("mgts", args.device, "--e", args.rx_links, "--align-to", args.align_to or "38,5")

data_filename = TDF_NAME + "_in.dat" # Returns "tagged" filename tdf_simple_buffer_loopback_in.dat
buffgen(args.pattern, board = args.device, outfile = data_filename)

if args.loopback:
    mp7butler("buffers", args.device, "loopPlay", "--e", args.rx_links, "--inject", "file://{data_filename}".format(**locals()))
else:
    mp7butler("buffers", args.device, "loopPlay")

if args.capture_buffers:
    mp7butler("buffers", args.device, "captureRxTxStb")   # buffer setting
    mp7butler("capture", args.device)                  # buffer capture

# Reset and setup the GT logic.
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-reset.cfg")
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-mux-tx-buffer.cfg")
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-delay-manager-values.cfg")

if args.hw_delay:
    write(args.device, "gt_mp7_frame.rb.dm.delay_muons", args.hw_delay)
    write(args.device, "gt_mp7_frame.rb.dm.delay_eg", args.hw_delay)
    write(args.device, "gt_mp7_frame.rb.dm.delay_tau", args.hw_delay)
    write(args.device, "gt_mp7_frame.rb.dm.delay_jet", args.hw_delay)
    write(args.device, "gt_mp7_frame.rb.dm.delay_ett", args.hw_delay)
    write(args.device, "gt_mp7_frame.rb.dm.delay_ht", args.hw_delay)
    write(args.device, "gt_mp7_frame.rb.dm.delay_etm", args.hw_delay)
    write(args.device, "gt_mp7_frame.rb.dm.delay_htm", args.hw_delay)
    write(args.device, "gt_mp7_frame.rb.dm.delay_ext_con", args.hw_delay)

# Clear the memories.
clear(args.device, "gt_mp7_frame.simspymem")
clear(args.device, "gt_mp7_frame.spymem2_algos")
clear(args.device, "gt_mp7_frame.spymem2_finor")

# Setup GTL algorithm masks.
if args.algo_bx_mask:
    run_routine("load_bx_masks", args.device, args.algo_bx_mask)
else:
    run_routine("enable_algo_bx_mem", args.device)

# Setup finor/veto masks.
if args.finor_veto_masks:
    run_routine("load_finor_veto_masks", args.device, args.finor_veto_masks)

## HB 2016-01-19: bcres_delay for FDL (= 25 [3564-3539 from mp7_ttc_decl.vhd] + 1 [bcres sync.] + "--delay" + 1 [algo-bx-mem output] + 1 [algo spy mem input])
write(args.device, "gt_mp7_frame.rb.dm.delay_bcres_fdl", 3564-args.ttc_bc0_bx + 1 + args.delay + 1 + 1)

## HB 2016-01-19: test for finor and veto masks
#write(args.device, "gt_mp7_gtlfdl.masks", 0)

# Start spy
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-spy.cfg")

# Dump the memories.
dump(args.device, "gt_mp7_frame.simspymem", outfile = TDF_NAME + "_simspymem.dat")
algo_dump = dump(args.device, "gt_mp7_frame.spymem2_algos", outfile = TDF_NAME + "_spymem2_algos.dat")
dump(args.device, "gt_mp7_frame.spymem2_finor", outfile = TDF_NAME + "_spymem2_finor.dat")

if args.pattern not in (':counter', ':zero'):
    # Compare the dumps.
    compare(args.device, "gt_mp7_frame.simspymem", TDF_NAME + "_simspymem.dat", args.pattern, offset = args.delay, size = args.size)
    compare(args.device, "gt_mp7_frame.spymem2_algos", TDF_NAME + "_spymem2_algos.dat", args.pattern, offset = args.delay + args.gtl_latency, size = args.size)
    compare(args.device, "gt_mp7_frame.spymem2_finor", TDF_NAME + "_spymem2_finor.dat", args.pattern, offset = args.delay + args.gtl_latency, size = args.size)

    # Read in test vector.
    tv = TestVector(open(args.pattern))

    # Overall delay.
    delay_all = args.delay + args.gtl_latency

    # Read the emulator log file if available (for active algorithms and names).
    logfile = args.pattern.replace(".txt", ".log")
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
