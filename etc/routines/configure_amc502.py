# ExtCond PatchPanel Test
#
# This routine sets up data transfer from a GLIB2 module with a TFMC VHDCI transmitter (source)
# to a AMC502 module with a HFMC as receiver(target).
#
# *Prerequisites*
# Connect a VHDCI cable from the TFMC card on the GLIB2 to either Rx0 or Rx1 on the HFMC on the AMC502 board.
# You must specify which connector on the HFMC is used, so that the script checks the correct spy memory.
#

from tdf.extern import argparse
from tdf.core import binutils
from tdf.extcond.images import ExtCondMemoryImage
import sys, os, random

# -----------------------------------------------------------------------------
#  Constants
# -----------------------------------------------------------------------------

DEFAULT_BOARD = 'extcond_amc502.12'
DEFAULT_PATTERN = ':counter'
DEFAULT_LINKS = '0-7'
DEFAULT_INPUT_DELAY = 0

# -----------------------------------------------------------------------------
#  Parsing arguments
# -----------------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument('device', default = 'extcond_amc502.12', help = "device defined in connections file")
parser.add_argument('--pattern', action='store_true', help = "pattern file: counter")
parser.add_argument('--links', default = DEFAULT_LINKS, help = "number of links to be configured")
parser.add_argument('-d', '--delay', default = DEFAULT_INPUT_DELAY, type = int, help = "input delay")
args = parser.parse_args(TDF_ARGS)

counter = range(TDF.ORBIT_LENGTH)


# -----------------------------------------------------------------------------
#  Reset device to use external clock
# -----------------------------------------------------------------------------
mp7butler("reset", args.device, "--clksrc", "external") #, "-m", MODEL)
configure(args.device, os.path.join(TDF.ROOT_DIR, "etc/config/extcond_amc502/reset.cfg"))
configure(args.device, os.path.join(TDF.ROOT_DIR, "etc/config/extcond_amc502/links.cfg"))
configure(args.device, os.path.join(TDF.ROOT_DIR, "etc/config/extcond_amc502/delay-manager-values.cfg"))

if args.pattern:
    pattern_image = dump(args.device, "payload.simmem")
    for i, value in enumerate(counter):
        pattern_image.data[i] = value
    blockwrite(args.device, "payload.simmem", pattern_image.serialize())
    write(args.device, 'payload.module_info.data_mux', 0x1) # set the TFMC output mux to SIM MEM

mp7butler("buffers", args.device, "algoPlay", "--enablelinks", args.links)



