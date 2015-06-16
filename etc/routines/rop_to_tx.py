# rop_to_tx.py
# for MP7 firmware >= 1.6.0
# BR 2015-05-15 adaptions for ROP testing in tx-buffer

from tdf.extern import argparse
from tdf.core.testvector import TestVector
import os, re
import time
import datetime

DEFAULT_INPUT_DELAY = 11
DEFAULT_GTL_LATENCY = 6
DEFAULT_SIZE = 170
DEFAULT_LINKS = '0-15'

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
parser.add_argument('--links', default = DEFAULT_LINKS, metavar = '<n-m>', help = "links to be configured, default is '{DEFAULT_LINKS}'".format(**locals()))
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

# Setup for loopback or cable mode.
if args.loopback:
    mp7butler("mgts", args.device, "--loopback", "--enablelinks", args.links, "--align-to", args.align_to or "8,5")
else:
    mp7butler("mgts", args.device, "--enablelinks", args.links, "--align-to", args.align_to or "38,5")

data_filename = TDF_NAME + "_in.dat" # Returns "tagged" filename tdf_simple_buffer_loopback_in.dat
buffgen(args.pattern, board = args.device, outfile = data_filename)

if args.loopback:
    mp7butler("buffers", args.device, "loopPlay", "--inject", "file://{data_filename}".format(**locals()))
else:
    mp7butler("buffers", args.device, "loopPlay")

if args.capture_buffers:
    mp7butler("buffers", args.device, "captureRxTxStb")   # buffer setting
    mp7butler("capture", args.device)                  # buffer capture

# Reset and setup the GT logic.
#configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-reset.cfg")
write (args.device, "gt_mp7_frame.pulse_reset", 1)
assert read(args.device, "gt_mp7_frame.rb.tcm_status.bx_nr_max") == 0xdeb, "TCM is not syncronized after initate a pulse register reset"
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-mux-tx-buffer.cfg")
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-delay-manager-values.cfg")

# overwirte the bcres_dealy in hardware for adusting the simspymemory
write (args.device, "gt_mp7_frame.rb.dm.delay_bcres", "14")

# Clear the memories.
clear(args.device, "gt_mp7_frame.simspymem")
clear(args.device, "gt_mp7_frame.spymem2_algos")
clear(args.device, "gt_mp7_frame.spymem2_finor")
clear(args.device, "gt_mp7_frame.spymem3")

# write Version in ROP
write (args.device, "gt_mp7_frame.rb.rop.version", 0xbabac)

# Setup GTL algorithm masks.
run_routine("enable_algo_bx_mem", args.device)

# Start spy : configuration of the mux setting for changing the incoming data
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-spy-LANE.cfg")

# Setup for rop test.
# 1) Decision for the size of ROP

configure(args.device, os.path.join(TDF.ROOT_DIR, "etc/config/gt_mp7/setup_roptest.cfg"))

# Read current Orbit Number:

# 2) Configure l1asim : 1asim.pattern_a.trigger_pattern_a0-4
print "current orbit number: "
print("  orbit_l: 0x%x" %  read (args.device, "gt_mp7_frame.rb.tcm_status.orbit_nr_l"))
orbit = read (args.device, "gt_mp7_frame.rb.tcm_status.orbit_nr_l")

# setting the l1asim

print("setting up l1asim")
write (args.device, "gt_mp7_frame.rb.l1asim.orbit_nr_l", orbit+50000)

# If you set l1a_sim to 1 you do not need more produced one by MP7(see bleow)
write (args.device, "gt_mp7_frame.rb.l1asim.l1asim_config.enable_l1a_sim", 1)

print("PATTERN_AT_ORBIT for L1ASIM")

write (args.device, "gt_mp7_frame.rb.l1asim.l1asim_config.cntrl", 2)

#setting up spy trigger 
print("setting up spytrigger");
write (args.device, "gt_mp7_frame.rb.spytrigger.control.clear_spy3_ready_event", 1)
write (args.device, "gt_mp7_frame.rb.spytrigger.control.clear_spy3_ready_event", 0)

write (args.device, "gt_mp7_frame.rb.spytrigger.orbit_nr_l", orbit+50000)
print "modified orbit number: "
print("  orbit_l: 0x%x" %  read (args.device, "gt_mp7_frame.rb.tcm_status.orbit_nr_l"))
write (args.device, "gt_mp7_frame.rb.spytrigger.control.spy3_event", 1)
write (args.device, "gt_mp7_frame.rb.spytrigger.control.spy3_event", 0)
# check why spy12_one is not working correctly for testing
#write (args.device, "gt_mp7_frame.rb.spytrigger.control.spy12_once_event", 1)
#write (args.device, "gt_mp7_frame.rb.spytrigger.control.spy12_once_event", 0)
write (args.device, "gt_mp7_frame.rb.spytrigger.control.spy12_next_event",  1)
write (args.device, "gt_mp7_frame.rb.spytrigger.control.spy12_next_event",  0)

#L1A emaulator from MP7 
write(args.device, "ttc.csr.ctrl.l1a_force", 1)


# Dump the memories.
dump(args.device, "gt_mp7_frame.simspymem", outfile = TDF_NAME + "_simspymem.dat")
algo_dump = dump(args.device, "gt_mp7_frame.spymem2_algos", outfile = TDF_NAME + "_spymem2_algos.dat")
dump(args.device, "gt_mp7_frame.spymem2_finor", outfile = TDF_NAME + "_spymem2_finor.dat")
dump(args.device, "gt_mp7_frame.spymem3", outfile = TDF_NAME + "_spymem3_rop.txt")

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
#mp7butler("buffers", args.device, "captureTx", "--cap", "1500", "--enablelinks", args.links)
mp7butler("buffers", args.device, "captureTx", "--enablelinks",  "0-3")
mp7butler("capture", args.device, "--enablelinks", "0-3")

