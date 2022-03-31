# Wait for next lumi section.
import time
from tdf.extern import argparse

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
args = parser.parse_args(TDF_ARGS)

lum_seg_nr_1=read(args.device, "gt_mp7_frame.rb.tcm_status.luminosity_seg_nr")
lum_seg_nr_2=read(args.device, "gt_mp7_frame.rb.tcm_status.luminosity_seg_nr")
if lum_seg_nr_1 == lum_seg_nr_2:
    while True:
    	time.sleep(5)   # Delays for 5 seconds
    	lum_seg_nr_3=read(args.device, "gt_mp7_frame.rb.tcm_status.luminosity_seg_nr")
    	if lum_seg_nr_3 > lum_seg_nr_2:
	    break	
else:
    lum_seg_nr_4=read(args.device, "gt_mp7_frame.rb.tcm_status.luminosity_seg_nr")
    if lum_seg_nr_4 == lum_seg_nr_2:
        while True:
    	    time.sleep(5)   # Delays for 5 seconds
    	    lum_seg_nr_5=read(args.device, "gt_mp7_frame.rb.tcm_status.luminosity_seg_nr")
    	    if lum_seg_nr_5 > lum_seg_nr_4:
	        break	
