# Test if TCM is locked.
assert read(TDF_DEVICE, "gt_mp7_frame.rb.tcm_status.bx_nr_max") == 0xdeb, "TCM is not syncronized"
