# dump_versions.py
# HB 2015-05-21: other registers have to be added
# BA 2015-05-28: cached reads
# Dump of versions.
from tdf.extern import argparse

parser = argparse.ArgumentParser()
parser.add_argument('device')
args = parser.parse_args(TDF_ARGS)

#mp7_fwrev = read(args.device, "ctrl.id.fwrev")
#print "{0} => 0x{1:08x}".format("MP7 firmware review", mp7_fwrev)

fwrev_design = read(args.device, "ctrl.id.fwrev.design")
fwrev_a = read(args.device, "ctrl.id.fwrev.a")
fwrev_b = read(args.device, "ctrl.id.fwrev.b")
fwrev_c = read(args.device, "ctrl.id.fwrev.c")

timestamp = read(args.device, "payload.module_info.timestamp", translate = True)
#hostname = read(args.device, "gt_mp7_frame.module_info.hostname", translate = True)
username = read(args.device, "payload.module_info.username", translate = True)
build = read(args.device, "payload.module_info.build_version", translate = True)

print ""
print "Device info for", args.device, "..."
print ""
print "   timestamp (synthesis) :", timestamp
#print "                hostname :", hostname
print "                username :", username
print "        fw build version :", build
print "    MP7 firmware version :", str(fwrev_a)+"."+str(fwrev_b)+"."+str(fwrev_c)
#print "      MP7 board revision :", fwrev_design
