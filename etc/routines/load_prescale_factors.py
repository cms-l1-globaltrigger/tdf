# Loads algo BX masks from file.
from tdf.extern import argparse
from tdf.mp7.images import PreScaleFactorsImage

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
parser.add_argument('filename', help = "filename for prescale factors (syntax: '<algorithm>: <value>')")
args = parser.parse_args(TDF_ARGS)

# Create new memory image.
image = PreScaleFactorsImage()

# Load from filestream.
with open(args.filename, 'rb') as fs:
    image.readPreScaleFactorsFile(fs)

# Write memory to firmware.
blockwrite(args.device, "gt_mp7_gtlfdl.prescale_factor", image.serialize())
