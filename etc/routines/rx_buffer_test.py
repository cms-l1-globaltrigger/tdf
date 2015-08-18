# Tx_buffer function test with rx_pattern input
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

def result_area():
    from datetime import datetime
    dirname = "{0}_{1}".format(TDF_NAME, datetime.strftime(datetime.now(), "%Y-%m-%dT%H-%M-%S"))
    return dirname

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
parser.add_argument('--loopback', action = 'store_true', help = "run internal loopback mode (without cable)")
parser.add_argument('--pattern', default = ':counter', metavar = '<source>', help = "source test vector to be loaded into the TX buffers (or ':counter' for generic counter, default)")
parser.add_argument('--delay', default = DEFAULT_INPUT_DELAY, metavar = '<n>', type = int, help = "delay in BX for incomming data in spy memory, default is '{DEFAULT_INPUT_DELAY}'".format(**locals()))
parser.add_argument('--clksrc', choices = ("external", "internal"), default = "internal", help = "clock source, default is 'internal'")
parser.add_argument('--rx-links', '--links', default = DEFAULT_RX_LINKS, metavar = '<n-m>', help = "RX links to be configured, default is '{DEFAULT_RX_LINKS}'".format(**locals()))
parser.add_argument('--tx-links', default = DEFAULT_TX_LINKS, metavar = '<n-m>', help = "TX links to be configured, default is '{DEFAULT_TX_LINKS}'".format(**locals()))
parser.add_argument('--gtl-latency', default = DEFAULT_GTL_LATENCY, metavar = '<n>', type = int, help = "set latency for GTL logic in BX, default is '{DEFAULT_GTL_LATENCY}'".format(**locals()))
parser.add_argument('--size', default = DEFAULT_SIZE, metavar = '<n>', type = int, help = "number of BX to be compared, default is '{DEFAULT_INPUT_DELAY}'".format(**locals()))
parser.add_argument('--align-to', default = None, help = "overwrite link alignment eg. 38,5 (bx, cycle)")
parser.add_argument('--capture-buffers', action = 'store_true')
parser.add_argument('--configure-amc13', action = 'store_true')
parser.add_argument('--run-unittests', action = 'store_true')
parser.add_argument('-o', '--output-dir', default = result_area(), help = "name of output directory")
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

# Setup for loopback.
mp7butler("mgts", args.device, "--loopback", "--enablelinks", args.rx_links, "--align-to", args.align_to or "8,5")

data_filename = args.pattern

mp7butler("buffers", args.device, "loopPlay", "--enablelinks", args.rx_links, "--inject", "file://{data_filename}".format(**locals()))

# Reset and setup the GT logic.
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-reset.cfg")
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-mux-tx-buffer.cfg")
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-delay-manager-values.cfg")

# Clear the memories.
clear(args.device, "gt_mp7_frame.simspymem")
clear(args.device, "gt_mp7_frame.spymem2_algos")
clear(args.device, "gt_mp7_frame.spymem2_finor")

# Setup GTL algorithm masks.
run_routine("enable_algo_bx_mem", args.device)

# Start spy
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-spy.cfg")

# Dump the memories.
dump(args.device, "gt_mp7_frame.simspymem", outfile = TDF_NAME + "_simspymem.dat")
algo_dump = dump(args.device, "gt_mp7_frame.spymem2_algos", outfile = TDF_NAME + "_spymem2_algos.dat")
dump(args.device, "gt_mp7_frame.spymem2_finor", outfile = TDF_NAME + "_spymem2_finor.dat")


# Dumping TX buffer content
mp7butler("buffers", args.device, "captureTx", "--enablelinks",  args.tx_links)
mp7butler("capture", args.device, "--enablelinks", args.tx_links, "--outputpath", "tx_buffer_dump")



