# Read UUID's of quad lanes.
from tdf.extern import argparse

parser = argparse.ArgumentParser()
parser.add_argument('device', help = "device defined in connections file")
parser.add_argument('quads', default = 17, nargs = '?', type = int, help = "number of quads, default 17")
args = parser.parse_args(TDF_ARGS)

report = []

for quad in range(args.quads):
    write(args.device, "ctrl.csr.ctrl.quad_sel", quad)
    report.append("quad {quad}".format(**locals()))
    for i in range(4):
        rx_trailer = read(args.device, "datapath.region.mgt.ro_regs.ch{i}.rx_trailer".format(**locals()))
        report.append(" ch{i}: 0x{rx_trailer}".format(**locals()))

print "\n".join(report)
