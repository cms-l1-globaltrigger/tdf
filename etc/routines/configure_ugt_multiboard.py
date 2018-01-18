# Tx_buffer function test
# for MP7 firmware >= 1.8.4
# Script sets up the uGT MP7 in run mode for global run

from tdf.extern import argparse
from tdf.core.testvector import TestVector
import os, re, sys
import time
import datetime

mp7path=os.environ.get('MP7_TESTS')
if mp7path == None:
    print "ERROR: Set the mp7sw environment before continuing."
    exit()
sys.path.append(mp7path+'/python/daq')

import re
import dtm
import uhal
import readline
import argparse
import logging
from mp7.tools.log_config import initLogging

DEFAULT_INPUT_DELAY = 11
DEFAULT_GTL_LATENCY = 6
DEFAULT_SIZE = 170
DEFAULT_RX_LINKS = '0-15'
DEFAULT_TX_LINKS = '16-24'
DEFAULT_CAP = 0
DEFAULT_FED_ID = 1404
DEFAULT_SLOT = 1-2
DEFAULT_ALGO_LATENCY = 45
DEFAULT_MASTER_LATENCY = 169
DEFAULT_SLOTS =[1, 2]

def result_area():
    from datetime import datetime
    dirname = "{0}_{1}".format(TDF_NAME, datetime.strftime(datetime.now(), "%Y-%m-%dT%H-%M-%S"))
    return dirname

parser = argparse.ArgumentParser()
parser.add_argument('device1', default = 'gt_mp7.1', help = "device defined in connections file")
parser.add_argument('device2', default = 'gt_mp7.2', help = "device defined in connections file")
parser.add_argument('--loopback', action = 'store_true', help = "run internal loopback mode (without cable)")
parser.add_argument('--pattern', default = ':counter', metavar = '<source>', help = "source test vector to be loaded into the TX buffers (or ':counter' for generic counter, default)")
parser.add_argument('--delay', default = DEFAULT_INPUT_DELAY, metavar = '<n>', type = int, help = "delay in BX for incomming data in spy memory, default is '{DEFAULT_INPUT_DELAY}'".format(**locals()))
parser.add_argument('--clksrc', choices = ("external", "internal"), default = "external", help = "clock source, default is 'external'")
parser.add_argument('--rx-links', '--links', default = DEFAULT_RX_LINKS, metavar = '<n-m>', help = "RX links to be configured, default is '{DEFAULT_RX_LINKS}'".format(**locals()))
parser.add_argument('--tx-links', default = DEFAULT_TX_LINKS, metavar = '<n-m>', help = "TX links to be configured, default is '{DEFAULT_TX_LINKS}'".format(**locals()))
parser.add_argument('--gtl-latency', default = DEFAULT_GTL_LATENCY, metavar = '<n>', type = int, help = "set latency for GTL logic in BX, default is '{DEFAULT_GTL_LATENCY}'".format(**locals()))
parser.add_argument('--size', default = DEFAULT_SIZE, metavar = '<n>', type = int, help = "number of BX to be compared, default is '{DEFAULT_INPUT_DELAY}'".format(**locals()))
parser.add_argument('--align-to', default = None, metavar = '<n,m>', help = "overwrite link alignment eg. 38,5 (bx, cycle)")
parser.add_argument('--algo-bx-mask', default = None, metavar = '<file>', help = "load algorithm BX mask from file")
parser.add_argument('--ugmt', action = 'store_true', default=False, help ="Enables uGMT inputs.")
parser.add_argument('--configure-amc13', action = 'store_true', help = "Configures the AMC13, first sets TTS busy and after configuring uGT to ready.")
parser.add_argument('--loadfw', action = 'store_true', default=False, help="Loads the fw given by --fwversion.")
parser.add_argument('--demux', action = 'store_true', default=False, help="Enables demux inputs.")
parser.add_argument('--extcond', action = 'store_true', default=False, help="Enables extcond inputs.")
parser.add_argument('--algo-latency', default = DEFAULT_ALGO_LATENCY, metavar = '<n>', type = int, help = "algo latency in frames (240MHz cycles), default is '{DEFAULT_ALGO_LATENCY}'".format(**locals()))
parser.add_argument('--master-latency', default = DEFAULT_MASTER_LATENCY, metavar = '<n>', type = int, help = "master latency in frames (240MHz cycles), default is '{DEFAULT_MASTER_LATENCY}'".format(**locals()))
parser.add_argument('--fedID', type=int, default=DEFAULT_FED_ID, metavar = '<n>', help="Enter your FED ID. Default is '{DEFAULT_FED_ID}'".format(**locals()))
parser.add_argument('--slot', nargs='+', default=DEFAULT_SLOTS, metavar = '<n>', help="Slots to activate in crate. Default is '{DEFAULT_SLOTS}'".format(**locals()))
parser.add_argument('--BCNoffset', type=int, default=(0xdec-23), metavar = '<n>', help='Bunch crossing to expect BC0 in.')
parser.add_argument('--enableSlink', action='store_true', help='Flag to enable the Slink to DAQ.')
parser.add_argument('--configure-tcds', action = 'store_true', help = "Configures the TCDS (pi,iCi) for cpm at the beginning.")
parser.add_argument('--spy', action = 'store_true', help = "Activates the spy function of the AMC13.")
parser.add_argument('--connections-file-amc13', type=str, default='/nfshome0/ugtts/software/tdf/etc/uhal/connections_p5_pro.xml', metavar = '<file>', help='path to amc13 connection file.')
parser.add_argument('--readout-menu', type=str, default='/nfshome0/ugtts/software/mp7sw_v2_0_1/mp7/tests/python/daq/simple.py', metavar = '<file>',help='path to readout menu file.')
parser.add_argument('--fwversion', type=str, default='gt_mp7_xe_v103e_module_0.bit', metavar = '<sdcard file>', help='firmware version which is loaded before the run.')
#parser.add_argument('-o', '--output-dir', default = result_area(), help = "name of output directory")
parser.add_argument('--cap', default = DEFAULT_CAP, metavar = '<n>', type = int, help = "delay in BX for capturing the tx buffer output, default is '{DEFAULT_CAP}'".format(**locals()))
args = parser.parse_args(TDF_ARGS)

args.pattern = os.path.abspath(args.pattern)

global slots, fedID, BCNoffset, EnableSlink

slots = args.slot
fedID = args.fedID
BCNoffset = args.BCNoffset
EnableSlink = args.enableSlink

def status(amc13, state):
    print "Current state according to script: " + state
    amc13.status()

def reset(amc13):
    amc13.reset()
    return "Halted"

def configureTTC(amc13, state):
    if state == "Halted":
        amc13.configureTTC()
        return "Halted"
    else:
        print "Error: Board not halted. Reset it first."

def configure(amc13, state):
    if state == "Halted":
        if EnableSlink == True:
            print "Enabling Slink."
            enableSlink = 1
        else:
            print "Slink disabled."
            enableSlink = 0
        print "Using " + str(BCNoffset) + " as BCNoffset."
        amc13.configure(slots, fedID, enableSlink, bcnOffset=BCNoffset)
        return "Configured"
    else:
        print "Error: Board not halted. Reset it first."

def start(amc13, state):
    if state == "Configured":
        amc13.start()
        return "Running"
    else:
        print "Error: Board not configured. Configure it first."

def stop(amc13, state):
    if state == "Running":
        print "Currently non-funcitonal. Use reset"
        return "Stopped"
        amc13.stop()
        return "Stopped"
    else:
        print "Error: Board not running."

def spy(amc13, state):
    if state != "Running":
        print "WARNING: Seems like we're not running, you probably won't see any events here."
    print "Spying on events. Use ctrl+c to stop."
    amc13.spy()

#if not os.path.isdir(args.output_dir):
    #print "creating result area directory:", args.output_dir
    #os.makedirs(args.output_dir)
    #os.chdir(args.output_dir)

if args.configure_tcds:
    print''
    print'Setup TCDS...'
    os.system("python /nfshome0/ugtts/software/tcds/setup-tcds.py")
    print''

if args.configure_amc13:
    state = "Undefined"

    # Sanitise the connection string
    conns = args.connections_file_amc13.split(';')
    for i,c in enumerate(conns):
        if re.match('^\w+://.*', c) is None:
            conns[i] = 'file://'+c

    print 'Using file',conns
    cm = uhal.ConnectionManager(';'.join(conns))

    amc13T1 = cm.getDevice('T1')
    amc13T2 = cm.getDevice('T2')

    amc13 = dtm.DTManager(t1=amc13T1, t2=amc13T2)

    # Reset AMC13 and set to 'Halted'
    print'Resetting AMC13...'
    state = reset(amc13)
    # Configure AMC13, clock, etc...
    #print'Configure AMC13...'
    #state = configure(amc13, state)

# Reconfigure uGT FPGA
if args.loadfw:
    mp7butler("rebootfpga", args.device1, args.fwversion)
    mp7butler("rebootfpga", args.device2, args.fwversion)

# Reset link's logic
mp7butler("reset", args.device1, "--clksrc", args.clksrc, "--clkcfg", "default-ext")
mp7butler("reset", args.device2, "--clksrc", args.clksrc, "--clkcfg", "default-ext")

# Wait for uGMT/Layer2 etc to be configured.
print ''
raw_input('Please configure now layer2 and/or uGMT. If layer2/uGMT is configured, press Return to continue!')
print ''

# Run unittests to RESET and verify integrity.
#if args.run_unittests:
    #os.makedirs(args.output_dir)
    #os.chdir(args.output_dir)

# Setup for loopback or cable mode.
if args.loopback:
    mp7butler("txmgts", args.device1, "--loopback", "--e", args.rx_links, "--pattern", "std")
    mp7butler("rxmgts", args.device1, "--e", args.rx_links)
    mp7butler("rxalign", args.device1, "--e", args.rx_links, "--to-bx", args.align_to or "8,4")
    mp7butler("txmgts", args.device2, "--loopback", "--e", args.rx_links, "--pattern", "std")
    mp7butler("rxmgts", args.device2, "--e", args.rx_links)
    mp7butler("rxalign", args.device2, "--e", args.rx_links, "--to-bx", args.align_to or "8,4")
else:
    if args.align_to:
        mp7butler("rxmgts", args.device1, "--e", args.rx_links)
	mp7butler("txmgts", args.device1, "--e", args.rx_links)
        mp7butler("rxalign", args.device1, "--e", args.rx_links, "--to-bx", args.align_to)
        mp7butler("rxmgts", args.device2, "--e", args.rx_links)
	mp7butler("txmgts", args.device2, "--e", args.rx_links)
        mp7butler("rxalign", args.device2, "--e", args.rx_links, "--to-bx", args.align_to)
    else:
        #mp7butler("mgts", args.device1, "--e", args.rx_links, "--align-to", "3531,5")
        mp7butler("rxmgts", args.device1, "--e", args.rx_links)
        mp7butler("txmgts", args.device1, "--e", args.rx_links)
        #mp7butler("rxalign", args.device1, "--e", "0-3", "--to-bx", "3558,5")
 	#mp7butler("rxalign", args.device1, "--e", "4-10", "--to-bx", "3534,5")
        mp7butler("rxalign", args.device1, "--e", "args.rx_links")
        #mp7butler("mgts", args.device1, "--e", "12-15", "--align-to", "3534,5") # for the Ext Cond inputs
        mp7butler("rxmgts", args.device2, "--e", args.rx_links)
        mp7butler("txmgts", args.device2, "--e", args.rx_links)
        mp7butler("rxalign", args.device2, "--e", "args.rx_links")


# Setup for loopback or cable mode.
if args.loopback:
    data_filename = TDF_NAME + "_in.dat" # Returns "tagged" filename tdf_simple_buffer_loopback_in.dat
    buffgen(args.pattern, board = args.device1, outfile = data_filename)
    buffgen(args.pattern, board = args.device2, outfile = data_filename)

#if args.loopback:
    #mp7butler("buffers", args.device1, "loopPlay", "--e", args.rx_links, "--inject", "file://{data_filename}".format(**locals()))
#else:
    #mp7butler("buffers", args.device1, "loopPlay")

#if args.capture_buffers:
    #mp7butler("buffers", args.device1, "captureRxTxStb")   # buffer setting
    #mp7butler("capture", args.device1)                  # buffer capture

run_routine("setup_ugt_triggers", args.device1)
run_routine("setup_ugt_triggers", args.device2)

# Setup GTL algorithm masks.
if args.algo_bx_mask:
    run_routine("load_bx_masks", args.device1, args.algo_bx_mask)
    run_routine("load_bx_masks", args.device2, args.algo_bx_mask)
else:
    run_routine("enable_algo_bx_mem", args.device1)
    run_routine("enable_algo_bx_mem", args.device2)

mp7butler("easylatency", args.device1, "--rx", "0-15", "--tx", args.tx_links, "--algoLatency", args.algo_latency, "--masterLatency", args.master_latency)
mp7butler("rosetup", args.device1, "--bxoffset", "2")
mp7butler("romenu", args.device1, args.readout_menu, "menuUGTA")
mp7butler("easylatency", args.device2, "--rx", "0-15", "--tx", args.tx_links, "--algoLatency", args.algo_latency, "--masterLatency", args.master_latency)
mp7butler("rosetup", args.device2, "--bxoffset", "2")
mp7butler("romenu", args.device2, args.readout_menu, "menuUGTA")

if not args.ugmt:
    mp7butler("buffers", args.device1, "algoPlay", "--e", "0-3",   "--inject", "generate://empty") #to mask all the uGMT inputs
    mp7butler("buffers", args.device2, "algoPlay", "--e", "0-3",   "--inject", "generate://empty") #to mask all the uGMT inputs
if not args.demux:
    mp7butler("buffers", args.device1, "algoPlay", "--e", "4-10",   "--inject", "generate://empty") #to mask all the demux inputs
    mp7butler("buffers", args.device2, "algoPlay", "--e", "4-10",   "--inject", "generate://empty") #to mask all the demux inputs
if not args.extcond:
    mp7butler("buffers", args.device1, "algoPlay", "--e", "11-15",   "--inject", "generate://empty") #to mask all the AMC502 inputs
    mp7butler("buffers", args.device2, "algoPlay", "--e", "11-15",   "--inject", "generate://empty") #to mask all the AMC502 inputs

# Wait for the run to be started.
#print ''
#raw_input('Now start the run. Then press Return to continue!')
#print ''

# Configure AMC13 and start run.
if args.configure_amc13:
    #state = reset(amc13)
    #state = configureTTC(amc13, state)
    state = configure(amc13, state)
    state = start(amc13, state)
    print''
    print 'Configure complete...'
    print ''

if args.spy:
    conns = args.connections_file_amc13.split(';')
    for i,c in enumerate(conns):
        if re.match('^\w+://.*', c) is None:
            conns[i] = 'file://'+c

    print 'Using file',conns
    cm = uhal.ConnectionManager(';'.join(conns))

    amc13T1 = cm.getDevice('T1')
    amc13T2 = cm.getDevice('T2')

    amc13 = dtm.DTManager(t1=amc13T1, t2=amc13T2)

    state = "Running"
    spy(amc13, state)

# Dump the memories.
dump(args.device1, "gt_mp7_frame.simspymem", outfile = TDF_NAME + "_simspymem.dat")
algo_dump = dump(args.device1, "gt_mp7_frame.spymem2_algos", outfile = TDF_NAME + "_spymem2_algos.dat")
dump(args.device1, "gt_mp7_frame.spymem2_finor", outfile = TDF_NAME + "_spymem2_finor.dat")
dump(args.device2, "gt_mp7_frame.simspymem", outfile = TDF_NAME + "_simspymem.dat")
algo_dump = dump(args.device2, "gt_mp7_frame.spymem2_algos", outfile = TDF_NAME + "_spymem2_algos.dat")
dump(args.device2, "gt_mp7_frame.spymem2_finor", outfile = TDF_NAME + "_spymem2_finor.dat")

#if args.loopback:
    #if args.pattern not in (':counter', ':zero'):
    ## Compare the dumps.
        #compare(args.device1, "gt_mp7_frame.simspymem", TDF_NAME + "_simspymem.dat", args.pattern, offset = args.delay, size = args.size)
        #compare(args.device1, "gt_mp7_frame.spymem2_algos", TDF_NAME + "_spymem2_algos.dat", args.pattern, offset = args.delay + args.gtl_latency, size = args.size)
        #compare(args.device1, "gt_mp7_frame.spymem2_finor", TDF_NAME + "_spymem2_finor.dat", args.pattern, offset = args.delay + args.gtl_latency, size = args.size)
        #compare(args.device2, "gt_mp7_frame.simspymem", TDF_NAME + "_simspymem.dat", args.pattern, offset = args.delay, size = args.size)
        #compare(args.device2, "gt_mp7_frame.spymem2_algos", TDF_NAME + "_spymem2_algos.dat", args.pattern, offset = args.delay + args.gtl_latency, size = args.size)
        #compare(args.device2, "gt_mp7_frame.spymem2_finor", TDF_NAME + "_spymem2_finor.dat", args.pattern, offset = args.delay + args.gtl_latency, size = args.size)

    ## Read in test vector.
    #tv = TestVector(open(args.pattern))

    ## Overall delay.
    #delay_all = args.delay + args.gtl_latency

    ## Read the emulator log file if available (for active algorithms and names).
    #logfile = args.pattern.replace(".txt", ".log")
    #if os.path.isfile(logfile):
        #lines = open(logfile).readlines()
        #for i in range(len(lines)):
            #if lines[i].strip() == "=========== Summary of results ==========":
                #print lines[i].strip()
                #print "bit\tL1A/tv\tL1A/hw\tresult\tname\t(tv=testvector, hw=hardware readout)"
                #for line in lines[i:]:
                    #result = re.match("^\s+(\d+)\s+(\d+)\s+(L1_[a-zA-Z0-9_]+)", line)
                    #if result:
                        #bit, l1a, name = result.groups()
                        #index = int(bit)
                        #l1a_hw = 0
                        #for algorithm in algo_dump.algorithms()[delay_all:delay_all+args.size]:
                            #l1a_hw += (algorithm >> index) & 0x1
                        #l1a_tv = 0
                        #for algorithm in tv.algorithms()[:args.size]:
                            #l1a_tv += (algorithm >> index) & 0x1
                        #result = "OK" if l1a_tv == l1a_hw else "ERROR"
                        #print "{bit}\t{l1a_tv}\t{l1a_hw}\t{result}\t{name}".format(**locals())
                #break

# Dumping TX buffer content
#if args.loopback:
#    mp7butler("buffers", args.device1, "captureTx", "--e",  args.tx_links, "--cap", args.cap)
#    mp7butler("capture", args.device1, "--e", args.tx_links, "--outputpath", "tx_buffer_dump")
