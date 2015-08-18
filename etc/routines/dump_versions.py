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

timestamp = read(args.device, "gt_mp7_frame.module_info.timestamp", translate = True)
hostname = read(args.device, "gt_mp7_frame.module_info.hostname", translate = True)
username = read(args.device, "gt_mp7_frame.module_info.username", translate = True)
frame = read(args.device, "gt_mp7_frame.module_info.frame_version", translate = True)
l1tm_name = read(args.device, "gt_mp7_gtlfdl.read_versions.l1tm_name", translate = True)
l1tm_uuid = read(args.device, "gt_mp7_gtlfdl.read_versions.l1tm_uuid", translate = True)
l1tm_compiler = read(args.device, "gt_mp7_gtlfdl.read_versions.l1tm_compiler_version", translate = True)
gtl = read(args.device, "gt_mp7_gtlfdl.read_versions.gtl_fw_version", translate = True)
fdl = read(args.device, "gt_mp7_gtlfdl.read_versions.fdl_fw_version", translate = True)

print "Device info for", args.device, "..."
print "   MP7 firmware version :", fwrev_a, fwrev_b, fwrev_c
print "           GT variation :", fwrev_design
print "              timestamp :", timestamp
print "               hostname :", hostname
print "               username :", username
print "payload (frame) version :", frame
print "              l1tm name :", l1tm_name
print "              l1tm uuid :", l1tm_uuid
print "  l1tm compiler version :", l1tm_compiler
print "   gtl firmware version :", gtl
print "   fdl firmware version :", fdl