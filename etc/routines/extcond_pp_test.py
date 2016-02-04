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

DEFAULT_SOURCE = 'testing_amc502.8'
DEFAULT_TARGET = 'extcond_amc502.12'
DEFAULT_CONNECTOR = 0
DEFAULT_PATTERN = ':counter'
DEFAULT_INPUT_DELAY = 2 
DEFAULT_SIZE = 3564
MODEL = 'r1'

# -----------------------------------------------------------------------------
#  Patterns
# -----------------------------------------------------------------------------

patterns = [
    ('counter', range(TDF.ORBIT_LENGTH)), #counter
    ('zero', [0x00000000] * TDF.ORBIT_LENGTH), #zero
    ('ffff', [0xffffffff] * TDF.ORBIT_LENGTH), #ffff
    ('running_1', [1 << i for i in range(32)] * (TDF.ORBIT_LENGTH/32 + 1)), # running 1
    ('running_0', [((1 << i) ^ 0xffffffff) for i in range(32)] * (TDF.ORBIT_LENGTH/32 + 1)), # running 0
    ('custom_pattern', [0xdeadbeef, 0x0c0ffee0, 0xdeadbabe, 0x12345678] * (TDF.ORBIT_LENGTH/4 + 1)), # custom pattern
    ('random_values', [random.randint(0, 0xffffffff) for _ in range(TDF.ORBIT_LENGTH)]) # random values
]

# -----------------------------------------------------------------------------
#  Parsing arguments
# -----------------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument('--source', default = DEFAULT_SOURCE, help = "source device name, default is `testing_amc502.8'")
parser.add_argument('--target', default = DEFAULT_TARGET, help = "target device name, default is `extcond_amc502.12'")
parser.add_argument('-c', '--connector', default = DEFAULT_CONNECTOR, type = int, choices=(0, 1), help = "target device connector (0 or 1), default is 0")
parser.add_argument('--pattern', default = DEFAULT_PATTERN, help = "pattern file or :counter, :random pattern, default is `:counter'")
parser.add_argument('--size', default = DEFAULT_SIZE, type = int, help = "Lines to compare")
parser.add_argument('-d', '--delay', default = DEFAULT_INPUT_DELAY, type = int, help = "input delay")
parser.add_argument('--bcres-delay', metavar = '<n>', type = binutils.integer, help = "overwrite BC_RES delay applied by configuration files")
args = parser.parse_args(TDF_ARGS)

# -----------------------------------------------------------------------------
#  Reset device to use external clock
# -----------------------------------------------------------------------------
mp7butler("reset", args.source, "--clksrc", "external", "-m", MODEL)
mp7butler("reset", args.target, "--clksrc", "external", "-m", MODEL)

# -----------------------------------------------------------------------------
#  Run unittests to RESET and verify integrity.
# -----------------------------------------------------------------------------
run_unittest(args.source, "clk40_locked")
run_unittest(args.source, "bc0_locked")
run_unittest(args.target, "clk40_locked")
run_unittest(args.target, "bc0_locked")
# ev. check FW version of one or both cards??

# -----------------------------------------------------------------------------
#  Setup AMC502 logic
# -----------------------------------------------------------------------------
configure(args.source, os.path.join(TDF.ROOT_DIR, "etc/config/testing_amc502/reset.cfg"))
configure(args.source, os.path.join(TDF.ROOT_DIR, "etc/config/testing_amc502/delay-manager-values.cfg"))
configure(args.target, os.path.join(TDF.ROOT_DIR, "etc/config/extcond_amc502/reset.cfg"))
configure(args.target, os.path.join(TDF.ROOT_DIR, "etc/config/extcond_amc502/delay-manager-values.cfg"))

results = []

for name, pattern in patterns:

    pattern_image = dump(args.source, "payload.simmem")

    for i, value in enumerate(pattern):
        pattern_image.data[i] = value

    # -----------------------------------------------------------------------------
    #  Setup sending device, load pattern and start transmission
    # -----------------------------------------------------------------------------
    #load(args.source, "user.dpmem0", args.pattern) # load a pattern into the SIM MEM
    blockwrite(args.source, "payload.simmem", pattern_image.serialize())
    write(args.source, 'payload.module_info.data_mux', 0x1) # set the TFMC output mux to SIM MEM

    # Overwrite BC_res delay on demand.
    #if args.bcres_delay is not None:
        #TDF_WARNING("overwriting BCRES_DELAY:", args.bcres_delay, "BX")
        #write(args.target, 'gt_mp7_frame.rb.dm.delay_bcres', args.bcres_delay)

    # -----------------------------------------------------------------------------
    #  Clear the memories
    # -----------------------------------------------------------------------------
    clear(args.target, "payload.spymem")

    # -----------------------------------------------------------------------------
    #  Dump test pattern data
    # -----------------------------------------------------------------------------
    source_data = dump(args.source, "payload.simmem")
    temp_data = ExtCondMemoryImage()

    if args.connector is 0:
        temp_data.inject(source_data.data, 0, 1)
        temp_data.inject([0xffffffff for _ in range(len(source_data.data))], 1, 1)
    elif args.connector is 1:
        temp_data.inject([0xffffffff for _ in range(len(source_data.data))], 0, 1)
        temp_data.inject(source_data.data, 1, 1)

    # print temp_data

    # -----------------------------------------------------------------------------
    #  Dump input data
    # -----------------------------------------------------------------------------
    target_data = dump(args.target, "payload.spymem")

    # -----------------------------------------------------------------------------
    #  Compare the dumps
    # -----------------------------------------------------------------------------
    errors = target_data.compare(temp_data, offset = args.delay, size = args.size)

    results.append([name, errors])

print
print
print 'Test summary:'
print

for name, errors in results:
    if errors:
        print 'Test Pattern', name, 'failed with', errors, 'errors!'
    else:
        print 'Test Pattern', name, 'was successful!'

print
errors = sum([result[1] for result in results])
if errors:
    TDF_ERROR('Test failed with' , str(errors), 'errors!!!')
else:
    TDF_INFO('Test succeeded without errors!!!')
