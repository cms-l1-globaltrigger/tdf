# Crate status
# -*- coding: utf-8 -*-

from tdf.extern import argparse
from tdf.core.toolbox import slot_number, device_type
import uhal

# -----------------------------------------------------------------------------
#  Crate configuration
#
#  Defines the full assembled crate layout. If an AMC is not present in the
#  crate it is excluded and assumed not present.
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
#  Helper functions
# -----------------------------------------------------------------------------

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
    return "{0}.{1}.{2}".format(a, b, c)

def mp7_design(device):
    """Retruns MP7 firmware design version."""
    design = read(device, 'ctrl.id.fwrev.design')
    return design

# -----------------------------------------------------------------------------
#  TTY color helpers
# -----------------------------------------------------------------------------

class Colors:
    """TTY color codes."""
    Reset = '\033[0m'
    Bold = '\033[1m'
    Red = '\033[31m'
    Green = '\033[32m'
    Yellow = '\033[33m'
    Blue = '\033[34m'
    Black = '\033[37m'
    White = '\033[39m'
    BgRed = '\033[41m'
    BgGreen = '\033[42m'
    BgYellow = '\033[43m'
    BgBlue = '\033[44m'
    BgBlack = '\033[48m'

# -----------------------------------------------------------------------------
#  AMC status record classes
# -----------------------------------------------------------------------------

class CoreRecord(object):
    """Tests if a device is present and tries to retrieve common MP7 core
    information available on every board.
    """
    def __init__(self, device):
        self.device = device
        self.present = is_device_present(device)
        self.mp7_version = mp7_version(device) if self.present else None
        self.mp7_design = mp7_design(device) if self.present else None

    @property
    def slot(self):
        """Returns device slot number."""
        return slot_number(self.device)

    @property
    def type(self):
        """Returns device full type name."""
        return device_type(self.device)

    def get(self, item, default=None, translate=True):
        """Retruns value read from item if device present or else a default value."""
        if self.present:
            return read(self.device, item, translate=translate)
        return default

class MP7Record(CoreRecord):
    """Retrieves MP7 board specific information."""

    def __init__(self, device):
        super(MP7Record, self).__init__(device)
        self.timestamp = self.get("gt_mp7_frame.module_info.timestamp")
        self.hostname = self.get("gt_mp7_frame.module_info.hostname")
        self.username = self.get("gt_mp7_frame.module_info.username")
        self.frame = self.get("gt_mp7_frame.module_info.frame_version")
        self.l1tm_name = self.get("gt_mp7_gtlfdl.read_versions.l1tm_name")
        self.l1tm_uuid = self.get("gt_mp7_gtlfdl.read_versions.l1tm_uuid")
        self.l1tm_uuid_fw = self.get("gt_mp7_gtlfdl.read_versions.l1tm_fw_uuid")
        self.l1tm_compiler = self.get("gt_mp7_gtlfdl.read_versions.l1tm_compiler_version")
        self.gtl = self.get("gt_mp7_gtlfdl.read_versions.gtl_fw_version")
        self.fdl = self.get("gt_mp7_gtlfdl.read_versions.fdl_fw_version")
        self.build = self.get("gt_mp7_frame.module_info.build_version", translate=False)
        try:
            self.module_id = self.get("gt_mp7_gtlfdl.read_versions.module_id", translate=False)
        except uhal._core.exception:
            self.module_id = "n/a"

class AMC502Record(CoreRecord):
    """Retrieves AMC502 board specific information."""

    def __init__(self, device):
        super(AMC502Record, self).__init__(device)
        self.timestamp = self.get("payload.module_info.timestamp")
        self.username = self.get("payload.module_info.username")
        # self.hostname = self.get("payload.module_info.hostname") # TODO n/a
        self.board_id = self.get("payload.module_info.board_id", translate=False)
        self.build = self.get("payload.module_info.build_version", translate=False)

# -----------------------------------------------------------------------------
#  Parse command line args
# -----------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', action='store_true', help="show more information")
args = parser.parse_args(TDF_ARGS)

# -----------------------------------------------------------------------------
#  Create records
# -----------------------------------------------------------------------------

records = []

for device in CrateConfig:
    if device_type(device).endswith('_mp7'):
        record= MP7Record(device)
    elif device_type(device).endswith('_amc502'):
        record = AMC502Record(device)
    else:
        raise RuntimeError("Unknown device {}".format(device))
    records.append(record)

# -----------------------------------------------------------------------------
#  Print visual crate representation
# -----------------------------------------------------------------------------

# encoding
# slot 1=a, 2=b, 3=c, ... 12=l
doodle = """
  ╔═══╤═══╤═══╤═══╤═══╤═══╦═══╦═══╤═══╤═══╤═══╤═══╤═══╗
  ║aaa│bbb│ccc│ddd│eee│fff║AMC║ggg│hhh│iii│jjj│kkk│lll║
  ║aaa│bbb│ccc│ddd│eee│fff║ 1 ║ggg│hhh│iii│jjj│kkk│lll║
  ║aaa│bbb│ccc│ddd│eee│fff║ 3 ║ggg│hhh│iii│jjj│kkk│lll║
  ║aa0│bb0│cc0│dd0│ee0│ff0╟───╢gg0│hh0│ii0│jj0│kk0│ll0║
  ║aa1│bb1│cc1│dd1│ee1│ff1║ M ║gg1│hh1│ii1│jj1│kk1│ll1║
  ║aaa│bbb│ccc│ddd│eee│fff║ C ║ggg│hhh│iii│jjj│kkk│lll║
  ║aaa│bbb│ccc│ddd│eee│fff║ H ║ggg│hhh│iii│jjj│kkk│lll║
  ╚═══╧═══╧═══╧═══╧═══╧═══╩═══╩═══╧═══╧═══╧═══╧═══╧═══╝
    1   2   3   4   5   6       7   8   9   10  11  12
"""

for record in records:
    char = chr(ord('a') + record.slot - 1)
    bgcolor = Colors.BgGreen if record.present else Colors.BgBlack
    doodle = doodle.replace(char*3, bgcolor+'   '+Colors.Reset)
    label_0 = 'n/a'
    label_1 = '   '
    if record.present:
        label_0 = '   '
        if isinstance(record, MP7Record):
            label_0 = 'MP7'
        elif isinstance(record, AMC502Record):
            label_0 = 'AMC'
            label_1 = '502'
    color = bgcolor+Colors.Black+Colors.Bold
    doodle = doodle.replace(char*2+'0', color+label_0+Colors.Reset)
    doodle = doodle.replace(char*2+'1', color+label_1+Colors.Reset)

print doodle

# -----------------------------------------------------------------------------
#  Print device records
# -----------------------------------------------------------------------------

for record in records:

    # Skip boards that are not present
    if not record.present:
        continue

    # Fancy title bar
    color = Colors.BgBlue + Colors.White + Colors.Bold
    right_label = "slot #{0} ".format(record.slot)
    left_label = " {0:<80}".format(record.device)
    title = "{0}{1}".format(left_label[:80-len(right_label)], right_label)
    print "{0}{1}{2}".format(color, title, Colors.Reset)

    # MP7 specific
    if isinstance(record, MP7Record):
        print "                 l1tm name :", record.l1tm_name
        print "                 l1tm UUID :", record.l1tm_uuid
        print "              l1tm UUID fw :", record.l1tm_uuid_fw
        print "                 module_id :", record.module_id
        print "     VHDL producer version :", record.l1tm_compiler
        print "     timestamp (synthesis) :", record.timestamp
        print "                  hostname :", record.hostname
        print "                  username :", record.username
        print "      uGT fw build version :", hex(record.build)

    # AMC502 specific
    if isinstance(record, AMC502Record):
        # TODO: exclude module info for extconds for the time being
        if not record.type.startswith('extcond'):
             print "     timestamp (synthesis) :", record.timestamp
             print "                  username :", record.username
        print "                  board ID :", record.board_id
        print "    firmware build version :", hex(record.build)

    # MP7 specific
    if isinstance(record, MP7Record):
        print "   payload (frame) version :", record.frame
        print "      gtl firmware version :", record.gtl
        print "      fdl firmware version :", record.fdl

    # Common information
    print "      MP7 firmware version :", record.mp7_version
    print "       MP7 firmware design :", record.mp7_design
    print
