# Enables all algo MBX masks.
from tdf.extern import argparse
from tdf.mp7.images import AlgoBxMemoryImage

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
parser.add_argument('--filename', help = "filename for a algorithm mask")
args = parser.parse_args(TDF_ARGS)

# Create new memory image.
image = AlgoBxMemoryImage()

if args.filename:
    # Load from filestream if porvided.
    image.read(open(args.filename, 'rb'))
else:
    # else enabel all algos.
    image.setEnabled(True)

# Write memory to firmware.
blockwrite(args.device, "gt_mp7_gtlfdl.algo_bx_mem", image.serialize())
