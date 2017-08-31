from tdf.extern import argparse
import subprocess
import sys, os

DEFAUT_SLOTS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

COMMANDS = [
    "/opt/vadatech/IPMI/tools/cliUTCSH/power_channel_control -a 0x82 -f 50 -c {pcn} -M 0 -i 50 -I 51 -l 80",
    "/opt/vadatech/IPMI/tools/cliUTCSH/power_channel_control -a 0x82 -f 51 -c {pcn} -M 0 -i 50 -I 51 -l 80",
    "/opt/vadatech/IPMI/tools/cliUTCSH/power_channel_control -a 0x82 -f 50 -c {pcn} -P 0 -i 50 -I 51 -l 80",
    "/opt/vadatech/IPMI/tools/cliUTCSH/power_channel_control -a 0x82 -f 51 -c {pcn} -P 0 -i 50 -I 51 -l 80",
    "/opt/vadatech/IPMI/tools/cliUTCSH/power_channel_control -a 0x82 -f 50 -c {pcn} -M 1 -i 50 -I 51 -l 80",
    "/opt/vadatech/IPMI/tools/cliUTCSH/power_channel_control -a 0x82 -f 51 -c {pcn} -M 1 -i 50 -I 51 -l 80",
    "/opt/vadatech/IPMI/tools/cliUTCSH/power_channel_control -a 0x82 -f 50 -c {pcn} -P 1 -i 50 -I 51 -l 80",
    "/opt/vadatech/IPMI/tools/cliUTCSH/power_channel_control -a 0x82 -f 51 -c {pcn} -P 1 -i 50 -I 51 -l 80",
    "/opt/vadatech/IPMI/tools/cliUTCSH/power_channel_control -a 0x82 -f 50 -c {pcn} -A 1 -i 50 -I 51 -l 80",
    "/opt/vadatech/IPMI/tools/cliUTCSH/power_channel_control -a 0x82 -f 51 -c {pcn} -A 1 -i 50 -I 51 -l 80",
]

# Comamnd line parser
parser = argparse.ArgumentParser()
parser.add_argument('hostname', help="MCH hostname")
parser.add_argument('slot', type=int, choices=DEFAUT_SLOTS, help="slot number")
parser.add_argument('-u', '--user', default='root', help="user, default is root")
args = parser.parse_args(TDF_ARGS)

# Calculate the power channel number for target AMC slot (slot + 4)
power_channel_number = args.slot + 4

TDF_WARNING("power cycling AMC module in slot #{0}".format(args.slot))

# Issue a SSH command
command = [
    'ssh',
    '{0}@{1}'.format(args.user, args.hostname),
    os.linesep.join(COMMANDS).format(pcn=power_channel_number)
]

result = subprocess.call(command)

if result > 1: # [sic] might be also 1 but executes still fine
    raise RuntimeError("ssh command failed with return code '{0}'".format(result))
