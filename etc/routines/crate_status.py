# Crate status
# -*- coding: utf-8 -*-

from tdf.extern import argparse
from tdf.core.toolbox import slot_number, device_type

def is_device_present(device):
    """Retruns True if device is accessible (assumingly present)."""
    try:
        read(device, 'ctrl.id')
    except:
        return False
    return True

def mp7_version(device):
    """Retruns MP7 firmware version."""
    a = read(device, 'ctrl.id.fwrev.a')
    b = read(device, 'ctrl.id.fwrev.b')
    c = read(device, 'ctrl.id.fwrev.c')
    return a, b, c

def mp7_design(device):
    """Retruns MP7 firmware design version."""
    design = read(device, 'ctrl.id.fwrev.design')
    return design

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', action='store_true', help="show more information")
args = parser.parse_args(TDF_ARGS)

CrateConfig = [
    'gt_mp7.1',
    'gt_mp7.2',
    'gt_mp7.3',
    'gt_mp7.4',
    'gt_mp7.5',
    'gt_mp7.6',
    'finor_amc502.7',
    'finor_pre_amc502.8',
    'extcond_amc502.9',
    'extcond_amc502.10',
    'extcond_amc502.11',
    'extcond_amc502.12',
]

states = []

for device in CrateConfig:
    state = {}
    state['device'] = device
    present = is_device_present(device)
    state['present'] = present
    if present:
        state['mp7.version'] = mp7_version(device)
        state['mp7.design'] = mp7_design(device)
        if device_type(device).endswith('_mp7'):
            state['timestamp'] = read(device, "gt_mp7_frame.module_info.timestamp", translate=True)
            state['hostname'] = read(device, "gt_mp7_frame.module_info.hostname", translate=True)
            state['username'] = read(device, "gt_mp7_frame.module_info.username", translate=True)
            state['frame'] = read(device, "gt_mp7_frame.module_info.frame_version", translate=True)
            state['l1tm_name'] = read(device, "gt_mp7_gtlfdl.read_versions.l1tm_name", translate=True)
            state['l1tm_uuid'] = read(device, "gt_mp7_gtlfdl.read_versions.l1tm_uuid", translate=True)
            state['l1tm_uuid_fw'] = read(device, "gt_mp7_gtlfdl.read_versions.l1tm_fw_uuid", translate=True)
            state['l1tm_compiler'] = read(device, "gt_mp7_gtlfdl.read_versions.l1tm_compiler_version", translate=True)
            state['gtl'] = read(device, "gt_mp7_gtlfdl.read_versions.gtl_fw_version", translate=True)
            state['fdl'] = read(device, "gt_mp7_gtlfdl.read_versions.fdl_fw_version", translate=True)
            state['build'] = read(device, "gt_mp7_frame.module_info.build_version", translate=True)
            # experimental support for module_id
            import uhal
            try:
                state['module_id'] = read(device, "gt_mp7_gtlfdl.read_versions.module_id")
            except uhal._core.exception:
                state['module_id'] = "n/a"
        if device_type(device).endswith('_amc502'):
            state['timestamp'] = read(device, "payload.module_info.timestamp", translate=True)
            state['username'] = read(device, "payload.module_info.username", translate=True)
            state['board_id'] = read(device, "payload.module_info.board_id")
            state['build'] = read(device, "payload.module_info.build_version", translate=True)
    states.append(state)

doodle = """
 ╔═══╤═══╤═══╤═══╤═══╤═══╦═══╦═══╤═══╤═══╤═══╤═══╤═══╗
 ║aaa│bbb│ccc│ddd│eee│fff║AMC║ggg│hhh│iii│jjj│kkk│lll║
 ║aaa│bbb│ccc│ddd│eee│fff║ 1 ║ggg│hhh│iii│jjj│kkk│lll║
 ║aaa│bbb│ccc│ddd│eee│fff║ 3 ║ggg│hhh│iii│jjj│kkk│lll║
 ║axx│bxx│cxx│dxx│exx│fxx╟───╢gxx│hxx│ixx│jxx│kxx│lxx║
 ║aaa│bbb│ccc│ddd│eee│fff║ M ║ggg│hhh│iii│jjj│kkk│lll║
 ║aaa│bbb│ccc│ddd│eee│fff║ C ║ggg│hhh│iii│jjj│kkk│lll║
 ║aaa│bbb│ccc│ddd│eee│fff║ H ║ggg│hhh│iii│jjj│kkk│lll║
 ╚═══╧═══╧═══╧═══╧═══╧═══╩═══╩═══╧═══╧═══╧═══╧═══╧═══╝
   1   2   3   4   5   6       7   8   9   10  11  12
"""

for state in states:
    device = state['device']
    present = state['present']
    slot = slot_number(device)
    c = chr(ord('a') + slot - 1)
    color = '\033[42m' if state['present'] else '\033[48m'
    doodle = doodle.replace(c*3, color+'   \033[0m')
    present_code = '   ' if present else 'n/a'
    doodle = doodle.replace(c+'xx', color+present_code+'\033[0m')

print doodle

for state in states:
    device = state['device']
    present = state['present']
    if present:
        print '-' * 80
        print "{0} (slot #{1})".format(device, slot_number(device))
        if device_type(device).endswith('_mp7'):
            print "               l1tm name :", state['l1tm_name']
            print "               l1tm UUID :", state['l1tm_uuid']
            print "            l1tm UUID fw :", state['l1tm_uuid_fw']
            print "               module_id :", state['module_id']
            print "   VHDL producer version :", state['l1tm_compiler']
            print "   timestamp (synthesis) :", state['timestamp']
            print "                hostname :", state['hostname']
            print "                username :", state['username']
            print "    uGT fw build version :", state['build']
        if device_type(device).endswith('_amc502'):
            if not device_type(device).startswith('extcond'):
                 print "   timestamp (synthesis) :", state['timestamp']
                 print "                username :", state['username']
            print "                board ID :", state['board_id']
            print "  firmware build version :", state['build']
        if device_type(device).endswith('_mp7'):
            print " payload (frame) version :", state['frame']
            print "    gtl firmware version :", state['gtl']
            print "    fdl firmware version :", state['fdl']
        print "    MP7 firmware version :", "{0}.{1}.{2}".format(*state['mp7.version'])
        print "    MP7 firmware design  :", state['mp7.design']
print '-' * 80
