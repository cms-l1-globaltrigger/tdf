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
DEFAULT_RX_LINKS = '4-10'
DEFAULT_TX_LINKS = '16-24'
DEFAULT_CAP = 0
DEFAULT_HW_DELAY = 0
DEFAULT_FED_ID = 1404
DEFAULT_SLOT = 1
DEFAULT_ALGO_LATENCY = 44
DEFAULT_MASTER_LATENCY = 187

def result_area():
    from datetime import datetime
    dirname = "{0}_{1}".format(TDF_NAME, datetime.strftime(datetime.now(), "%Y-%m-%dT%H-%M-%S"))
    return dirname

parser = argparse.ArgumentParser()
parser.add_argument('device', default = 'gt_mp7.1', help = "device defined in connections file")
parser.add_argument('--loopback', action = 'store_true', help = "run internal loopback mode (without cable)")
parser.add_argument('--pattern', default = ':counter', metavar = '<source>', help = "source test vector to be loaded into the TX buffers (or ':counter' for generic counter, default)")
parser.add_argument('--delay', default = DEFAULT_INPUT_DELAY, metavar = '<n>', type = int, help = "delay in BX for incomming data in spy memory, default is '{DEFAULT_INPUT_DELAY}'".format(**locals()))
parser.add_argument('--hw-delay', default = DEFAULT_HW_DELAY, metavar = '<n>', type = int, help = "delay in BX for incomming data, default is '{DEFAULT_HW_DELAY}'".format(**locals()))
parser.add_argument('--clksrc', choices = ("external", "internal"), default = "external", help = "clock source, default is 'external'")
parser.add_argument('--rx-links', '--links', default = DEFAULT_RX_LINKS, metavar = '<n-m>', help = "RX links to be configured, default is '{DEFAULT_RX_LINKS}'".format(**locals()))
parser.add_argument('--tx-links', default = DEFAULT_TX_LINKS, metavar = '<n-m>', help = "TX links to be configured, default is '{DEFAULT_TX_LINKS}'".format(**locals()))
parser.add_argument('--gtl-latency', default = DEFAULT_GTL_LATENCY, metavar = '<n>', type = int, help = "set latency for GTL logic in BX, default is '{DEFAULT_GTL_LATENCY}'".format(**locals()))
parser.add_argument('--size', default = DEFAULT_SIZE, metavar = '<n>', type = int, help = "number of BX to be compared, default is '{DEFAULT_INPUT_DELAY}'".format(**locals()))
parser.add_argument('--align-to', default = None, metavar = '<n,m>', help = "overwrite link alignment eg. 38,5 (bx, cycle)")
parser.add_argument('--algo-bx-mask', default = None, metavar = '<file>', help = "load algorithm BX mask from file")
#parser.add_argument('--capture-buffers', action = 'store_true')
parser.add_argument('--configure-amc13', action = 'store_true', help = "Configures the AMC13, first sets TTS busy and after configuring uGT to ready.")
#parser.add_argument('--run-unittests', action = 'store_true')
parser.add_argument('--algo-latency', default = DEFAULT_ALGO_LATENCY, metavar = '<n>', type = int, help = "algo latency in frames (240MHz cycles), default is '{DEFAULT_ALGO_LATENCY}'".format(**locals()))
parser.add_argument('--master-latency', default = DEFAULT_MASTER_LATENCY, metavar = '<n>', type = int, help = "master latency in frames (240MHz cycles), default is '{DEFAULT_MASTER_LATENCY}'".format(**locals()))
parser.add_argument('--fedID', type=int, default=DEFAULT_FED_ID, metavar = '<n>', help="Enter your FED ID. Default is '{DEFAULT_FED_ID}'".format(**locals()))
parser.add_argument('--slot', type=int, default=DEFAULT_SLOT, metavar = '<n>', help="Slot to activate in crate. Default is '{DEFAULT_SLOT}'".format(**locals()))
parser.add_argument('--BCNoffset', type=int, default=(0xdec-23), metavar = '<n>', help='Bunch crossing to expect BC0 in.')
parser.add_argument('--enableSlink', action='store_true', help='Flag to enable the Slink to DAQ.')
parser.add_argument('--configure-tcds', action = 'store_true', help = "Configures the TCDS (pi,iCi) for cpm at the beginning.")
parser.add_argument('--spy', action = 'store_true', help = "Activates the spy function of the AMC13.")
parser.add_argument('--connections-file-amc13', type=str, default='/nfshome0/ugtts/software/tdf/etc/uhal/connections-amc13-p5.xml', metavar = '<file>', help='path to amc13 connection file.')
parser.add_argument('--readout-menu', type=str, default='/nfshome0/ugtts/software/mp7sw_v1_8_5_pre1/mp7/tests/python/daq/simple.py', metavar = '<file>',help='path to readout menu file.')
parser.add_argument('--fwversion', type=str, default='gt_mp7_xe_v103a_module_0.bit', metavar = '<sdcard file>', help='firmware version which is loaded before the run.')
#parser.add_argument('-o', '--output-dir', default = result_area(), help = "name of output directory")
parser.add_argument('--cap', default = DEFAULT_CAP, metavar = '<n>', type = int, help = "delay in BX for capturing the tx buffer output, default is '{DEFAULT_CAP}'".format(**locals()))
args = parser.parse_args(TDF_ARGS)

args.pattern = os.path.abspath(args.pattern)

global slot, fedID, BCNoffset, EnableSlink

slot = args.slot
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
        amc13.configure([slot], fedID, enableSlink, bcnOffset=BCNoffset)
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
    state = reset(amc13)

# Reconfigure uGT FPGA
mp7butler("rebootfpga", args.device, args.fwversion)

# Reset link's logic
mp7butler("reset", args.device, "--clksrc", args.clksrc)

# Wait for Layer2/Layer2 etc to be configured.
print ''
raw_input('Please configure now layer2. If layer2 is configured, press Return to continue!')
print ''

# Run unittests to RESET and verify integrity.
#if args.run_unittests:
    #os.makedirs(args.output_dir)
    #os.chdir(args.output_dir)

# Setup for loopback or cable mode.
if args.loopback:
    mp7butler("mgts", args.device, "--loopback", "--e", args.rx_links, "--align-to", args.align_to or "8,5")
else:
    if args.align_to:
        mp7butler("mgts", args.device, "--e", args.rx_links, "--align-to", args.align_to)
    else:
        mp7butler("mgts", args.device, "--e", args.rx_links, "--align-to", "3531,5")
        
mp7butler("buffers", args.device, "algoPlay", "-e", "0-3",   "--inject", "generate://empty") #to mask all the uGMT inputs
mp7butler("buffers", args.device, "algoPlay", "-e", "12-15",   "--inject", "generate://empty") #to mask all the AMC502 inputs
 
# Setup for loopback or cable mode.
if args.loopback:
    data_filename = TDF_NAME + "_in.dat" # Returns "tagged" filename tdf_simple_buffer_loopback_in.dat
    buffgen(args.pattern, board = args.device, outfile = data_filename)

#if args.loopback:
    #mp7butler("buffers", args.device, "loopPlay", "--e", args.rx_links, "--inject", "file://{data_filename}".format(**locals()))
#else:
    #mp7butler("buffers", args.device, "loopPlay")

#if args.capture_buffers:
    #mp7butler("buffers", args.device, "captureRxTxStb")   # buffer setting
    #mp7butler("capture", args.device)                  # buffer capture

run_routine("setup_ugt_triggers", args.device)

if args.hw_delay:
    write(args.device, "gt_mp7_frame.rb.dm.delay_muons", args.hw_delay)
    write(args.device, "gt_mp7_frame.rb.dm.delay_eg", args.hw_delay)
    write(args.device, "gt_mp7_frame.rb.dm.delay_tau", args.hw_delay)
    write(args.device, "gt_mp7_frame.rb.dm.delay_jet", args.hw_delay)
    write(args.device, "gt_mp7_frame.rb.dm.delay_ett", args.hw_delay)
    write(args.device, "gt_mp7_frame.rb.dm.delay_ht", args.hw_delay)
    write(args.device, "gt_mp7_frame.rb.dm.delay_etm", args.hw_delay)
    write(args.device, "gt_mp7_frame.rb.dm.delay_htm", args.hw_delay)
    write(args.device, "gt_mp7_frame.rb.dm.delay_ext_con", args.hw_delay)
    
# Setup GTL algorithm masks.
if args.algo_bx_mask:
    run_routine("load_bx_masks", args.device, args.algo_bx_mask)
else:
    run_routine("enable_algo_bx_mem", args.device)
    
mp7butler("easylatency", args.device, "--rx", "0-15", "--tx", args.tx_links, "--algoLatency", args.algo_latency, "--masterLatency", args.master_latency)
mp7butler("rosetup", args.device, "--bxoffset", "2")
mp7butler("romenu", args.device, args.readout_menu, "menuUGTA")

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
        spy(amc13, state)
    
# Dump the memories.
#dump(args.device, "gt_mp7_frame.simspymem", outfile = TDF_NAME + "_simspymem.dat")
#algo_dump = dump(args.device, "gt_mp7_frame.spymem2_algos", outfile = TDF_NAME + "_spymem2_algos.dat")
#dump(args.device, "gt_mp7_frame.spymem2_finor", outfile = TDF_NAME + "_spymem2_finor.dat")

if args.loopback:
    if args.pattern not in (':counter', ':zero'):
    # Compare the dumps.
        compare(args.device, "gt_mp7_frame.simspymem", TDF_NAME + "_simspymem.dat", args.pattern, offset = args.delay, size = args.size)
        compare(args.device, "gt_mp7_frame.spymem2_algos", TDF_NAME + "_spymem2_algos.dat", args.pattern, offset = args.delay + args.gtl_latency, size = args.size)
        compare(args.device, "gt_mp7_frame.spymem2_finor", TDF_NAME + "_spymem2_finor.dat", args.pattern, offset = args.delay + args.gtl_latency, size = args.size)

    # Read in test vector.
    tv = TestVector(open(args.pattern))

    # Overall delay.
    delay_all = args.delay + args.gtl_latency

    # Read the emulator log file if available (for active algorithms and names).
    logfile = args.pattern.replace(".txt", ".log")
    if os.path.isfile(logfile):
        lines = open(logfile).readlines()
        for i in range(len(lines)):
            if lines[i].strip() == "=========== Summary of results ==========":
                print lines[i].strip()
                print "bit\tL1A/tv\tL1A/hw\tresult\tname\t(tv=testvector, hw=hardware readout)"
                for line in lines[i:]:
                    result = re.match("^\s+(\d+)\s+(\d+)\s+(L1_[a-zA-Z0-9_]+)", line)
                    if result:
                        bit, l1a, name = result.groups()
                        index = int(bit)
                        l1a_hw = 0
                        for algorithm in algo_dump.algorithms()[delay_all:delay_all+args.size]:
                            l1a_hw += (algorithm >> index) & 0x1
                        l1a_tv = 0
                        for algorithm in tv.algorithms()[:args.size]:
                            l1a_tv += (algorithm >> index) & 0x1
                        result = "OK" if l1a_tv == l1a_hw else "ERROR"
                        print "{bit}\t{l1a_tv}\t{l1a_hw}\t{result}\t{name}".format(**locals())
                break

# Dumping TX buffer content
#if args.loopback:
#    mp7butler("buffers", args.device, "captureTx", "--e",  args.tx_links, "--cap", args.cap)
#    mp7butler("capture", args.device, "--e", args.tx_links, "--outputpath", "tx_buffer_dump")
