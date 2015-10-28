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

timestamp = read(args.device, "tdf_mp7.module_info.timestamp", translate = True)
hostname = read(args.device, "tdf_mp7.module_info.hostname", translate = True)
username = read(args.device, "tdf_mp7.module_info.username", translate = True)
version = read(args.device, "tdf_mp7.module_info.tdf_version", translate = True)
build = read(args.device, "tdf_mp7.module_info.build_version", translate = True)

print "Device info for", args.device, "..."
print "   MP7 firmware version :", fwrev_a, fwrev_b, fwrev_c
print "           GT variation :", fwrev_design
print "              timestamp :", timestamp
print "               hostname :", hostname
print "               username :", username
print "  payload (tdf) version :", version
print "   tdf fw build version :", build
