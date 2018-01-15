# multiboard_function_test
#
# usage: tdf run multiboard_function_test --menu sample.xml --testvector sample.txt --loopback
#
# HB 2016-06-07: changed DEFAULT_INPUT_DELAY 9 -> 8 with FW frame v0.0.38, because of additional delay for bcres_d in dm.vhd.
#

from tdf.extern import argparse
from tdf.core.testvector import TestVector, AlgorithmDump, FinorDump
from tdf.core.xmlmenu import XmlMenu
from tdf.core.settings import TDF
from tdf.core import tty

import tempfile
import sys, os, re
import time
import shutil

DEFAULT_ALIGN_CABLE = '38,5'
DEFAULT_ALIGN_LOOPBACK = '9,5'
DEFAULT_INPUT_DELAY = 9
DEFAULT_GTL_LATENCY = 6
DEFAULT_SIZE = 170
DEFAULT_RX_LINKS = '0-15'
DEFAULT_TX_LINKS = '0-3'
DEFAULT_CAP = 0
DEFAULT_HW_DELAY = 0
DEFAULT_TTC_BC0_BX = 3539

# Keys
RESULT_OK = "OK"
RESULT_ERROR = "ERROR"
RESULT_IGNORED = "IGNORED"

# Default module to device mapping.
device_mapping = {
    0: 'gt_mp7.1',
    1: 'gt_mp7.2',
    2: 'gt_mp7.3',
    3: 'gt_mp7.4',
    4: 'gt_mp7.5',
    5: 'gt_mp7.6',
}

# Ignored algorithm names.
ignored_algorithms = [
    'L1_FirstBunchInTrain',
]

def mkfilename(module, name, prefix=TDF_NAME):
    """Returns prefixed absolute path and filename with contained module index.
    The absoulute path is retrieved from current working directory.
    Format: /<abs-path>/<prefix>_module_<module>_<name>

    >>> mkfilename(module=1, name='foo.txt', prefix='bar')
    '/home/user/bar_module_1_foo.txt'
    """
    return os.path.join(os.getcwd(), "{prefix}_module_{module}_{name}".format(**locals()))

def get_modules(menu):
    """Returns dict of modules ids with list of assigned algorithm names.

    >>> menu = XmlMenu('sample.xml')
    >>> get_modules(menu)
    {0: ['L1_foo', ...], 1: ['L1_bar', ...], ... }
    """
    modules = {}
    for algorithm in menu.algorithms:
        module_id = algorithm.module_id
        if module_id not in modules.keys():
            modules[module_id] = []
        modules[module_id].append(algorithm)
    return modules

def validate_uuid_menu(device, menu):
    """Validates match of menu UUID. Raises a RuntimeError on mismatches."""
    uuid_menu = read(device, 'gt_mp7_gtlfdl.read_versions.l1tm_uuid', translate=True)
    if not menu.uuid_menu == uuid_menu:
        raise RuntimeError("menu UUID missmatch:\n" \
            "xml      : {menu.uuid_menu} : {menu.filename}\n" \
            "hardware : {uuid_menu} : {device}".format(**locals()))

def validate_uuid_firmware(device, menu):
    """Validates match of firmware UUID. Raises a RuntimeError on mismatches."""
    uuid_firmware = read(device, 'gt_mp7_gtlfdl.read_versions.l1tm_fw_uuid', translate=True)
    if not menu.uuid_firmware == uuid_firmware:
        raise RuntimeError("firmware UUID missmatch:\n" \
            "xml      : {menu.uuid_firmware} : {menu.filename}\n" \
            "hardware : {uuid_firmware} : {device}".format(**locals()))

def merge_algorithm_dumps(dumps, filename):
    """Merge algorithm dumps. Takes list of algorithm dump objects, writes
    merged dump to filename. Returns merged dump instance."""
    merged = AlgorithmDump()
    merged._algorithms = [0] * TDF.ORBIT_LENGTH # Make sure to init
    for dump in dumps:
        algorithms = dump.algorithms()
        for bx in range(len(algorithms)):
            merged._algorithms[bx] |= algorithms[bx]
    with open(filename, 'w') as fp:
        fp.write(merged.serialize())
    return merged

def merge_finor_dumps(dumps, filename):
    """Merge finor dumps. Takes list of FinOR dump objects, writes merged
    dump to filename. Returns merged dump instance."""
    merged = FinorDump()
    merged._finor = [0] * TDF.ORBIT_LENGTH # Make sure to init
    for dump in dumps:
        finors = dump.finors()
        for bx in range(len(finors)):
            merged._finor[bx] |= finors[bx]
    with open(filename, 'w') as fp:
        fp.write(merged.serialize())
    return merged

parser = argparse.ArgumentParser()
parser.add_argument('--menu', metavar='<menu>', required=True, type=os.path.abspath, help="XML menu file")
parser.add_argument('--testvector', metavar='<testvector>', required=True, type=os.path.abspath, help="test vector to be loaded into the TX buffers")
parser.add_argument('--map', dest = 'mapping', action = 'append', default = [], metavar = '<module>:<device>', help = "map module to device (eg. --map 0:gt_mp7.6)")
parser.add_argument('--clksrc', choices=('external', 'internal'), default='external', help="clock source, default is 'external'")
parser.add_argument('--loopback', action='store_true', help="run internal loopback mode (without cable)")
parser.add_argument('--rx-links', '--links', default=DEFAULT_RX_LINKS, metavar='<n-m>', help="RX links to be configured, default is '{DEFAULT_RX_LINKS}'".format(**locals()))
parser.add_argument('--tx-links', default=DEFAULT_TX_LINKS, metavar='<n-m>', help="TX links to be configured, default is '{DEFAULT_TX_LINKS}'".format(**locals()))
parser.add_argument('--delay', default=DEFAULT_INPUT_DELAY, metavar='<n>', type=int, help="delay in BX for incomming data in spy memory, default is '{DEFAULT_INPUT_DELAY}'".format(**locals()))
parser.add_argument('--hw-delay', default=DEFAULT_HW_DELAY, metavar='<n>', type=int, help="delay in BX for incomming data, default is '{DEFAULT_HW_DELAY}'".format(**locals()))
parser.add_argument('--gtl-latency', default=DEFAULT_GTL_LATENCY, metavar='<n>', type=int, help="set latency for GTL logic in BX, default is '{DEFAULT_GTL_LATENCY}'".format(**locals()))
parser.add_argument('--size', default=DEFAULT_SIZE, metavar='<n>', type=int, help="number of BX to be compared, default is '{DEFAULT_INPUT_DELAY}'".format(**locals()))
parser.add_argument('--align-to', default=None, metavar='<bx,cycle>', help="overwrite link alignment, default '{DEFAULT_ALIGN_CABLE}', with --loopback option '{DEFAULT_ALIGN_LOOPBACK}' (bx, cycle)".format(**locals()))
parser.add_argument('--algo-bx-mask', default=None, metavar='<file>', help="load algorithm BX mask from file")
parser.add_argument('--finor-veto-masks', default=None, metavar='<file>', help="load finor veto masks from file")
parser.add_argument('--prescale-factors', default=None, metavar='<file>', help="load prescale factors from file")
parser.add_argument('--ttc-bc0-bx', default=DEFAULT_TTC_BC0_BX, metavar='<n>', type=int, help="TTC_BC0_BX value, default is '{DEFAULT_TTC_BC0_BX}'".format(**locals()))
parser.add_argument('--cap', default=DEFAULT_CAP, metavar='<n>', type=int, help="delay in BX for capturing the tx buffer output, default is '{DEFAULT_CAP}'".format(**locals()))
parser.add_argument('--keep', action='store_true', help="preserve dump directory after execution")
args = parser.parse_args(TDF_ARGS)

TDF_INFO("reading XML menu", args.menu)
menu = XmlMenu(args.menu)

TDF_INFO("menu name:", menu.name)
TDF_INFO("menu UUID:", menu.uuid_menu)
TDF_INFO("firmware UUID:", menu.uuid_firmware)

# Split algorithms by modules.
modules = get_modules(menu)

# Overwrite default device mapping on demand.
for module, device in (entry.split(':') for entry in args.mapping):
    device_mapping[int(module)] = device
# Compile ordered list of devices used for this menu
devices = [device_mapping[module] for module in sorted(modules.keys())]

TDF_INFO("menu", menu.name, "implements", len(modules), "module(s)")

# Verify menu and firmware UUIDs
for device in devices:
    validate_uuid_menu(device, menu)
    validate_uuid_firmware(device, menu)


temp_dir = tempfile.mkdtemp(prefix=TDF_NAME)
TDF_NOTICE("created temporary directory:", temp_dir)

# Catch exceptions to be able to remove temp dir
try:
    # Change to dump area
    os.chdir(temp_dir)

    # Reset link's logic
    for device in devices:
        mp7butler("reset", device, "--clksrc", args.clksrc, '--clkcfg', 'default-ext')

    # Setup for loopback or cable mode.
    for device in devices:
        if args.loopback:
            mp7butler("txmgts", device, "--loopback", "--e", args.rx_links, "--pattern", "std")
            mp7butler("rxmgts", device, "--e", args.rx_links)
            mp7butler("rxalign", device, "--e", args.rx_links, "--to-bx", args.align_to or DEFAULT_ALIGN_LOOPBACK)
        else:
            mp7butler("txmgts", device, "--e", args.rx_links)
            mp7butler("rxmgts", device, "--e", args.rx_links)
            mp7butler("rxalign", device, "--e", args.rx_links, "--to-bx", args.align_to or DEFAULT_ALIGN_CABLE)

    # Generate set of testvectors
    run_routine("testvector_split", args.testvector, args.menu, '-o', temp_dir)

    # Generate set of buffer images from splitted testvectors - keept track of that names!
    for module in modules.keys():
        basename = os.path.splitext(os.path.basename(args.testvector))[0]
        tv_filename = "{basename}_module_{module}.txt".format(**locals())
        data_filename = mkfilename(module, "in.dat")
        buffgen(tv_filename, board=devices[module], outfile=data_filename)

    for device in devices:
        data_filename = mkfilename(module, "in.dat")
        if args.loopback:
            mp7butler("buffers", device, "loopPlay", "--e", args.rx_links, "--inject", "file://{data_filename}".format(**locals()))
        else:
            mp7butler("buffers", device, "loopPlay")

    # Reset and setup the GT logic.
    for device in devices:
        configure(device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-reset.cfg")
        configure(device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-mux-tx-buffer.cfg")
        configure(device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-delay-manager-values.cfg")
        # Configure LEMO outputs to FINOR AMC502
        configure(device, TDF.ROOT_DIR + "/etc/config/gt_mp7/tp_mux_finor.cfg")

    # Input delays (will be obsolete in future)
## HB 2017-09-18: removed dm.vhd from payload.vhd and rb.vhd
    #for device in devices:
        #write(device, "gt_mp7_frame.rb.dm.delay_muons", args.hw_delay)
        #write(device, "gt_mp7_frame.rb.dm.delay_eg", args.hw_delay)
        #write(device, "gt_mp7_frame.rb.dm.delay_tau", args.hw_delay)
        #write(device, "gt_mp7_frame.rb.dm.delay_jet", args.hw_delay)
        #write(device, "gt_mp7_frame.rb.dm.delay_ett", args.hw_delay)
        #write(device, "gt_mp7_frame.rb.dm.delay_ht", args.hw_delay)
        #write(device, "gt_mp7_frame.rb.dm.delay_etm", args.hw_delay)
        #write(device, "gt_mp7_frame.rb.dm.delay_htm", args.hw_delay)
        #write(device, "gt_mp7_frame.rb.dm.delay_ext_con", args.hw_delay)

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
## HB 2017-09-18: removed dm.vhd from payload.vhd and rb.vhd
    #delay_bcres_fdl = TDF.ORBIT_LENGTH - args.ttc_bc0_bx + 1 + args.delay + 1 + 1
    #for device in devices:
        #write(device, "gt_mp7_frame.rb.dm.delay_bcres_fdl", delay_bcres_fdl)

    # Start spy
    for device in devices:
        configure(device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-spy.cfg")

    # Dump the memories.
    algo_dumps = {}
    finor_dumps = {}
    for module, device in enumerate(devices):
        dump(device, "gt_mp7_frame.simspymem", outfile=mkfilename(module, "simspymem.dat"))
        algo_dumps[module] = dump(device, "gt_mp7_frame.spymem2_algos", outfile=mkfilename(module, "spymem2_algos.dat"))
        finor_dumps[module] = dump(device, "gt_mp7_frame.spymem2_finor", outfile=mkfilename(module, "spymem2_finor.dat"))

    # Merge dumped algorithm results
    algodump_filename = "{TDF_NAME}_merged_spymem2_algos.dat".format(**globals())
    TDF_INFO("merging dumped algorithms results to", algodump_filename)
    merged_algo_dump = merge_algorithm_dumps(algo_dumps.values(), algodump_filename)

    # Merge dumped FinOR results
    finordump_filename = "{TDF_NAME}_merged_spymem2_finor.dat".format(**globals())
    TDF_INFO("merging dumped FinOR results to", finordump_filename)
    merge_finor_dumps(finor_dumps.values(), finordump_filename)

    # Compare the dumps.
    basename = os.path.splitext(os.path.basename(args.testvector))[0]
    tv_filename = "{basename}_module_{module}.txt".format(**locals())
    print ""
    print "Summary of input links"
    for module, device in enumerate(devices):
        print ""
        print "Module {module} ({device}):".format(**locals())
        compare(device, "gt_mp7_frame.simspymem", mkfilename(module, "simspymem.dat"), args.testvector, offset=args.delay, size=args.size)

    print ""
    print "-------------------------------------------------------"
    print ""
    print "Algo & finor summary (all modules merged):"
    compare(devices[0], "gt_mp7_frame.spymem2_algos", algodump_filename, args.testvector, offset=args.delay + args.gtl_latency, size=args.size)
    compare(devices[0], "gt_mp7_frame.spymem2_finor", finordump_filename, args.testvector, offset=args.delay + args.gtl_latency, size=args.size)

    TDF_INFO("reading testvector", args.testvector)
    tv = TestVector(args.testvector)

    # Print L1A statistics
    algorithms = sorted(menu.algorithms, key=lambda algorithm: algorithm.index)
    delay_all = args.delay + args.gtl_latency
    good = 0
    errors = 0
    ignored = 0

    print "|-----|-----|------------------------------------------------------------------|--------|--------|----------|"
    print "| Mod | Idx | Name                                                             | l1a.tv | l1a.hw | Result   |"
    print "|-----|-----|------------------------------------------------------------------|--------|--------|----------|"
    for algorithm in algorithms:

        l1a_tv = 0
        for value in tv.algorithms()[:args.size]:
            l1a_tv += (value >> algorithm.index) & 0x1

        l1a_hw = 0
        for value in merged_algo_dump.algorithms()[delay_all:delay_all+args.size]:
            l1a_hw += (value >> algorithm.index) & 0x1

        if algorithm.name in ignored_algorithms:
            result_code = RESULT_IGNORED
            result_style = tty.Yellow + tty.Bold
            ignored += 1
        elif l1a_tv == l1a_hw:
            result_code = RESULT_OK
            result_style = tty.Green + tty.Bold
            good += 1
        else:
            result_code = RESULT_ERROR
            result_style = tty.Red + tty.Bold
            errors += 1

        result = "{result_style}{result_code:<7}{tty.Reset}".format(**locals())
        print "| {algorithm.module_id:>3d} | {algorithm.index:>3d} | {algorithm.name:<64} |  {l1a_tv:>4d}  |  {l1a_hw:>4d}  | {result}  |".format(**locals())
    print "|-----|-----|------------------------------------------------------------------|--------|--------|----------|"

    # Remove temporary directory
    if args.keep:
        TDF_NOTICE("kept temporary directory:", temp_dir)
    else:
        TDF_NOTICE("removing temporary directory:", temp_dir)
        shutil.rmtree(temp_dir)

    if ignored:
        TDF_WARNING(ignored, "algorithms ignored.")
    if errors:
        TDF_ERROR(errors, "errors occured.")

# Clean up on exception
except:
    TDF_NOTICE("removing temporary directory:", temp_dir)
    shutil.rmtree(temp_dir)
    raise
