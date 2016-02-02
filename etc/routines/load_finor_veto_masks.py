# Loads algo BX masks from file.
from tdf.extern import argparse
from tdf.mp7.images import MasksMemoryImage

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
parser.add_argument('filename', help = "filename for finor and veto masks (syntax: 'finor_masks: [algo, algo-algo, ...]' 'veto_masks: [algo, algo-algo, ...]')")
args = parser.parse_args(TDF_ARGS)

# Create new memory image.
image = MasksMemoryImage()

# Load from filestream.
with open(args.filename, 'rb') as fs:
    image.readMasksFile(fs)

# Write memory to firmware.
blockwrite(args.device, "gt_mp7_gtlfdl.masks", image.serialize())
