# ttc_enable.py
# Enables TTC distribution for all slots.
from tdf.extern import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--device', default='T2', help="AMC13 T2 device (default T2)")
args = parser.parse_args(TDF_ARGS)

# Overwrite mask
write(args.device, 'CONF.TTC.OVERRIDE_MASK', 0xfff)
