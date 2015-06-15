# dump_versions.py
# HB 2015-05-21: other registers have to be added 
# Dump of versions.

fwrev_design = read(TDF_DEVICE, "ctrl.id.fwrev.design")
fwrev_a = read(TDF_DEVICE, "ctrl.id.fwrev.a")
fwrev_b = read(TDF_DEVICE, "ctrl.id.fwrev.b")
fwrev_c = read(TDF_DEVICE, "ctrl.id.fwrev.c")
print "{0} => {1:d}.{2:d}.{3:d} [GT variation: 0x{4:x}]".format("MP7 firmware review", fwrev_design, fwrev_a, fwrev_b, fwrev_c)

timestamp = read(TDF_DEVICE, "gt_mp7_frame.module_info.timestamp", translate = True)
print "{0} => {1:s}".format("timestamp", timestamp)

hostname = read(TDF_DEVICE, "gt_mp7_frame.module_info.hostname", translate = True)
print "{0} => {1:s}".format("hostname", hostname)

username = read(TDF_DEVICE, "gt_mp7_frame.module_info.username", translate = True)
print "{0} => {1:s}".format("username", username)

frame = read(TDF_DEVICE, "gt_mp7_frame.module_info.frame_version", translate = True)
print "{0} => {1:s}".format("frame version", frame)

l1tm_name = read(TDF_DEVICE, "gt_mp7_gtlfdl.read_versions.l1tm_name", translate = True)
print "{0} => {1:s}".format("l1tm name", l1tm_name)

l1tm_uuid = read(TDF_DEVICE, "gt_mp7_gtlfdl.read_versions.l1tm_uuid", translate = True)
print "{0} => {1:s}".format("l1tm uuid", l1tm_uuid)

l1tm_compiler = read(TDF_DEVICE, "gt_mp7_gtlfdl.read_versions.l1tm_compiler_version", translate = True)
print "{0} => {1:s}".format("l1tm compiler version", l1tm_compiler)

gtl = read(TDF_DEVICE, "gt_mp7_gtlfdl.read_versions.gtl_fw_version", translate = True)
print "{0} => {1:s}".format("gtl firmware version", gtl)

fdl = read(TDF_DEVICE, "gt_mp7_gtlfdl.read_versions.fdl_fw_version", translate = True)
print "{0} => {1:s}".format("fdl firmware version", fdl)

