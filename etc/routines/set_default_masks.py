# Enables all algo MBX masks.
from tdf.extern import argparse
from tdf.mp7.images import MasksMemoryImage

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
args = parser.parse_args(TDF_ARGS)

# Create new memory image.
image = MasksMemoryImage()
image.setDefault()

# Write memory to firmware.
blockwrite(args.device, "gt_mp7_gtlfdl.masks", image.serialize())
