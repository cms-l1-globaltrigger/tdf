# Check if 40MHz clock is locked.
assert read(TDF_DEVICE, "ctrl.csr.stat.clk40_lock") == 0x1, "clk40 is NOT locked"
