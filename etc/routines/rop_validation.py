# Simple ROP (spymem3)
#from tdf.extern import argparse
#import sys, os
#import time

from tdf.extern import argparse
#from tdf.core.testvector import TestVector
import os, re
import time
import datetime


def result_area():
    from datetime import datetime
    dirname = "{0}_{1}".format(TDF_NAME, datetime.strftime(datetime.now(), "%Y-%m-%dT%H-%M-%S"))
    return dirname

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
parser.add_argument('filename', help = "testvector filename")
parser.add_argument('--clksrc', choices = ("external", "internal"), default = "external", help = "clock source, default `external'")
parser.add_argument('-o', '--output-dir', default = result_area(), help = "name of output directory")
args = parser.parse_args(TDF_ARGS)


if not os.path.isdir(args.output_dir):
    print "creating result area directory:", args.output_dir
    os.makedirs(args.output_dir)
    os.chdir(args.output_dir)


print "The routine is for testing the ROP with emulator data, which will be uploaded into simspy memory: "
# Reset link's logic
mp7butler("reset", args.device, "--clksrc", args.clksrc)

# Reset and setup the GT logic.
#configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-reset.cfg")

# Calibrate the Delay based on delay_bcres, which the current measured value is 14
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-delay-manager-values.cfg")

# use the new reset pulse register for synchronizing the TCM 
write (args.device, "gt_mp7_frame.pulse_reset", 1)

assert read(args.device, "gt_mp7_frame.rb.tcm_status.bx_nr_max") == 0xdeb, "TCM is not syncronized after initate a pulse register reset"

print "clear all UGT memories: "

# Clear the all UGT memories.
clear(args.device, "gt_mp7_frame.simspymem")
clear(args.device, "gt_mp7_frame.spymem2_algos")
clear(args.device, "gt_mp7_frame.spymem2_finor")
clear(args.device, "gt_mp7_frame.spymem3")

# Setup GTL algorithm masks for gtl
run_routine("enable_algo_bx_mem", args.device)

# write Version in ROP
write (args.device, "gt_mp7_frame.rb.rop.version", 0xbabac)


# Start spy : configuration of the mux setting for changing the incoming data
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-spy-SIM.cfg")

# Load testvector to simspymem.
load(args.device, "gt_mp7_frame.simspymem", args.filename)

# Setup for rop test.
# 1) Decision for the size of ROP
# 2) Configure l1asim : 1asim.pattern_a.trigger_pattern_a0-4

configure(args.device, os.path.join(TDF.ROOT_DIR, "etc/config/gt_mp7/setup_roptest.cfg"))

# Read current Orbit Number:
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
write (args.device, "gt_mp7_frame.rb.spytrigger.control.spy12_once_event", 1)
write (args.device, "gt_mp7_frame.rb.spytrigger.control.spy12_once_event", 0)

#L1A emaulator from MP7 
#write(args.device, "ttc.csr.ctrl.l1a_force", 1)

# Wait for trig_spy3_busy != 1, timeout after 10 sec
#print("waiting until spytrigger is ready");
#while True:
#	busy = read(args.device, "gt_mp7_frame.rb.spytrigger_status.trig_spy3_busy");
#	if busy == 1 :
#		sys.stdout.write('.')
#		sys.stdout.flush()
#		time.sleep(0.1)
#	else:
#		break;

    # Read the emulator log file if available (for active algorithms and names).
    





dump(args.device, "gt_mp7_frame.spymem3", outfile = TDF_NAME + "_spymem3_rop.txt")
