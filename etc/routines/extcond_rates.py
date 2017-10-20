from tdf.extern import argparse
from tdf.core import tty
from tdf.core.xmlmenu import XmlMenu

LUMI_SEC = 23.312

devices = {
    9: 'extcond_amc502.9',
    10: 'extcond_amc502.10',
    11: 'extcond_amc502.11',
    12: 'extcond_amc502.12',
}

parser = argparse.ArgumentParser()
parser.add_argument('slot', choices=devices.keys(), type=int, help="slot number (9..12)")
parser.add_argument('--menu', help="L1Menu XML filename")
parser.add_argument('--sort', default=None, choices=('asc', 'desc'), help="sort by rate asc/desc")
args = parser.parse_args(TDF_ARGS)

if args.menu:
    menu = XmlMenu(args.menu)

# Get counts from memory image
counts = dump(devices[args.slot], 'payload.rate_cnt_extcond').data

# Enumerate
counts = list(enumerate(counts))

# Sort by rate if required
if args.sort:
    reverse = dict(asc=False, desc=True)[args.sort]
    counts.sort(
        key=lambda item: (item[1]),
        reverse=reverse
    )

print "|---------|-----------|----------|--------------------------------|--------|--------------|"
print "| Channel | Rate (Hz) | Count    | Name                           | System | Label        |"
print "|---------|-----------|----------|--------------------------------|--------|--------------|"
for channel, count in counts:
    rate = count / LUMI_SEC
    name = 'n/a'
    system = ''
    label = ''
    rate_style = tty.Reset
    if rate:
        rate_style = tty.Bold
    if args.menu:
        items = filter(lambda item: item.channel == channel, menu.externals)
        if items:
            item = items[0]
            name = item.name[:31]
            system = item.system[:9]
            label = item.label[:12]
    print "| {channel:>7d} | {rate_style}{rate:>9.1f}{tty.Reset} | {rate_style}{count:>8d}{tty.Reset} | {name:<30} | {system:<6} | {label:<12} |".format(**locals())
print "|---------|-----------|----------|--------------------------------|--------|--------------|"
