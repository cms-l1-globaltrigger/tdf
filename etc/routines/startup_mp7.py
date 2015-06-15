from tdf.extern import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
parser.add_argument('-m', '--model', default = 'xe', choices = ('r1', 'xe'), help = "select MP7 model ('r1' or 'xe', default is 'xe')")
parser.add_argument('--clksrc', choices = ("external", "internal"), default = "external", help = "clock source")
parser.add_argument('--firmware', help = "reboot FPGA with selected firmware *.bit file from SD card")
parser.add_argument('--list', action = "store_true", help = "list content of SD card and exit")
args = parser.parse_args(TDF_ARGS)

if args.list:
    mp7butler("scansd", args.device, "-m", args.model)
    sys.exit()

# Enable clocks on AMC13
configure("amc13_k7", TDF.ROOT_DIR + "/etc/config/amc13xg/default_k7.cfg")

if args.firmware:
    # Reboot with firmware image if given.
    mp7butler("rebootfpga", args.device, args.firmware, "-m", args.model)

# Reset MP7 logic for external clock.
mp7butler("reset", args.device, "--clksrc", args.clksrc, "-m", args.model)

# Run unittests to RESET and verify integrity.
run_unittest(args.device, "sw_reset")
