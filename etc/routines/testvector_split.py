# testvector_split.py
# Split a testvector by information read from XML menu.
from tdf.core.xmlmenu import XmlMenu
from tdf.core.testvector import TestVector
from tdf.core.xmlmenu import XmlMenu
from tdf.extern import argparse
import sys, os, copy

def calc_mask(algorithms):
    """Calculate algorithm mask using global indices."""
    mask = 0
    for algorithm in algorithms:
        mask |= (1 << algorithm.index)
    return mask

def mask_algorithms(tv, mask):
    """Masks algorithms using the global indices."""
    for bx, algorithms in enumerate(tv._algorithms):
        tv._algorithms[bx] = algorithms & mask

def update_finor(tv):
    """Update FinORs (after masking algorithms)."""
    tv._finor = [bool(algorithms) for algorithms in tv._algorithms]

parser = argparse.ArgumentParser(description="Split text vector into modules by information from XML file")
parser.add_argument('testvector', help="test vector file")
parser.add_argument('menu', help="XML menu file")
parser.add_argument('-o', metavar='<path>', default=os.getcwd(), help="path to output location")
args = parser.parse_args(TDF_ARGS)

TDF_INFO("reading", args.testvector)
tv = TestVector(args.testvector)

TDF_INFO("reading", args.menu)
menu = XmlMenu(args.menu)

TDF_INFO("menu name:", menu.name)
TDF_INFO("menu UUID:", menu.uuid_menu)
TDF_INFO("firmware UUID:", menu.uuid_firmware)

# Split algorithms by modules.
modules = {}
for algorithm in menu.algorithms:
    module_id = algorithm.module_id
    if module_id not in modules.keys():
        modules[module_id] = []
    modules[module_id].append(algorithm)

TDF_INFO("menu implements", len(modules.keys()), "module(s)")

# Write masked testvectors to files.
for module, algorithms in modules.iteritems():
    TDF_INFO("preparing testvector for module", module)
    basename = os.path.splitext(os.path.basename(args.testvector))[0]
    filename = "{basename}_module_{module}.txt".format(**locals())
    module_tv = copy.deepcopy(tv)
    with open(os.path.join(args.o, filename), 'w') as fp:
        mask = calc_mask(algorithms)
        TDF_INFO("update algorithm mask...", TDF.ALGORITHM.hexstr(mask))
        mask_algorithms(module_tv, mask)
        TDF_INFO("update FINOR using algorithm mask...")
        update_finor(module_tv)
        TDF_INFO("writing", fp.name)
        fp.write(str(module_tv))
