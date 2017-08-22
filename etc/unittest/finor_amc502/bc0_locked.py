# Test if BC0 is locked (only external BC0).
assert read(TDF_DEVICE, "ttc.csr.stat0.bc0_lock") == 0x1, "bc0 is NOT locked"
