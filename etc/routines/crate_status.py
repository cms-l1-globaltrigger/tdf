# Crate status
# -*- coding: utf-8 -*-

from tdf.extern import argparse
from tdf.core.toolbox import slot_number, device_type
import sys, os
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

def tty_ctrl(*codes):
    """Create responsive TTY control sequences."""
    if sys.stdout.isatty():
        return "\033[{}m".format(';'.join([format(code) for code in codes]))
    return ''

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

WhiteRedBold = tty_ctrl(1, 37, 41)
WhiteGreenBold = tty_ctrl(1, 37, 42)
WhiteYellowBold = tty_ctrl(1, 37, 43)
WhiteBlueBold = tty_ctrl(1, 37, 44)
WhiteCyanBold = tty_ctrl(1, 37, 45)
Reset = tty_ctrl(0)
Bold = tty_ctrl(1)

def render_title(left, right='', width=80):
    """Render fancy colored title bar with left and optional right content."""
    left_width = (width - 2) - len(right)
    right_width = len(right)
    content = "{0:<{1}}{2:>{3}}".format(left, left_width, right, right_width)
    return "{0} {1} {2}".format(WhiteBlueBold, content, Reset)

class CrateLayout(object):
    """Render ASCII crate visualization."""

    Template = """
╔═════╤═════╤═════╤═════╤═════╤═════╤═════╤═════╤═════╤═════╤═════╤═════╤═════╗
║01%00│02%00│03%00│04%00│05%00│06%00│13%00│07%00│08%00│09%00│10%00│11%00│12%00║
║01%01│02%01│03%01│04%01│05%01│06%01│13%01│07%01│08%01│09%01│10%01│11%01│12%01║
║01%02│02%02│03%02│04%02│05%02│06%02│13%02│07%02│08%02│09%02│10%02│11%02│12%02║
║01%03│02%03│03%03│04%03│05%03│06%03│13%03│07%03│08%03│09%03│10%03│11%03│12%03║
║01%04│02%04│03%04│04%04│05%04│06%04├─────┤07%04│08%04│09%04│10%04│11%04│12%04║
║01%05│02%05│03%05│04%05│05%05│06%05│14%00│07%05│08%05│09%05│10%05│11%05│12%05║
║01%06│02%06│03%06│04%06│05%06│06%06│14%01│07%06│08%06│09%06│10%06│11%06│12%06║
║01%07│02%07│03%07│04%07│05%07│06%07│14%02│07%07│08%07│09%07│10%07│11%07│12%07║
║01%08│02%08│03%08│04%08│05%08│06%08│14%03│07%08│08%08│09%08│10%08│11%08│12%08║
╚═════╧═════╧═════╧═════╧═════╧═════╧═════╧═════╧═════╧═════╧═════╧═════╧═════╝
   1     2     3     4     5     6           7     8     9     10    11    12
"""

    def __init__(self):
       	self.colors = {}
        self.content = {}
        for slot in range(1, 14 + 1):
            self.reset(slot)
        self.set_default()

    def set_default(self):
        """Set default labels."""
        for slot in range(1, 6 + 1):
            self.reset(slot)
            self.set_text(slot, 1, ' MP7 ')
            self.set_color(slot, WhiteGreenBold)
        for slot in range(7, 12 + 1):
            self.reset(slot)
            self.set_text(slot, 1, ' AMC ')
            self.set_text(slot, 2, ' 502 ')
            self.set_color(slot, WhiteGreenBold)
        self.reset(13)
        self.set_text(13, 1, 'AMC13')
        self.reset(14)
        self.set_text(14, 1, ' MCH ')

    def create(self, slot):
        """Create empty content for slot."""
        lines = 9
        if slot > 12:
            lines = 4
        content = {}
        for line in range(lines):
            content[line] = ' ' * 5
        return content

    def encode(self, slot, line):
        """Encode slot/line to template placeholders."""
        return '{0:02d}%{1:02d}'.format(slot, line)

    def reset(self, slot):
        """Reset text and colors for slot."""
        self.content[slot] = self.create(slot)
        self.set_color(slot, Bold)

    def set_text(self, slot, line, value):
        """Set text for slot and line."""
        self.content[slot][line] = "{:<5}".format(value)[:5]

    def set_color(self, slot, color):
        """Set (background) color for slot."""
        self.colors[slot] = color

    def render(self):
        """Render crate representation."""
        template = self.Template
        for slot, lines in self.content.items():
            for line, value in lines.items():
                value = "{}{}{}".format(self.colors[slot], value, Reset)
                template = template.replace(self.encode(slot, line), value)
        return template

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

crate = CrateLayout()

for record in records:
    if not record.present:
        crate.reset(record.slot)
        crate.set_text(record.slot, 1, ' n/a ')
    # Add additional checks...

print
print render_title("Crate Status")
print crate.render()

# -----------------------------------------------------------------------------
#  Print device records
# -----------------------------------------------------------------------------

for record in records:

    # Skip boards that are not present
    if not record.present:
        continue

    # Fancy title bar
    print render_title(record.device, "slot #{0}".format(record.slot))

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
