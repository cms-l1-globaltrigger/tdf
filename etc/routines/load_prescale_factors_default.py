# Loads prescale factor default values (fractional prescale factor 1.00 => 100).
from tdf.extern import argparse
from tdf.mp7.images import PreScaleFactorsImage

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
args = parser.parse_args(TDF_ARGS)

fractional_prescale_factor_default=1.00
default_value=int(fractional_prescale_factor_default*100)
values = [default_value] * 512

print("{args.device} fractional prescale factor default={fractional_prescale_factor_default} - value loaded into register={default_value} [0x{default_value:02x}]".format(**locals()))
blockwrite(args.device, "gt_mp7_gtlfdl.prescale_factor", values)
