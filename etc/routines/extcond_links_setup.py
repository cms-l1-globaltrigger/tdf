# ExtCond Fiber Test
#
# This routine sets up data transfer from all AMC502 module with a FMC107 transmitter (source)
# to a MP7 module as receiver(target).
#
#

from tdf.extern import argparse
from tdf.core import binutils
from tdf.extcond.images import ExtCondMemoryImage
import sys, os, random

# -----------------------------------------------------------------------------
#  Constants
# -----------------------------------------------------------------------------

DEFAULT_PATTERN = ':counter'
DEFAULT_INPUT_DELAY = 11
DEFAULT_GTL_LATENCY = 6
DEFAULT_LINKS = '0-3'
MODEL = 'r1'

SOURCES = 'extcond_amc502.12', 'extcond_amc502.11', 'extcond_amc502.10', 'extcond_amc502.9'

# -----------------------------------------------------------------------------
#  Patterns
# -----------------------------------------------------------------------------

patterns = {
    ':counter'        : range(TDF.ORBIT_LENGTH), #counter
    ':zero'           : [0x00000000] * TDF.ORBIT_LENGTH, #zero
    ':ffff'           : [0xffffffff] * TDF.ORBIT_LENGTH, #ffff
    ':running_1'      : [1 << i for i in range(32)] * (TDF.ORBIT_LENGTH/32 + 1), # running 1
    ':running_0'      : [((1 << i) ^ 0xffffffff) for i in range(32)] * (TDF.ORBIT_LENGTH/32 + 1), # running 0
    ':custom_pattern' : [0xdeadbeef, 0x0c0ffee0, 0xdeadbabe, 0x12345678] * (TDF.ORBIT_LENGTH/4 + 1), # custom pattern
    ':random_values'  : [random.randint(0, 0xffffffff) for _ in range(TDF.ORBIT_LENGTH)] # random values
}

# -----------------------------------------------------------------------------
#  Parsing arguments
# -----------------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument('--pattern', default = DEFAULT_PATTERN, choices = patterns.keys(), help = "pattern file or :counter, :random pattern, default is `:counter'")
parser.add_argument('--links', default = DEFAULT_LINKS, help = "number of links to be configured")
parser.add_argument('-d', '--delay', default = DEFAULT_INPUT_DELAY, type = int, help = "input delay")
parser.add_argument('--gtl-latency', default = DEFAULT_GTL_LATENCY, metavar = '<n>', type = int, help = "set latency for GTL logic (for analysis only)")
parser.add_argument('--bcres-delay', metavar = '<n>', type = binutils.integer, help = "overwrite BC_RES delay applied by configuration files")
parser.add_argument('--size', default = TDF.ORBIT_LENGTH, type = int, help = "number of BX to be compared")
args = parser.parse_args(TDF_ARGS)


# -----------------------------------------------------------------------------
#  Reset device to use external clock
# -----------------------------------------------------------------------------
for target in SOURCES:
    mp7butler("reset", target, "--clksrc", "external", "-m", MODEL)

# -----------------------------------------------------------------------------
#  Run unittests to RESET and verify integrity.
# -----------------------------------------------------------------------------
for target in SOURCES:
    run_unittest(target, "clk40_locked")
    run_unittest(target, "bc0_locked")
# ev. check FW version of one or both cards??

# -----------------------------------------------------------------------------
#  Set up the AMC502 boards
# -----------------------------------------------------------------------------
for target in SOURCES:
    configure(target, os.path.join(TDF.ROOT_DIR, "etc/config/extcond_amc502/reset.cfg"))
    configure(target, os.path.join(TDF.ROOT_DIR, "etc/config/extcond_amc502/delay-manager-values.cfg"))
    configure(target, os.path.join(TDF.ROOT_DIR, "etc/config/extcond_amc502/links.cfg"))
    clear(target, "payload.simmem")

# -----------------------------------------------------------------------------
#  Load pattern in sim memories on AMC502 boards
# -----------------------------------------------------------------------------
for target in SOURCES:
    pattern_image = dump(target, "payload.simmem")
    for i, value in enumerate(patterns[args.pattern]):
        pattern_image.data[i] = value
    blockwrite(target, "payload.simmem", pattern_image.serialize())
    write(target, "payload.module_info.data_mux", 1)
    mp7butler("buffers", target, "algoPlay", "--enablelinks", args.links, "-m", MODEL)

