# testvector_split.py
# Split a testvector by information read from XML menu.
from tdf.core.xmlmenu import XmlMenu
from tdf.core.testvector import TestVector
from tdf.core.xmlmenu import XmlMenu
from tdf.extern import argparse
import sys, os, copy

parser = argparse.ArgumentParser(description="Split text vector into modules by information from XML file")
parser.add_argument('testvector', help="test vector file")
parser.add_argument('menu', help="XML menu file")
parser.add_argument('-o', metavar='<path>', default=os.getcwd(), help="path to output location")
args = parser.parse_args(TDF_ARGS)

TDF_INFO("parsing", args.testvector)
testvector = TestVector(args.testvector)

TDF_INFO("parsing", args.menu)
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
    module_tv = copy.deepcopy(testvector)
    with open(os.path.join(args.o, filename), 'w') as fp:
        # Calculate algorithms mask
        mask = 0x0
        for algorithm in algorithms:
            mask |= (1 << algorithm.module_index)
        TDF_INFO("applying algorithm mask", TDF.ALGORITHM.hexstr(mask))
        # Write masked output to file
        for bx, algorithms in enumerate(module_tv._algorithms):
            module_tv._algorithms[bx] = algorithms & mask
        TDF_INFO("writing", fp.name)
        fp.write(str(module_tv))
