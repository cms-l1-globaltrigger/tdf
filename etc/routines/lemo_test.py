from tdf.extern import argparse
import os
import time

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--module', action = 'store', choices = range(1, 7), metavar = 'int', help = 'number of modules in use', default = 6)
    return parser.parse_args(TDF_ARGS)

bit_count = 8    #the ammount of bits used
args = parse()
err = False    #variavle for the final output

finor_module = 'finor_amc502.7'    #finalOR card
finor_pre_module = 'finor_pre_amc502.8'    #finalOR pre card

devices = {    #the different card installed
    0: 'gt_mp7.1',
    1: 'gt_mp7.2',
    2: 'gt_mp7.3',
    3: 'gt_mp7.4',
    4: 'gt_mp7.5',
    5: 'gt_mp7.6',
}

cables = {    #the different cables and names
    0: 'finOR cable',
    1: 'veto cable',
    2: 'finOR preview cable',
}

for module in range(args.module):    #sets the output of the finOR modules to 1
    write(finor_module, 'payload.input_masks.module_{}'.format(module), '1')
    write(finor_pre_module, 'payload.input_masks.module_{}'.format(module), '1')

output = ''
algo_dumps = {}
bit_help = ['01', '02', '04', '08', '10', '20']    #used for the bits witch triggert on the finOR card


for module_index in range(args.module):    #prepares cards and cables for output and sets them to 0
    for cable in range(3):
        write(devices[module_index], 'gt_mp7_tp_mux.tp_mux.out{}'.format(cable), '0x14')
        write(devices[module_index], 'gt_mp7_tp_mux.test_out{}'.format(cable), '0')

for module_index in range(args.module):
    for cable in range(3):
        write(devices[module_index], 'gt_mp7_tp_mux.test_out{}'.format(cable), '1')    #set one cable output to 1
        time.sleep(0.1)

        if cable == 2:    #if the current cable is on the finOR pre module
            write(finor_pre_module, 'payload.spy12_next_event', '1')    #use the finOr pre card for the output
            algo_dumps[cable] = dump(finor_pre_module, 'payload.spymem')
        else:    #use the finOR module
            write(finor_module, 'payload.spy12_next_event', '1')
            algo_dumps[cable] = dump(finor_module, 'payload.spymem')
        output = str(hex(algo_dumps[cable].finor()[10]))    #the variable output gets the value of the dump in line 10 and converts it into 0x and then into a string

        time.sleep(0.1)
        out_len = len(output)
        bit_h = int(bit_help[module_index])    #here bit_h gets the int value of bit_help[moudle_index] eg. when the module number is 3 it gets 04 back and converts it to an int (4)

        if cable == 1:#here the output message is made
            should_out = '0x{}00'.format(int(bit_help[module_index]))    #eg for module 1 it is 0x100
        elif cable == 0 or cable == 2:
            should_out = '0x100{}'.format(bit_help[module_index])    #eg 0x10001

        if out_len == 3:    #if the output length is three is looks like this 0x0 then the cable isnt conneceted or no signal was sent
            err = True
            print 'error at module: {}'.format(devices[module_index])
            print '         cable : {}'.format(cables[cable])
            print 'cable not connected'
        elif out_len == 5:    #if the output length is 5 it looks like this 0x100 that means it can only come form the first 4 modules and is the veto cable
            if int(output[2:3]) != bit_h and cable == 1:
                err = True
                print 'error at module: {}'.format(devices[module_index])
                print '         cable : {}'.format(cables[cable])
                print 'bit should be: {}    bits are: {}'.format(should_out, output)
        elif out_len == 6:    #if the output length is 6 it looks like ths 0x1000 that means it can only come form the last 2 module and is the veto cable
            if int(output[2:4]) != bit_h and cable == 1:
                err = True
                print 'error at module: {}'.format(devices[module_index])
                print '         cable : {}'.format(cables[cable])
                print 'bit should be: {}    bits are: {}'.format(should_out, output)
        elif out_len == 7:    #if the length is 7 is looks like this 0x10001 that means it is either the finOR cable or the finOR pre cable
            if int(output[5:]) != bit_h and cable != 1:
                err = True
                print 'error at module: {}'.format(devices[module_index])
                print '         cable : {}'.format(cables[cable])
                print 'bit should be: {}    bits are: {}'.format(should_out, output)
        write(devices[module_index], 'gt_mp7_tp_mux.test_out{}'.format(cable), '0')

print 'all cables checked'

if err:    #if any error was found err is true
    print 'Errors found!'
else:
    print 'no errors found'
