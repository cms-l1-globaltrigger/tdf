# Test for correct software reset behavior.

# Make sure clocks are locked.
run_unittest(TDF_DEVICE, "default")

# Helper for reading 64 bit orit number.
def read_orbit_nr():
    low = read(TDF_DEVICE, "gt_mp7_frame.rb.tcm_status.orbit_nr_l")
    high = read(TDF_DEVICE, "gt_mp7_frame.rb.tcm_status.orbit_nr_h")
    return high << 32 | low

# Get current orbit number.
orbit_nr_old = read_orbit_nr()

# Emit counter reset.
write(TDF_DEVICE, "gt_mp7_frame.counter_reset", 0x1)

# Get current orbit number.
orbit_nr_new = read_orbit_nr()

# Make sure that the current orbit number is lower then the previous one.
assert orbit_nr_old > orbit_nr_new, \
    "software reset failed, had no effect on orbit number: before=0x{orbit_nr_old} after=0x{orbit_nr_new}".format(**locals())

run_unittest(TDF_DEVICE, "tcm_locked")
