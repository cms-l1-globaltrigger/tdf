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
parser.add_argument('device', help = "device defined in connections file")
parser.add_argument('file', nargs="+", help = "bitfiles to delete from the SD card. double check the filename, because the script will crash on missing files.")
args = parser.parse_args(TDF_ARGS)

device = args.device
print
print " => checking uSD card contents on device `{device}'...".format(**locals())

# Read stdout results from butler command (bitfiles located on uSD).
filenames = scansd(device)
    
for filename in args.file:


    # If file with same name already exists, delete it:
    print " => bit file `{filename}' found on the SD card, deleting...".format(**locals())
    mp7butler("deletefw", device, filename)

device = args.device
print
print " => checking uSD card contents on device `{device}'...".format(**locals())

# Read stdout results from butler command (bitfiles located on uSD).
filenames = scansd(device)
