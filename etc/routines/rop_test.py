# Simple ROP (spymem3)
from tdf.extern import argparse
import sys, os
import time

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
parser.add_argument('filename', help = "testvector filename")
parser.add_argument('-m', '--model', default = 'xe', choices = ('r1', 'xe'), help = "select MP7 model ('r1' or 'xe', default is 'xe')")
parser.add_argument('--clksrc', choices = ("external", "internal"), default = "external", help = "clock source, default `external'")
args = parser.parse_args(TDF_ARGS)

# Reset link's logic
mp7butler("reset", args.device, "--clksrc", args.clksrc, "-m", args.model)

# Reset GT logic.
configure(args.device, os.path.join(TDF.ROOT_DIR, "etc/config/gt_mp7/cfg-140/mp7-reset.cfg"))

# Make sure to enable all algorithms.
run_routine("enable_algo_bx_mem", args.device)

# Load testvector to simspymem.
load(args.device, "gt_mp7_frame.simspymem", args.filename)

# Setup for rop test.
configure(args.device, os.path.join(TDF.ROOT_DIR, "etc/config/gt_mp7/setup_roptest.cfg"))

# Wait for trig_spy3_busy != 1, timeout after 10 sec
t = time.time()
while read(args.device, "gt_mp7_frame.rb.spytrigger_status.trig_spy3_busy") != 0:
    if time.time() > t + 10.0:
        raise RuntimeError("timeout waiting for `trig_spy3_busy'")
    time.sleep(0.5)

dump(args.device, "gt_mp7_frame.spymem3", outfile = TDF_NAME + "_spymem3_rop.txt")
