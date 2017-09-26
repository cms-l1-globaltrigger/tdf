# Crate status
# -*- coding: utf-8 -*-

from tdf.extern import argparse
from tdf.core.toolbox import slot_number, device_type
from tdf.core import tty

from distutils.version import StrictVersion
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
    """Retruns True if device is accessible (assumingly present)."""
    try:
        read(device, 'ctrl.id')
    except uhal._core.exception:
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
#  TTY colors and helpers
# -----------------------------------------------------------------------------

RedStyle = tty.White + tty.Bold + tty.BackgroundRed
GreenStyle = tty.White + tty.Bold + tty.BackgroundGreen
YellowStyle = tty.White + tty.Bold + tty.BackgroundYellow
RedStyle = tty.White + tty.Bold + tty.BackgroundRed
BlueStyle = tty.White + tty.Bold + tty.BackgroundBlue

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

    def __init__(self, name, label=None, callback=None, template=None):
        self.name = name
        self.label = label or name
        self.callback = callback
        self.template = template or "{}"
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
        # Apply custom string formatting templates
        value = self.template.format(self.value)
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

    def add_property(self, name, label=None, callback=None, template=None):
        prop = DeviceProperty(name, label, callback, template)
        self.properties[name] = prop
        setattr(self, name, prop)

    def dispatch(self):
        for prop in self.properties.values():
            prop.dispatch()

    def render(self):
        """Render device header and properties."""
        lines = []
        slot = "slot #{}".format(self.slot)
        lines.append(FancyHeader(BlueStyle).render(self.device, slot))
        for prop in self.ordered_properties:
            lines.append(format(prop.render()))
        return os.linesep.join(lines)

class MP7Device(Device):

    def __init__(self, device):
        super(MP7Device, self).__init__(device)
        self.add_property('mp7_firmware', "MP7 firmware", self._mp7_version)
        self.add_property('mp7_design', "MP7 design", self._mp7_design)
        self.properties_order = [
            'mp7_firmware',
            'mp7_design',
        ]

    def _mp7_present(self):
        """Retruns True if device is accessible (assumingly present)."""
        try:
            read(self.device, 'ctrl.id')
        except uhal._core.exception:
            return False
        return True

    def _mp7_version(self):
        """Retruns MP7 firmware version."""
        a = read(self.device, 'ctrl.id.fwrev.a')
        b = read(self.device, 'ctrl.id.fwrev.b')
        c = read(self.device, 'ctrl.id.fwrev.c')
        return "{0}.{1}.{2}".format(a, b, c)

    def _mp7_design(self):
        """Retruns MP7 firmware design version."""
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
            label="VHDL producer",
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
            label="uGT build",
            template="0x{:04x}",
            callback=lambda: read(self.device, 'gt_mp7_frame.module_info.build_version')
        )
        self.add_property(
            name='payload_version',
            label="payload (frame) version",
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

        self.properties_order = [
            'menu_name',
            'menu_uuid',
            'menu_uuid_fw',
            'module_id',
            'producer_version',
            'timestamp',
            'hostname',
            'username',
            'build_version',
            'payload_version',
            'gtl_version',
            'fdl_version',
        ] + self.properties_order

    def dispatch(self):
        super(GtDevice, self).dispatch()

        # Validations
        if self.module_id.value != (self.slot - 1):
            self.module_id.is_warning = True
            self.module_id.message = "wrong slot number?"

        # if self.is_present:
        #     if StrictVersion(self.gtl_version.value) < StrictVersion("1.4.1"):
        #         self.gtl_version.is_warning = True
        #         self.gtl_version.message = "outdated GTL logic"

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
            label="username (crator)",
            callback=lambda: read(self.device, 'payload.module_info.username', translate=True)
        )

class PreviewDevice(FinorDevice):

    def __init__(self, device):
        super(PreviewDevice, self).__init__(device)

class ExtcondDevice(AMC502Device):

    def __init__(self, device):
        super(ExtcondDevice, self).__init__(device)

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

devices = []
devices.append(GtDevice('gt_mp7.1'))
devices.append(GtDevice('gt_mp7.2'))
devices.append(GtDevice('gt_mp7.3'))
devices.append(GtDevice('gt_mp7.4'))
devices.append(GtDevice('gt_mp7.5'))
devices.append(GtDevice('gt_mp7.6'))
devices.append(PreviewDevice('finor_pre_amc502.8'))
devices.append(ExtcondDevice('extcond_amc502.9'))
devices.append(ExtcondDevice('extcond_amc502.9'))
devices.append(ExtcondDevice('extcond_amc502.10'))
devices.append(ExtcondDevice('extcond_amc502.11'))
devices.append(ExtcondDevice('extcond_amc502.12'))

for device in devices:
    device.dispatch()

crate = CrateLayout()

for device in devices:
    if not device.is_present:
        crate.reset(device.slot)
        crate.set_text(device.slot, 1, " n/a ")
    elif device.is_warning:
        crate.set_color(device.slot, YellowStyle)
    elif device.is_error:
        crate.set_color(device.slot, RedStyle)
    # Add additional checks...

print
print FancyHeader().render("Crate Status")
print crate.render()

for device in devices:
    if device.is_present:
        print device.render()
        print
