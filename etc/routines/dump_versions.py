# dump_versions.py

from tdf.extern import argparse

parser = argparse.ArgumentParser()
parser.add_argument('device')
args = parser.parse_args(TDF_ARGS)

# -----------------------------------------------------------------------------
#  Common
# -----------------------------------------------------------------------------

fwrev_a = read(args.device, "ctrl.id.fwrev.a")
fwrev_b = read(args.device, "ctrl.id.fwrev.b")
fwrev_c = read(args.device, "ctrl.id.fwrev.c")

# -----------------------------------------------------------------------------
#  MP7
# -----------------------------------------------------------------------------

if args.device.startswith("gt_mp7"):

    fwrev_design = read(args.device, "ctrl.id.fwrev.design")

    timestamp = read(args.device, "gt_mp7_frame.module_info.timestamp", translate=True)
    hostname = read(args.device, "gt_mp7_frame.module_info.hostname", translate=True)
    username = read(args.device, "gt_mp7_frame.module_info.username", translate=True)
    frame = read(args.device, "gt_mp7_frame.module_info.frame_version", translate=True)
    l1tm_name = read(args.device, "gt_mp7_gtlfdl.read_versions.l1tm_name", translate=True)
    l1tm_uuid = read(args.device, "gt_mp7_gtlfdl.read_versions.l1tm_uuid", translate=True)
    l1tm_uuid_fw = read(args.device, "gt_mp7_gtlfdl.read_versions.l1tm_fw_uuid", translate=True)
    l1tm_compiler = read(args.device, "gt_mp7_gtlfdl.read_versions.l1tm_compiler_version", translate=True)
    gtl = read(args.device, "gt_mp7_gtlfdl.read_versions.gtl_fw_version", translate=True)
    fdl = read(args.device, "gt_mp7_gtlfdl.read_versions.fdl_fw_version", translate=True)
    build = read(args.device, "gt_mp7_frame.module_info.build_version", translate=True)

    # experimental support for module_id
    import uhal
    try:
        module_id = read(args.device, "gt_mp7_gtlfdl.read_versions.module_id")
    except uhal._core.exception:
        module_id = "n/a"

    print
    print "Device info for", args.device, "..."
    print
    print "               l1tm name :", l1tm_name
    print "               l1tm UUID :", l1tm_uuid
    print "            l1tm UUID fw :", l1tm_uuid_fw
    print "               module_id :", module_id
    print "   VHDL producer version :", l1tm_compiler
    print "   timestamp (synthesis) :", timestamp
    print "                hostname :", hostname
    print "                username :", username
    print "    uGT fw build version :", build
    print "    MP7 firmware version :", "{0}.{1}.{2}".format(fwrev_a, fwrev_b, fwrev_c)
    print "      MP7 board revision :", fwrev_design
    print " payload (frame) version :", frame
    print "    gtl firmware version :", gtl
    print "    fdl firmware version :", fdl

# -----------------------------------------------------------------------------
#  AMC502
# -----------------------------------------------------------------------------

elif "_amc502." in args.device:

    timestamp = read(args.device, "payload.module_info.timestamp", translate=True)
    username = read(args.device, "payload.module_info.username", translate=True)
    board_id = read(args.device, "payload.module_info.board_id")
    build = read(args.device, "payload.module_info.build_version", translate=True)

    print
    print "Device info for", args.device, "..."
    print
    print "   timestamp (synthesis) :", timestamp
    print "                username :", username
    print "                board ID :", board_id
    print "        fw build version :", build
    print "    MP7 firmware version :", "{0}.{1}.{2}".format(fwrev_a, fwrev_b, fwrev_c)
