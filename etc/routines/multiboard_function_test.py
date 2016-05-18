# multiboard_function_test

from tdf.extern import argparse
from tdf.core.testvector import TestVector
from tdf.core.xmlmenu import XmlMenu
import sys, os, re
import time
from datetime import datetime

DEFAULT_INPUT_DELAY = 8
DEFAULT_GTL_LATENCY = 6
DEFAULT_SIZE = 170
DEFAULT_RX_LINKS = '0-15'
DEFAULT_TX_LINKS = '0-3'
DEFAULT_CAP = 0
DEFAULT_HW_DELAY = 0
DEFAULT_TTC_BC0_BX = 3539
DEFAULT_DEVICES = {
    0: 'gt_mp7.1',
    1: 'gt_mp7.2',
    2: 'gt_mp7.3',
    3: 'gt_mp7.4',
    4: 'gt_mp7.5',
    5: 'gt_mp7.6',
}

def get_modules(menu):
    """Returns dict of modules ids and assigned algorithm names."""
    modules = {}
    for algorithm in menu.algorithms:
        module_id = algorithm.module_id
        if module_id not in modules.keys():
            modules[module_id] = []
        modules[module_id].append(algorithm)
    return modules

parser = argparse.ArgumentParser()
parser.add_argument('menu', metavar='<menu>', type=os.path.abspath, help="XML menu file")
parser.add_argument('testvector', metavar='<testvector>', type=os.path.abspath, help="test vector to be loaded into the TX buffers")
parser.add_argument('--clksrc', choices=('external', 'internal'), default='external', help="clock source, default is 'external'")
parser.add_argument('--loopback', action='store_true', help="run internal loopback mode (without cable)")
parser.add_argument('--rx-links', '--links', default=DEFAULT_RX_LINKS, metavar='<n-m>', help="RX links to be configured, default is '{DEFAULT_RX_LINKS}'".format(**locals()))
parser.add_argument('--tx-links', default=DEFAULT_TX_LINKS, metavar='<n-m>', help="TX links to be configured, default is '{DEFAULT_TX_LINKS}'".format(**locals()))
parser.add_argument('--delay', default=DEFAULT_INPUT_DELAY, metavar='<n>', type=int, help="delay in BX for incomming data in spy memory, default is '{DEFAULT_INPUT_DELAY}'".format(**locals()))
parser.add_argument('--hw-delay', default=DEFAULT_HW_DELAY, metavar='<n>', type=int, help="delay in BX for incomming data, default is '{DEFAULT_HW_DELAY}'".format(**locals()))
parser.add_argument('--gtl-latency', default=DEFAULT_GTL_LATENCY, metavar='<n>', type=int, help="set latency for GTL logic in BX, default is '{DEFAULT_GTL_LATENCY}'".format(**locals()))
parser.add_argument('--size', default=DEFAULT_SIZE, metavar='<n>', type=int, help="number of BX to be compared, default is '{DEFAULT_INPUT_DELAY}'".format(**locals()))
parser.add_argument('--align-to', default=None, help="overwrite link alignment eg. 38,5 (bx, cycle)")
parser.add_argument('--algo-bx-mask', default=None, metavar='<file>', help="load algorithm BX mask from file")
parser.add_argument('--finor-veto-masks', default=None, metavar='<file>', help="load finor veto masks from file")
parser.add_argument('--prescale-factors', default=None, metavar='<file>', help="load prescale factors from file")
parser.add_argument('--ttc-bc0-bx', default=DEFAULT_TTC_BC0_BX, metavar='<n>', type=int, help="TTC_BC0_BX value, default is '{DEFAULT_TTC_BC0_BX}'".format(**locals()))
parser.add_argument('-o', '--output-dir', default=None, help="name of output directory")
parser.add_argument('--cap', default=DEFAULT_CAP, metavar='<n>', type=int, help="delay in BX for capturing the tx buffer output, default is '{DEFAULT_CAP}'".format(**locals()))
args = parser.parse_args(TDF_ARGS)

TDF_INFO("reading", args.menu)
menu = XmlMenu(args.menu)

TDF_INFO("menu name:", menu.name)
TDF_INFO("menu UUID:", menu.uuid_menu)
TDF_INFO("firmware UUID:", menu.uuid_firmware)

# Split algorithms by modules.
modules = get_modules(menu)

# Compile ordered list of devices used for this menu
devices = [DEFAULT_DEVICES[module] for module in sorted(modules.keys())]

TDF_INFO("menu implements", len(modules), "module(s)")

# Verify menu and firmware UUIDs
if 0:#for device in devices:
    uuid_menu = read(device, 'gt_mp7_gtlfdl.read_versions.l1tm_uuid', translate=True)
    if not menu.uuid_menu == uuid_menu:
        raise RuntimeError("menu UUID missmatch:\n" \
            "xml     : {menu.uuid_menu}\n" \
            "hardware: {uuid_menu}".format(**locals()))
    uuid_firmware = read(device, 'gt_mp7_gtlfdl.read_versions.l1tm_fw_uuid', translate=True)
    if not menu.uuid_firmware == uuid_firmware:
        raise RuntimeError("firmware UUID missmatch:\n" \
            "xml     : {menu.uuid_firmware}\n" \
            "hardware: {uuid_firmware}".format(**locals()))

# Create output directory only on demand
if args.output_dir:
    if not os.path.isdir(args.output_dir):
        TDF_INFO("creating result area directory:", args.output_dir)
        os.makedirs(args.output_dir)
        os.chdir(args.output_dir)

# Reset link's logic
for device in devices:
    mp7butler("reset", device, "--clksrc", args.clksrc)

# Setup for loopback or cable mode.
for device in devices:
    if args.loopback:
        mp7butler("txmgts", device, "--loopback", "--e", args.rx_links, "--pattern", "std")
        mp7butler("rxmgts", device, "--e", args.rx_links)
        mp7butler("rxalign", device, "--e", args.rx_links, "--to-bx", args.align_to or "8,4")
    else:
        mp7butler("txmgts", device, "--e", args.rx_links)
        mp7butler("rxmgts", device, "--e", args.rx_links)
        mp7butler("rxalign", device, "--e", args.rx_links, "--to-bx", args.align_to or "38,5")

# Generate set of testvectors
run_routine("testvector_split", args.testvector, args.menu)

# Generate set of buffer images
for module in modules.keys():
    basename = os.path.splitext(os.path.basename(args.testvector))[0]
    tv_filename = "{basename}_module_{module}.txt".format(**locals())
    data_filename = TDF_NAME + "_module_{module}_in.dat".format(**locals())
    buffgen(tv_filename, board = devices[module], outfile = data_filename)

for device in devices:
    data_filename = TDF_NAME + "_module_{module}_in.dat".format(**locals())
    if args.loopback:
        mp7butler("buffers", device, "loopPlay", "--e", args.rx_links, "--inject", "file://{data_filename}".format(**locals()))
    else:
        mp7butler("buffers", device, "loopPlay")

# Reset and setup the GT logic.
for device in devices:
    configure(device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-reset.cfg")
    configure(device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-mux-tx-buffer.cfg")
    configure(device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-delay-manager-values.cfg")

for device in devices:
    if args.hw_delay:
        write(device, "gt_mp7_frame.rb.dm.delay_muons", args.hw_delay)
        write(device, "gt_mp7_frame.rb.dm.delay_eg", args.hw_delay)
        write(device, "gt_mp7_frame.rb.dm.delay_tau", args.hw_delay)
        write(device, "gt_mp7_frame.rb.dm.delay_jet", args.hw_delay)
        write(device, "gt_mp7_frame.rb.dm.delay_ett", args.hw_delay)
        write(device, "gt_mp7_frame.rb.dm.delay_ht", args.hw_delay)
        write(device, "gt_mp7_frame.rb.dm.delay_etm", args.hw_delay)
        write(device, "gt_mp7_frame.rb.dm.delay_htm", args.hw_delay)
        write(device, "gt_mp7_frame.rb.dm.delay_ext_con", args.hw_delay)

# Clear the memories.
for device in devices:
    clear(device, "gt_mp7_frame.simspymem")
    clear(device, "gt_mp7_frame.spymem2_algos")
    clear(device, "gt_mp7_frame.spymem2_finor")

# Setup GTL algorithm masks.
for device in devices:
    if args.algo_bx_mask:
        run_routine("load_bx_masks", device, args.algo_bx_mask)
    else:
        run_routine("enable_algo_bx_mem", device)

# Setup finor/veto masks.
for device in devices:
    if args.finor_veto_masks:
        run_routine("load_finor_veto_masks", device, args.finor_veto_masks)

# Setup presclae factors.
for device in devices:
    if args.prescale_factors:
        run_routine("load_prescale_factors", args.device, args.prescale_factors)

## HB 2016-01-19: bcres_delay for FDL (= 25 [3564-3539 from mp7_ttc_decl.vhd] + 1 [bcres sync.] + "--delay" + 1 [algo-bx-mem output] + 1 [algo spy mem input])
# NOTE: how about less magic numbers?!
for device in devices:
    write(device, "gt_mp7_frame.rb.dm.delay_bcres_fdl", 3564-args.ttc_bc0_bx + 1 + args.delay + 1 + 1)

# Start spy
for device in devices:
    configure(device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-spy.cfg")

# Dump the memories.
for module, device in enumerate(devices):
    dump(device, "gt_mp7_frame.simspymem", outfile = TDF_NAME + "_simspymem_module_{module}.dat".format(module=module))
    algo_dump = dump(device, "gt_mp7_frame.spymem2_algos", outfile = TDF_NAME + "_spymem2_algos_module_{module}.dat".format(module=module))
    dump(device, "gt_mp7_frame.spymem2_finor", outfile = TDF_NAME + "_spymem2_finor_module_{module}.dat".format(module=module))

# Compare the dumps.
for module, device in enumerate(devices):
    basename = os.path.splitext(os.path.basename(args.testvector))[0]
    tv_filename = "{basename}_module_{module}.txt".format(**locals())
    compare(device, "gt_mp7_frame.simspymem", TDF_NAME + "_simspymem_module_{module}.dat".format(module=module), tv_filename, offset = args.delay, size = args.size)
    compare(device, "gt_mp7_frame.spymem2_algos", TDF_NAME + "_spymem2_algos_module_{module}.dat".format(module=module), tv_filename, offset = args.delay + args.gtl_latency, size = args.size)
    compare(device, "gt_mp7_frame.spymem2_finor", TDF_NAME + "_spymem2_finor_module_{module}.dat".format(module=module), tv_filename, offset = args.delay + args.gtl_latency, size = args.size)

# Read in test vector.
tv = TestVector(open(args.testvector))

# Overall delay.
delay_all = args.delay + args.gtl_latency

# Read the emulator log file if available (for active algorithms and names).
logfile = args.testvector[:-len(".txt")] + ".log" # ugly
if os.path.isfile(logfile):
    lines = open(logfile).readlines()
    for i in range(len(lines)):
        if "==== Summary of results ====".lower() in lines[i].lower():
            print lines[i].strip()
            print "bit\tL1A/tv\tL1A/hw\tresult\t(tv=testvector, hw=hardware readout)"
            for line in lines[i:]:
                #result = re.match("^\s+(\d+)\s+(\d+)\s+(L1_[a-zA-Z0-9_]+)", line)
                result = re.match("^\s+(\d+)\s+(\d+)", line)
                if result:
                    #bit, l1a, name = result.groups()
                    bit, l1a = result.groups()
                    index = int(bit)
                    l1a_hw = 0
                    for algorithm in algo_dump.algorithms()[delay_all:delay_all+args.size]:
                        l1a_hw += (algorithm >> index) & 0x1
                    l1a_tv = 0
                    for algorithm in tv.algorithms()[:args.size]:
                        l1a_tv += (algorithm >> index) & 0x1
                    result = "OK" if l1a_tv == l1a_hw else "ERROR"
                    print "{bit}\t{l1a_tv}\t{l1a_hw}\t{result}".format(**locals())
            break
