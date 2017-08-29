from tdf.extern import argparse
from tdf.core import TDF
from tdf.core.binutils import bitmask
from collections import Counter
import sys, os
import time

DEFAULT_OFFSET = 10
MAX_MODULES = 6
FW_BUILD = 0xabc3

FINOR_CABLE = 0
VETO_CABLE = 1
FINOR2TCDS_CABLE = 2

parser = argparse.ArgumentParser()
parser.add_argument('--modules', metavar='<n>[-<m>]', help="single module or range of modules (default 0-5)")
parser.add_argument('--offset', metavar='<n>', default=DEFAULT_OFFSET, type=int, help="take sample data with offset (default {})".format(DEFAULT_OFFSET))
parser.add_argument('--reset', action='store_true', help="reset AMC502 logic before test")
args = parser.parse_args(TDF_ARGS)

# variable for the final output
errors = False

modules = range(MAX_MODULES)

# sets the new range in the for loops
if args.modules:
    nm = args.modules.split('-')
    modules = range(int(nm[0]), int(nm[-1])+1)

# Source devices
ugt_devices = {
    0: 'gt_mp7.1',
    1: 'gt_mp7.2',
    2: 'gt_mp7.3',
    3: 'gt_mp7.4',
    4: 'gt_mp7.5',
    5: 'gt_mp7.6',
}

finor_device = 'finor_amc502.7'
finor_pre_device = 'finor_pre_amc502.8'

# FinOR devices by cable number
finor_devices = {
    FINOR_CABLE: finor_device,
    VETO_CABLE: finor_device,
    FINOR2TCDS_CABLE: finor_pre_device,
}

cables = (
    FINOR_CABLE,
    VETO_CABLE,
    FINOR2TCDS_CABLE,
)

# the different cables and names
cable_names = {
    FINOR_CABLE: 'finOR cable',
    VETO_CABLE: 'veto cable',
    FINOR2TCDS_CABLE: 'finOR preview cable',
}

if args.reset:
    # Reset AMC502 logic
    amc502butler('reset', finor_device, '--clksrc=external')
    amc502butler('reset', finor_pre_device, '--clksrc=external')

# Setup target inputs
for index in range(MAX_MODULES):
    write(finor_device, 'payload.input_masks.module_{}'.format(index), 0)
    write(finor_pre_device, 'payload.input_masks.module_{}'.format(index), 0)

# Setup target inputs
for index in modules:
    write(finor_device, 'payload.input_masks.module_{}'.format(index), 1)
    write(finor_pre_device, 'payload.input_masks.module_{}'.format(index), 1)

# Setup source modules
for index in modules:
    device = ugt_devices[index]

    # Verify firmware version
    build = read(device, "gt_mp7_frame.module_info.build_version")
    if build != FW_BUILD:
        TDF_WARNING("device={}, loaded firmware 0x{:04x} probably not suitable for"
                    "this test (expected 0x{:04x})".format(device, build, FW_BUILD))

    for cable in cables:
        # Configure output MUX
        write(device, 'gt_mp7_tp_mux.tp_mux.out{}'.format(cable), 0x14)
        # Disable cable output
        write(device, 'gt_mp7_tp_mux.test_out{}'.format(cable), 0)

for index in modules:
    source_device = ugt_devices[index]
    for cable in cables:
        # Enable current cable
        write(source_device, 'gt_mp7_tp_mux.test_out{}'.format(cable), 1)

        time.sleep(0.1)

        # Select target device by cable number
        target_device = finor_devices[cable]
        write(target_device, 'payload.spy12_next_event', 1)

        # Fetch raw memory to decode and cross-check...
        spymem = dump(target_device, 'payload.spymem')

        # Check for jitter
        samples = spymem.merged()[1:TDF.ORBIT_LENGTH]
        counter = Counter(samples)
        if len(counter) != 1:
            errors += 1
            TDF_ERROR("DETECTED JITTER:")
            for key, count in counter.iteritems():
                TDF_ERROR("  value=0x{:08x} count={} times".format(key, count))

        # Fetch sample memory line
        # bits [xxxxxxxTxxVVVVVVxxFFFFFF]  T=finor2tcds, V=veto, F=finor
        sample = spymem.merged()[args.offset]
        sample_finor = (sample >> (0 + index)) & bitmask(6)
        sample_veto = (sample >> (8 + index)) & bitmask(6)
        sample_finor2tcds = (sample >> 16) & bitmask(1)

        # Cross check (no other bit must be active)
        reference = (sample_finor2tcds << 16) | (sample_veto << (8 + index)) | (sample_finor << (0 + index))
        if sample != reference:
            errors += 1
            TDF_ERROR("CROSS-CHECK FAILED: sample={:08x} (reference={:08x})".format(sample, reference))

        TDF_NOTICE(
            "source={}, target={}, cable={}, sample=0x{:08x}, finor={}, veto={}, finor2tcds={}".format(
                device, target_device, cable, sample, sample_finor, sample_veto, sample_finor2tcds)
        )

        success = False

        if cable == FINOR_CABLE:
            if sample_finor == 1:
                success = True

        elif cable == VETO_CABLE:
            if sample_veto == 1:
                success = True

        elif cable == FINOR2TCDS_CABLE:
            if sample_finor == 1:
                success = True

        if not success:
            errors += 1
            TDF_ERROR("error at connection : {} => {}".format(source_device, target_device))
            TDF_ERROR("              cable : #{} ({})".format(cable, cable_names[cable]))
            TDF_ERROR("*** cable not connected!")

        time.sleep(0.1)

        # Disable current cable
        write(source_device, 'gt_mp7_tp_mux.test_out{}'.format(cable), 0)

# if any error was found err is true
if errors:
    TDF_ERROR(errors, "errors found!")
else:
    TDF_NOTICE("No errors found")
