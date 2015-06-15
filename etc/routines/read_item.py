# read_item.py
# Simple read item script for demonstration purpose.
from tdf.extern import argparse

parser = argparse.ArgumentParser()
parser.add_argument('device')
parser.add_argument('item')
args = parser.parse_args(TDF_ARGS)

value = read(args.device, args.item)
print "{0} => 0x{1:08x}".format(args.item, value)
