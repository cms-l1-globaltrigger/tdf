from tdf.extern import argparse
from tdf.core import tty
from tdf.core.xmlmenu import XmlMenu

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

# Get rates from memory image
rates = dump(devices[args.slot], 'payload.rate_cnt_extcond').data

# Enumerate
rates = list(enumerate(rates))

# Sort by rate if required
if args.sort:
    reverse = dict(asc=False, desc=True)[args.sort]
    rates.sort(
        key=lambda item: (item[1]),
        reverse=reverse
    )

print "|---------|----------|---------------------------------|--------|--------------|"
print "| Channel | Rate     | Name                            | System | Label        |"
print "|---------|----------|---------------------------------|--------|--------------|"
for channel, rate in rates:
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
    print "| {channel:>7d} | {rate_style}{rate:>8d}{tty.Reset} | {name:<31} | {system:<6} | {label:<12} |".format(**locals())
print "|---------|----------|---------------------------------|--------|--------------|"
