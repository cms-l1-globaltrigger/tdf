# versions.py

REQ_DESIGN = 0x12
REQ_FWREV = (2, 2, 1)

assert read(TDF_DEVICE, "ctrl.id.fwrev.design") >= REQ_DESIGN, "requires MP7 design version >= {}".format(REQ_DESIGN)

fwrev_a = read(TDF_DEVICE, "ctrl.id.fwrev.a")
fwrev_b = read(TDF_DEVICE, "ctrl.id.fwrev.b")
fwrev_c = read(TDF_DEVICE, "ctrl.id.fwrev.c")
assert (fwrev_a, fwrev_b, fwrev_c) >= REQ_FWREV, "requires MP7 firmware >= {}.{}.{}".format(*REQ_FWREV)
