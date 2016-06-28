# dump_versions_amc502.py
# Dump of versions.
from tdf.extern import argparse

parser = argparse.ArgumentParser()
parser.add_argument('device')
args = parser.parse_args(TDF_ARGS)

fwrev_design = read(args.device, "ctrl.id.fwrev.design")
fwrev_a = read(args.device, "ctrl.id.fwrev.a")
fwrev_b = read(args.device, "ctrl.id.fwrev.b")
fwrev_c = read(args.device, "ctrl.id.fwrev.c")

timestamp = read(args.device, "payload.module_info.timestamp", translate=True)
#hostname = read(args.device, "gt_mp7_frame.module_info.hostname", translate=True)
username = read(args.device, "payload.module_info.username", translate=True)
board_id = read(args.device, "payload.module_info.board_id")
build = read(args.device, "payload.module_info.build_version", translate=True)

print
print "Device info for", args.device, "..."
print
print "   timestamp (synthesis) :", timestamp
#print "                hostname :", hostname
print "                username :", username
print "                board ID :", board_id
print "        fw build version :", build
print "    MP7 firmware version :", "{0}.{1}.{2}".format(fwrev_a, fwrev_b, fwrev_c)
#print "      MP7 board revision :", fwrev_design
