# delete GT firmware bitfiles from uSD card(s).

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
        result = re.search(r"([\w_\.]+\.bit)", line.strip())
        if result:
            filenames.append(result.group(1))
    # Close the temporary file.
    tmp.close()
    # Return list of bitfiles.
    return filenames

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
parser.add_argument('file', nargs="+", help = "bitfiles to delete from the SD card. double check the filename, because the script will crash on missing files.")
args = parser.parse_args(TDF_ARGS)

print
print " => checking uSD card contents on device `{args.device}'...".format(**locals())

# Read stdout results from butler command (bitfiles located on uSD).
filenames = scansd(args.device)

for filename in args.file:

    if filename in filenames:
        # If file with same name already exists, delete it:
        print " => bit file `{filename}' found on the SD card, deleting...".format(**locals())
        mp7butler("deletefw", args.device, filename)
    else:
        print " ! ignoring non exising file `{filename}' ...".format(**locals())
