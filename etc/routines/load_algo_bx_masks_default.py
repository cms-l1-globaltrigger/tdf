# Loads algo bx memory with default values for algo bx masks.
from tdf.extern import argparse

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
args = parser.parse_args(TDF_ARGS)

algo_bx_mask_default=0xFFFFFFFF
values = [algo_bx_mask_default] * 512

print("{args.device} algo bx mask default=0x{algo_bx_mask_default:08x}".format(**locals()))
blockwrite(args.device, "gt_mp7_gtlfdl.algo_bx_mem", values)
