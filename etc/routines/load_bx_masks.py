# Loads algo BX masks from file.
from tdf.extern import argparse
from tdf.mp7.images import AlgoBxMemoryImage

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
parser.add_argument('filename', help = "filename for a algorithm cancel-out mask (syntax: '<algorithm>: [bx, bx-bx, ...]')")
args = parser.parse_args(TDF_ARGS)

# Create new memory image.
image = AlgoBxMemoryImage()

# Load from filestream.
with open(args.filename, 'rb') as fs:
    image.readBxMaskFile(fs)

# Write memory to firmware.
blockwrite(args.device, "gt_mp7_gtlfdl.algo_bx_mem", image.serialize())
