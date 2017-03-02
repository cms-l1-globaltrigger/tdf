# Load GT firmware from uSD card(s).

from tdf.extern import argparse
import tarfile
import tempfile
import shutil
import re, os

def scansd(device):
    """Read stdout results from butler command (bitfiles located on uSD).
    Returns list of filenames stored on uSD card.
    """
    # Create temporary file in memory.
    tmp = tempfile.SpooledTemporaryFile()
    # Capture stdout from butler (should contain list of bitfiles).
    mp7butler("scansd", device, stderr = tmp)
    # Set file pointer to begin of temporary file.
    tmp.seek(0)
    # Read content of temporary file.
    filenames = []
    for line in tmp.readlines():
        result = re.search(r"([\w_\.]+\.(bit|bin))", line.strip())
        if result:
            filenames.append(result.group(1))
    # Close the temporary file.
    tmp.close()
    # Return list of bitfiles.
    return filenames

def build_t(value):
    """Firmware build number validation (four digit hex code)."""
    value = value.lower()
    if not re.match("^[\da-f]{4}$", value):
        raise ValueError("not a build number: {value}".format(**locals()))
    return value

parser = argparse.ArgumentParser()
parser.add_argument('build', type=build_t, help = "firmware build number (eg. 10a5)")
parser.add_argument('modules', type=int, help = "number of uGT modules")
args = parser.parse_args(TDF_ARGS)

# Default module to device mapping.
device_mapping = {
    0: 'gt_mp7.1',
    1: 'gt_mp7.2',
    2: 'gt_mp7.3',
    3: 'gt_mp7.4',
    4: 'gt_mp7.5',
    5: 'gt_mp7.6',
}


# Upload files to uSD cards.
for module in range(args.modules):
    device = device_mapping[module]
    filename = "gt_mp7_xe_v{args.build}_module_{module}.bin".format(**locals())

    print
    print " => checking uSD card contents on device `{device}'...".format(**locals())

    # Read stdout results from butler command (bitfiles located on uSD).
    filenames = scansd(device)
    print " => current files on uSD card:"
    print "\n".join(filenames)

    # If file with same name already exists, delete it on force.
    if filename not in filenames:
        message = "bin file `{filename}' does not exist. Use upload_gt routine to load it onto the uSD card".format(**locals())
        raise RuntimeError(message)

    print " => rebootfpga `{filename}' on device `{device}'".format(**locals())
    mp7butler("rebootfpga", device, filename)

