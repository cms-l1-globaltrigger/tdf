# Enables all algo MBX masks.
from tdf.extern import argparse

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
args = parser.parse_args(TDF_ARGS)

# Reset and setup the GT logic.
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-reset.cfg")
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-mux-tx-buffer.cfg")
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-delay-manager-values.cfg")

# Clear the memories.
clear(args.device, "gt_mp7_frame.simspymem")
clear(args.device, "gt_mp7_frame.spymem2_algos")
clear(args.device, "gt_mp7_frame.spymem2_finor")

run_routine("enable_algo_bx_mem", args.device)

# Start spy
configure(args.device, TDF.ROOT_DIR + "/etc/config/gt_mp7/cfg-140/mp7-spy.cfg")
