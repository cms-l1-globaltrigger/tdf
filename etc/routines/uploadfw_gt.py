# Upload GT firmware tarball to uSD card(s).

from tdf.extern import argparse
import tarfile
import tempfile
import shutil
import re, os

def scansd(device):
    """Read stdout results from butler command (bitfiles located on uSD).
    Returns list of filenames stored on uSD card.
    """
    import tempfile
    # Create temporary file in memory.
    tmp = tempfile.SpooledTemporaryFile()
    # Capture stdout from butler (should contain list of bitfiles).
    mp7butler("scansd", device, stdout = tmp)
    # Set file pointer to begin of temporary file.
    tmp.seek(0)
    # Read content of temporary file.
    result = tmp.read().strip().split("\n")
    # Close the temporary file.
    tmp.close()
    # Return list of bitfiles.
    return [filename.strip() for filename in result]

parser = argparse.ArgumentParser()
parser.add_argument('filename', help = "uGT firmware tarball (*.tar.gz)")
parser.add_argument('--map', dest = 'mapping', action = 'append', default = [], metavar = '<module>:<device>', help = "map module to device (eg. --map 0:gt_mp7.6)")
parser.add_argument('--rebootfpga', action = 'store_true', help = "load image into FPGA")
parser.add_argument('--force', action = 'store_true', help = "overwrite if file already exists on uSD card")
parser.add_argument('--dryrun', action = 'store_true', help = "do not apply any changes to uSD cards")
args = parser.parse_args(TDF_ARGS)

if args.dryrun:
    print "*** running in dryrun mode: does not apply any changes to uSD cards"

# Regular expression defining the tarball filename.
# eg. '(L1Menu_Sample)_v(1000)_(xe)-2015-01-01-T00-00-00.tar.gz'
regex_filename = re.compile(
    '(L1Menu_[a-zA-Z][0-9a-zA-Z_]+)_v([0-9a-f]{4})_([0-9a-zA-Z]+)\-20\d\d-\d\d-\d\d-[-T]\d\d-\d\d-\d\d.tar.gz')

result = regex_filename.match(os.path.basename(args.filename))
if not result:
    raise RuntimeError("Invalid filename for `{args.filename}'.\nNot a uGT firmware tarball?".format(**locals()))

# Extracting captured match groups.
menu, version, boardtype = result.groups()

print
print " => analyzing metadata:"
print "tarball   :", args.filename
print "menu      :", menu
print "version   :", version
print "boardtype :", boardtype

# Open the tarball.
tar = tarfile.open(args.filename, "r:gz")

# Collect bit files to extract.
bitfiles = []
for tarinfo in tar:
    if tarinfo.isreg():
        if tarinfo.name.endswith('.bit'):
            if not re.match('{menu}_v{version}_{boardtype}/module_[0-9]/build/gt_mp7_{boardtype}_v{version}_module_[0-9]\.bit'.format(**locals()), tarinfo.name):
                raise RuntimeError("Invalid filename for bitfile: `{tarinfo.name}'".format(**locals()))
            bitfiles.append(tarinfo.name)
bitfiles.sort()

# Bail out if no bit files found inside tarball.
if not bitfiles:
    raise RuntimeError("no bitfiles found in tarball `{args.filename}'.\nNot a uGT firmware tarball?".format(**locals()))

# Close the tarball.
tar.close()

# Default module to device mapping.
device_mapping = {
    0: 'gt_mp7.1',
    1: 'gt_mp7.2',
    2: 'gt_mp7.3',
    3: 'gt_mp7.4',
    4: 'gt_mp7.5',
    5: 'gt_mp7.6',
}

print
print " => calculate device mapping..."

# Overwrite default device mapping on demand.
for module, device in (entry.split(':') for entry in args.mapping):
    device_mapping[int(module)] = device

# Print device mapping table.
print "+---------------------------- Device Mapping Table ----------------------------+"
print "| {0:<10}| {1:<65}|".format("Module", "Bitfile")
print "+------------------------------------------------------------------------------+"
for module, bitfile in enumerate(bitfiles):
    device = device_mapping[module]
    print "| {0:<10}| {1:<65}|".format(device, os.path.basename(bitfile))
print "+------------------------------------------------------------------------------+"

# Upload files to uSD cards.
for module, bitfile in enumerate(bitfiles):
    device = device_mapping[module]
    filename = os.path.basename(bitfile)
    print
    print " => checking uSD card contents on device `{device}'...".format(**locals())

    # Read stdout results from butler command (bitfiles located on uSD).
    filenames = scansd(device)
    print " => current files on uSD card:"
    print "\n".join(filenames)

    # If file with same name already exists, delete it on force.
    if filename in filenames:
        if args.force:
            print
            print " => bit file `{filename}' does already exist, deleting...".format(**locals())
            if not args.dryrun:
                mp7butler("deletefw", device, filename)
        else:
            message = "bit file `{filename}' does already exist. Use `--force' to overwrite.".format(**locals())
            raise RuntimeError(message)

    # Extract the *.bit file from the tarball.
    tmpdir = tempfile.mkdtemp()
    tmp_filename = os.path.join(tmpdir, bitfile)
    tar = tarfile.open(args.filename, "r:gz")
    tar.extract(bitfile, tmpdir)
    tar.close()

    # Temporary extracted bitfile path/filename.
    tmp_filename = os.path.join(tmpdir, bitfile)
    print
    print " => extracted bit file to to temporary location `{tmp_filename}'".format(**locals())

    try:
        print
        print " => uploading `{filename}' to uSD on device `{device}'".format(**locals())
        if not args.dryrun:
            mp7butler("uploadfw", device, tmp_filename, filename)
        shutil.rmtree(tmpdir)
    except:
        # Note:
        # Make sure to remove the temporary directory at all cost.
        shutil.rmtree(tmpdir)
        raise # Re-raise the previous exception.

    if args.rebootfpga:
        print
        print " => rebootfpga `{filename}' on device `{device}'".format(**locals())
        if not args.dryrun:
            mp7butler("rebootfpga", device, filename)
