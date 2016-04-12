# Delay manager (DM) test.
#
# This test loads a counter pattern into the TX buffer and starts a loopback
# transmission. Different BCRES and object type specific delays are applied
# checked in the spy memory.
#
# [TX]---->[RX]---->[DEMUX]---->[LM]---->[DM]---->[SPY]
#

from random import randint
import argparse
import time
import os

# -----------------------------------------------------------------------------
#  Constants
# -----------------------------------------------------------------------------

# Config files.
CFG_RESET = os.path.join(TDF.ROOT_DIR, "etc/config/gt_mp7/reset.cfg")
CFG_SPY_NEXT = os.path.join(TDF.ROOT_DIR, "etc/config/gt_mp7/spy_next.cfg")

DEFAULT_BCRES_RANDOM_PASSES = 4
DEFAULT_OBJECT_RANDOM_PASSES = 4

# Limits for BCRES delay.
MIN_BCRES = 0
MAX_BCRES = TDF.ORBIT_LENGTH - 1

# Limits for object delays.
MIN_OBJ = 0
MAX_OBJ = (TDF.ORBIT_LENGTH / 2) - 1

# Set of applied bcres delays.
DEFAULT_BCRES_DELAYS = [
    MIN_BCRES,
    MIN_BCRES + 1,
    MIN_BCRES + 2,
    MAX_BCRES - 2,
    MAX_BCRES - 1,
    MAX_BCRES,
]

# Set of applied object delays.
DEFAULT_OBJECT_DELAYS = [
    MIN_OBJ,
    MIN_OBJ + 1,
    MIN_OBJ + 2,
    MAX_OBJ - 2,
    MAX_OBJ - 1,
    MAX_OBJ,
]

# Object types to be used.
SORTED_OBJECTS = 'muons', 'eg', 'tau', 'jet', 'ett', 'ht', 'etm', 'htm', 'ext_con'
DEFAULT_OBJECTS = [name for name in SORTED_OBJECTS]

# Logic delay for loopback.
DEFAULT_DELAY_LOGIC = 12

# WARNING memory delay compensation.
DEFAULT_MEMORY_DELAY = 0

# -----------------------------------------------------------------------------
#  Argument parsing
# -----------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
parser.add_argument('--objects', metavar = '<object>', default = DEFAULT_OBJECTS, choices = SORTED_OBJECTS, nargs = '+', help = "object types to be checked, default are `{0}'".format(', '.join(DEFAULT_OBJECTS)))
parser.add_argument('--memory-offset', metavar = '<n>', default = DEFAULT_MEMORY_DELAY, type = int, help = "calculated offset for object/bcres delays >= 2 , default is `{DEFAULT_MEMORY_DELAY}'".format(**locals()))
parser.add_argument('--delay-logic', metavar = '<n>', default = DEFAULT_DELAY_LOGIC, type = int, help = "Internal logic delay for loopback mode, default is `{DEFAULT_DELAY_LOGIC}'".format(**locals()))
parser.add_argument('--random-bcres-passes', metavar = '<n>', default = DEFAULT_BCRES_RANDOM_PASSES, type = int, help = "number of random BCRES dealy passes, default is `{DEFAULT_BCRES_RANDOM_PASSES}'".format(**locals()))
parser.add_argument('--random-object-passes', metavar = '<n>', default = DEFAULT_OBJECT_RANDOM_PASSES, type = int, help = "number of random object delay passes, default is `{DEFAULT_OBJECT_RANDOM_PASSES}'".format(**locals()))
parser.add_argument('-s', '--size', metavar = '<n>', default = 170, type = int, help = "size of counter pattern (default is `170')")
parser.add_argument('-m', '--model', default = 'xe', choices = ('r1', 'xe'), help = "select MP7 model ('r1' or 'xe', default is 'xe')")
args = parser.parse_args(TDF_ARGS)

# Remove double object entries and sort object types.
args.objects = [name for name in SORTED_OBJECTS if name in args.objects]

# Generate random bcres delays.
BCRES_DELAYS = DEFAULT_BCRES_DELAYS + [randint(MIN_BCRES + 3, MAX_BCRES - 3) for _ in range(args.random_bcres_passes)]

# Generate random object delays for every object type.
OBJECT_DELAYS = {}
for name in args.objects:
    OBJECT_DELAYS[name] = DEFAULT_OBJECT_DELAYS + [randint(MIN_OBJ + 3, MAX_OBJ - 3) for _ in range(args.random_object_passes)]

# WARNING memory delay compensation.
if args.memory_offset:
    TDF_WARNING("using memory offset compensation:", args.memory_offset, "BX")

print " => using following bcres_delays ({0} passes):".format(len(BCRES_DELAYS)), ', '.join([str(delay) for delay in BCRES_DELAYS]), "BX"
print " => using following object delays ({0} passes):".format(len(OBJECT_DELAYS.items()[0][1]))
for name in args.objects:
    delays = ', '.join([format(delay, '>4') for delay in OBJECT_DELAYS[name]])
    print "    {name:<8}: {delays} BX".format(**locals())

# Pattern to match (counter).
REF_PATTERN = range(args.size)

# Pattern file for TX buffer.
PATTERN_FILE = TDF_NAME + "_pattern.txt"

# Links to be used.
LINKS = "0-15"

# Latency for loopback.
LATENCY = "43"

# -----------------------------------------------------------------------------
#  Helpers
# -----------------------------------------------------------------------------

def ring_buffer(values, size, offset = 0):
    """Extract section of ring buffer."""
    cut = offset % len(values)
    return (values[cut:] + values[:cut])[:size]

def mask_list(values, mask):
    """Mask all values of a list of values."""
    return [value & mask for value in values]

# -----------------------------------------------------------------------------
#  Setup buffers
# -----------------------------------------------------------------------------

# Reset board.
mp7butler("reset", args.device, "--clksrc", "external", "-m", args.model)

# Generate counter pattern and setup MGTs.
buffgen(":counter", outfile = PATTERN_FILE)
mp7butler("mgts", args.device, "--loopback", "--fix-latency", LATENCY, "--enablelinks", LINKS, "-m", args.model)
mp7butler("buffers", args.device, "loopPlay", "--inject", "file://" + PATTERN_FILE, "--enablelinks", LINKS, "-m", args.model)

# -----------------------------------------------------------------------------
#  Spy with different bcres/object delays
# -----------------------------------------------------------------------------

errors = []

# For different bcres delays...
for delay_bcres in BCRES_DELAYS:
    #write(args.device, "gt_mp7_frame.rb.dm.delay_bcres", delay_bcres)

    # For different object delays...
    for i in range(len(OBJECT_DELAYS.items()[0][1])):

        write(args.device, "gt_mp7_frame.rb.dm.delay_bcres", delay_bcres)


        for name, values in OBJECT_DELAYS.items():
            if name in args.objects:
                # Apply object delays.
                write(args.device, "gt_mp7_frame.rb.dm.delay_{name}".format(**locals()), values[i])

        # Reset GT logic and spy at next orbit.
        configure(args.device, CFG_RESET)
        configure(args.device, CFG_SPY_NEXT)

        # Wait for trig_spy12_busy == 0
        wait(args.device, "gt_mp7_frame.rb.spytrigger_status.trig_spy12_busy", 0)

        # Dump
        image = dump(args.device, "gt_mp7_frame.simspymem")

        # Map memory data.
        data = {
            'muons'   : image.muons(),
            'eg'      : image.egs(),
            'jet'     : image.jets(),
            'tau'     : image.taus(),
            'ett'     : [image.ett(), ],
            'ht'      : [image.ht(), ],
            'etm'     : [image.etm(), ],
            'htm'     : [image.htm(), ],
            'ext_con' : [image.extconds(), ],
        }

        print "computing offsets for..."
        print "+--------------+-------------++-------------+--------------++-------------------+"
        print "| object       | logic delay || delay_bcres | object delay || calculated offset |"
        print "+--------------+-------------++-------------+--------------++-------------------+"

        # For every object type...
        for name in args.objects:
            delay_obj = OBJECT_DELAYS[name][i]

            # Calculate the offset (ring-buffer).
            offset = (TDF.ORBIT_LENGTH + args.delay_logic - delay_bcres + delay_obj) % TDF.ORBIT_LENGTH

            # For every object of this type.
            for n, values in enumerate(data[name]):
                print "| {name:<8}[{n:>2}] | {args.delay_logic:>8} BX || {delay_bcres:>8} BX | {delay_obj:>9} BX || {offset:>14} BX |".format(**locals())
                for bx, value in enumerate(values):
                    if value == 0:
                        TDF_WARNING("*** zero data for", name, " in BX", bx)
                        errors.append("ZERO_DATA : OBJ={name} : BX={bx}".format(**locals()))

                # Compensate memory delay for object delays >= 2.
                offset_ = offset + args.memory_offset if (delay_obj >= 2) else offset
                offset_ = offset_ - args.memory_offset if (delay_bcres >= 2) else offset_

                # Extract and mask the lookup pattern from expected position.
                pattern = ring_buffer(mask_list(values, 0xff), len(REF_PATTERN), offset_)

                # Match with reference pattern.
                if pattern != REF_PATTERN:
                    TDF_WARNING("*** delay missmatch for object `{name}'".format(**locals()))
                    errors.append("DATA_MISSMATCH : OBJ={name} : offset_={offset_} : delay_bcres={delay_bcres} : delay_obj={delay_obj} : ".format(**locals()))
                    for j in range(len(pattern)):
                        if pattern[j] != REF_PATTERN[j]:
                            TDF_WARNING("offset={0} hw={1} sw={2}".format(j, pattern[j], REF_PATTERN[j]))
                #assert pattern == REF_PATTERN, "delay missmatch for object `{name}':\n{pattern}\n{REF_PATTERN}".format(**locals())

        print "+--------------+-------------++-------------+--------------++-------------------+"
        TDF_INFO("found all pattern, done.")

for error in errors:
    TDF_WARNING(error)

assert len(errors) == 0, "failed with errors (see above)"
