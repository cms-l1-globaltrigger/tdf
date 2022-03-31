# Crate status
# -*- coding: utf-8 -*-

from tdf.extern import argparse
from tdf.core.toolbox import slot_number, device_type
from tdf.core import tty

from distutils.version import StrictVersion
import random
import sys, os
import uhal

# -----------------------------------------------------------------------------
#  Helper functions
# -----------------------------------------------------------------------------

def all_equal(items):
    """Returns True if all items in list are equal.
    >>> all_equal([42, 42, 42, 42])
    True
    """
    return len(set(items)) == 1

def is_device_present(device):
    """Returns True if device is accessible (assumingly present)."""
    try:
        read(device, 'ctrl.id')
    except uhal._core.exception:
        return False
    return True

def mp7_version(device):
    """Returns MP7 firmware version."""
    a = read(device, 'ctrl.id.fwrev.a')
    b = read(device, 'ctrl.id.fwrev.b')
    c = read(device, 'ctrl.id.fwrev.c')
    return "{0}.{1}.{2}".format(a, b, c)

def mp7_design(device):
    """Returns MP7 firmware design version."""
    design = read(device, 'ctrl.id.fwrev.design')
    return design

# -----------------------------------------------------------------------------
#  TTY colors and helpers
# -----------------------------------------------------------------------------

RedStyle = tty.White + tty.Bold + tty.BackgroundRed
GreenStyle = tty.White + tty.Bold + tty.BackgroundGreen
YellowStyle = tty.White + tty.Bold + tty.BackgroundYellow
RedStyle = tty.White + tty.Bold + tty.BackgroundRed
BlueStyle = tty.White + tty.Bold + tty.BackgroundBlue

def get_style(item):
    """Returns style for fancy header according to error level of item."""
    if item.is_error:
        return RedStyle
    if item.is_warning:
        return YellowStyle
    return BlueStyle

class FancyHeader(object):
    """Render fancy colored title bar with left and optional right content."""

    def __init__(self, style=BlueStyle, width=80):
        self.style = style
        self.width = width

    def render(self, left, right=""):
        left, right = format(left), format(right)
        left_width = (self.width - 2) - len(right)
        right_width = len(right)
        content = "{0:<{1}}{2:>{3}}".format(left, left_width, right, right_width)
        return "{0} {1} {2}".format(self.style, content, tty.Reset)

# -----------------------------------------------------------------------------
#  Device property classes
# -----------------------------------------------------------------------------

class DeviceProperty(object):

    def __init__(self, name, label=None, callback=None, template=None, version_format=False):
        self.name = name
        self.label = label or name
        self.callback = callback
        self.template = template or "{}"
        self.version_format = False
        # Retrieved information
        self.value = None
        self.is_warning = False
        self.is_error = False
        self.message = ""

    def dispatch(self):
        """Dispatch property value by executing assigned callback function."""
        try:
            self.value = self.callback() if self.callback else None
        except:
            self.value = None
            self.is_error = True

    def padded_hex(val, l):
        hex_result = hex(val)[2:] # remove '0x' from beginning of str
        num_hex_chars = len(hex_result)
        lead_zeros = '0' * (l - num_hex_chars) # may not get used.
        return ('0x' + hex_result if num_hex_chars == l else
                '0x' + lead_zeros + hex_result if num_hex_chars < l else
                None)

    def render(self):
        """Render property for device listing.
        >>> print property.render()
        '    board ID : 10'
        """
        # Set proper visual appeareance for TTY
        style = tty.Reset
        if self.is_error:
            style = tty.Red+tty.Bold
        elif self.is_warning:
            style = tty.Yellow+tty.Bold

        if self.version_format:
            value=padded_hex(self.value,8)
        else:
            # Apply custom string formatting templates if value not None
            value = '' if self.value is None else self.template.format(self.value)

        message = ""
        if self.message:
            message = "{}{:>24} : *** {:<49}".format(os.linesep, "", self.message)
        # Return endered item
        return "{}{:>24} : {:<53}{}{}".format(style, self.label, value, message, tty.Reset)

class Device(object):

    def __init__(self, device):
        self.device = device
        self.is_present = False
        self.properties = {}
        self.properties_order = []
        self.is_warning = False
        self.is_error = False

    @property
    def slot(self):
        return slot_number(self.device)

    @property
    def ordered_properties(self):
        """Returns ordered list of properties."""
        unordered = list(set(self.properties.keys()) - set(self.properties_order))
        properties_order = self.properties_order + unordered
        return sorted(self.properties.values(), key=lambda prop: properties_order.index(prop.name))

    def add_property(self, name, label=None, callback=None, template=None, version_format=False):
        prop = DeviceProperty(name, label, callback, template, version_format)
        self.properties[name] = prop
        setattr(self, name, prop)

    def dispatch(self):
        for prop in self.properties.values():
            prop.dispatch()

    def render(self):
        """Render device header and properties."""
        lines = []
        slot = "slot #{}".format(self.slot)
        style = BlueStyle
        if self.is_warning:
            style = YellowStyle
        if self.is_error:
            style = RedStyle
        lines.append(FancyHeader(get_style(self)).render(self.device, slot))
        for prop in self.ordered_properties:
            lines.append(format(prop.render()))
        return os.linesep.join(lines)

class MP7Device(Device):

    def __init__(self, device):
        super(MP7Device, self).__init__(device)
        self.add_property('mp7_firmware', "MP7 firmware version", self._mp7_version)
        self.add_property('mp7_design', "MP7 design", self._mp7_design)
        self.properties_order = [
            'mp7_firmware',
            'mp7_design',
        ]

    def _mp7_present(self):
        """Returns True if device is accessible (assumingly present)."""
        try:
            read(self.device, 'ctrl.id')
        except uhal._core.exception:
            return False
        return True

    def _mp7_version(self):
        """Returns MP7 firmware version."""
        a = read(self.device, 'ctrl.id.fwrev.a')
        b = read(self.device, 'ctrl.id.fwrev.b')
        c = read(self.device, 'ctrl.id.fwrev.c')
        return "{0}.{1}.{2}".format(a, b, c)

    def _mp7_design(self):
        """Returns MP7 firmware design version."""
        design = read(self.device, 'ctrl.id.fwrev.design')
        return design

    def dispatch(self):
        """Detect if board is present, if so dispatch all properties."""
        self.is_present = self._mp7_present()
        if self.is_present:
            super(MP7Device, self).dispatch()

class GtDevice(MP7Device):

    def __init__(self, device):
        super(GtDevice, self).__init__(device)
        self.add_property(
            name='menu_name',
            label="menu name",
            callback=lambda: read(self.device, 'gt_mp7_gtlfdl.read_versions.l1tm_name', translate=True)
        )
        self.add_property(
            name='menu_uuid',
            label="menu UUID",
            callback=lambda: read(self.device, 'gt_mp7_gtlfdl.read_versions.l1tm_uuid', translate=True)
        )
        self.add_property(
            name='menu_uuid_fw',
            label="menu firmware UUID",
            callback=lambda: read(self.device, 'gt_mp7_gtlfdl.read_versions.l1tm_fw_uuid', translate=True)
        )
        self.add_property(
            name='module_id',
            label="module ID",
            callback=lambda: read(self.device, 'gt_mp7_gtlfdl.read_versions.module_id')
        )
        self.add_property(
            name='producer_version',
            label="VHDL producer version",
            callback=lambda: read(self.device, 'gt_mp7_gtlfdl.read_versions.l1tm_compiler_version', translate=True)
        )
        self.add_property(
            name='timestamp',
            callback=lambda: read(self.device, 'gt_mp7_frame.module_info.timestamp', translate=True)
        )
        self.add_property(
            name='hostname',
            callback=lambda: read(self.device, 'gt_mp7_frame.module_info.hostname', translate=True)
        )
        self.add_property(
            name='username',
            callback=lambda: read(self.device, 'gt_mp7_frame.module_info.username', translate=True)
        )
        self.add_property(
            name='build_version',
            label="build version",
            template="0x{:04x}",
            callback=lambda: read(self.device, 'gt_mp7_frame.module_info.build_version')
        )
        self.add_property(
            name='payload_version',
            label="uGT payload version",
            callback=lambda: read(self.device, 'gt_mp7_frame.module_info.frame_version', translate=True)
        )
        self.add_property(
            name='gtl_version',
            label="GTL version",
            callback=lambda: read(self.device, 'gt_mp7_gtlfdl.read_versions.gtl_fw_version', translate=True)
        )
        self.add_property(
            name='fdl_version',
            label="FDL version",
            callback=lambda: read(self.device, 'gt_mp7_gtlfdl.read_versions.fdl_fw_version', translate=True)
        )
        self.add_property(
            name='frame_version',
            label="frame version",
            version_format=True,
            callback=lambda: read(self.device, 'gt_mp7_gtlfdl.read_versions.svn_revision_number', translate=True)
        )

        self.properties_order = [
            'module_id',
            'menu_name',
            'menu_uuid',
            'menu_uuid_fw',
            'producer_version',
            'timestamp',
            'hostname',
            'username',
            'build_version',
            'payload_version',
            'frame_version',
            'gtl_version',
            'fdl_version',
        ] + self.properties_order

    def dispatch(self):
        super(GtDevice, self).dispatch()
        if self.is_present:
            # Validations
            if self.module_id.value != (self.slot - 1):
                self.module_id.is_warning = True
                self.module_id.message = "wrong slot number?"
                self.is_warning = True


    def match(self, other):
        """Match with reference device."""
        assert isinstance(other, GtDevice)
        if self.menu_name.value != other.menu_name.value:
            self.menu_name.is_warning = True
            self.menu_name.message = "menu name does not match module #{}".format(other.slot)
            self.is_warning = True
        if self.menu_uuid.value != other.menu_uuid.value:
            self.menu_uuid.is_warning = True
            self.menu_uuid.message = "menu UUID does not match module #{}".format(other.slot)
            self.is_warning = True
        if self.menu_uuid_fw.value != other.menu_uuid_fw.value:
            self.menu_uuid_fw.is_warning = True
            self.menu_uuid_fw.message = "firmware UUID does not match module #{}".format(other.slot)
            self.is_warning = True

class AMC502Device(MP7Device):

    def __init__(self, device):
        super(AMC502Device, self).__init__(device)
        self.add_property(
            name='board_id',
            label="board ID",
            callback=lambda: read(self.device, 'payload.module_info.board_id')
        )
        self.add_property(
            name='build_version',
            label="build version",
            template="0x{:04x}",
            callback=lambda: read(self.device, 'payload.module_info.build_version')
        )
        self.properties_order = [
            'board_id',
            'build_version',
        ] + self.properties_order

    def dispatch(self):
        super(AMC502Device, self).dispatch()
        if self.is_present:
            # Validations
            if self.board_id.value != self.slot:
                self.board_id.is_warning = True
                self.board_id.message = "wrong slot number?"

class FinorDevice(AMC502Device):

    def __init__(self, device):
        super(FinorDevice, self).__init__(device)
        self.add_property(
            name='timestamp',
            label="timestamp (synthesis)",
            callback=lambda: read(self.device, 'payload.module_info.timestamp', translate=True)
        )
        self.add_property(
            name='username',
            label="username (creator)",
            callback=lambda: read(self.device, 'payload.module_info.username', translate=True)
        )

class PreviewDevice(FinorDevice):

    def __init__(self, device):
        super(PreviewDevice, self).__init__(device)

class ExtcondDevice(AMC502Device):

    def __init__(self, device):
        super(ExtcondDevice, self).__init__(device)

    def match(self, other):
        """Match with reference device."""
        assert isinstance(other, ExtcondDevice)
        if self.build_version.value != other.build_version.value:
            self.build_version.is_warning = True
            self.build_version.message = "build version mismatch"
            self.is_warning = True

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
            self.set_text(slot, 1, " MP7 ")
            self.set_color(slot, GreenStyle)
        for slot in range(7, 12 + 1):
            self.reset(slot)
            self.set_text(slot, 1, " AMC ")
            self.set_text(slot, 2, " 502 ")
            self.set_color(slot, GreenStyle)
        self.reset(13)
        self.set_text(13, 1, "AMC13")
        self.set_color(13, GreenStyle)
        self.reset(14)
        self.set_text(14, 1, " MCH ")
        self.set_color(14, GreenStyle)
        self.is_warning = False
        self.is_error = False

    def create(self, slot):
        """Create empty content for slot."""
        lines = 9
        if slot > 12:
            lines = 4
        content = {}
        for line in range(lines):
            content[line] = " " * 5
        return content

    def encode(self, slot, line):
        """Encode slot/line to template placeholders."""
        return "{0:02d}%{1:02d}".format(slot, line)

    def reset(self, slot):
        """Reset text and colors for slot."""
        self.content[slot] = self.create(slot)
        self.set_color(slot, tty.Bold)

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
                value = "{}{}{}".format(self.colors[slot], value, tty.Reset)
                template = template.replace(self.encode(slot, line), value)
        return template

# -----------------------------------------------------------------------------
#  Parse command line args
# -----------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', action='store_true', help="show more information")
args = parser.parse_args(TDF_ARGS)

# -----------------------------------------------------------------------------
#  Create records
# -----------------------------------------------------------------------------

gt_devices = [
    GtDevice('gt_mp7.1'),
    GtDevice('gt_mp7.2'),
    GtDevice('gt_mp7.3'),
    GtDevice('gt_mp7.4'),
    GtDevice('gt_mp7.5'),
    GtDevice('gt_mp7.6'),
]
finor_devices = [
    PreviewDevice('finor_amc502.7'),
    PreviewDevice('finor_pre_amc502.8'),
]
extcond_devices = [
    ExtcondDevice('extcond_amc502.9'),
    ExtcondDevice('extcond_amc502.10'),
    ExtcondDevice('extcond_amc502.11'),
    ExtcondDevice('extcond_amc502.12'),
]

devices = []
devices.extend(gt_devices)
devices.extend(finor_devices)
devices.extend(extcond_devices)

# Dispatch devices
for device in devices:
    device.dispatch()

# Match MP7 devices
ref_gt_device = (filter(lambda device: device.is_present, gt_devices) or [None])[0]
for device in [device for device in gt_devices if device.is_present]:
    if ref_gt_device:
        device.match(ref_gt_device)

# Match Extcond devices
ref_extcond_device = (filter(lambda device: device.is_present, extcond_devices) or [None])[0]
for device in [device for device in extcond_devices if device.is_present]:
    if ref_extcond_device:
        device.match(ref_extcond_device)

# Build crate
crate = CrateLayout()

for device in devices:
    if device.is_present:
        if device.is_warning:
            crate.set_color(device.slot, YellowStyle)
            crate.is_warning = True
        if device.is_error:
            crate.set_color(device.slot, RedStyle)
            crate.is_error = True
    else:
        crate.reset(device.slot)
        crate.set_text(device.slot, 1, " n/a ")

print
print FancyHeader(get_style(crate)).render("Crate Status")
print crate.render()

# Print device reports
for device in devices:
    if device.is_present:
        print device.render()
        print

# Collect earnings/errors.
warnings = 0
errors = 0
for device in devices:
    if device.is_present:
        if device.is_warning:
            warnings += 1
        if device.is_error:
            errors += 1

# Dump warnings/errors.
if warnings:
    print FancyHeader(YellowStyle).render("Warnings: {}".format(warnings))
    print
if errors:
    print FancyHeader(RedStyle).render("Errors: {}".format(errors))
    print
if not (warnings or errors):
    print FancyHeader(GreenStyle).render("All is well!")
    print
