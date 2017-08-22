from tdf.extern import argparse
import os
import time

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--modules', action = 'store', metavar = '1-6:1-6', help = 'test between modules n:n', type = str)
    return parser.parse_args(TDF_ARGS)

# the ammount of bits used
bit_count = 8
args = parse()

# variable for the final output
err = False
min_module = 1
max_module = 6
from_module = 0
to_module = 6

# sets the new range in the for loops
if args.modules:
    # checks if the argument is only 3 characters long
    if len(args.modules) != 3:
        raise Exception('Argument for --module is invalid! Try using a value between 1-6 then ":" and then another value between 1-6.')
    # checks if the first number is valid
    if not ((int(args.modules[0]) <= max_module) and (int(args.modules[0]) >= min_module)):
        raise Exception('Argument for --module is invalid! Try using a value between 1-6 then a : and then another value between 1-6.')
    # checks if the second number is valid
    if not ((int(args.modules[2]) <= max_module) and (int(args.modules[2]) >= min_module)):
        raise Exception('Argument for --module is invalid! Try using a value between 1-6 then a : and then another value between 1-6.')
    # checks if the smaller number is at the start and the bigger number at the end
    if int(args.modules[0]) > int(args.modules[2]):
        raise Exception('Argument for --module is invalid! Try to keep the smaller number at the start and the bigger number at the end.')
    from_module = int(args.modules[0]) - 1
    to_module = int(args.modules[2])

# finalOR card
finor_module = 'finor_amc502.7'
# finalOR pre card
finor_pre_module = 'finor_pre_amc502.8'

# the different cards installed
devices = {
    0: 'gt_mp7.1',
    1: 'gt_mp7.2',
    2: 'gt_mp7.3',
    3: 'gt_mp7.4',
    4: 'gt_mp7.5',
    5: 'gt_mp7.6',
}

# the different cables and names
cables = {
    0: 'finOR cable',
    1: 'veto cable',
    2: 'finOR preview cable',
}

# sets the output of the finOR modules to 1
for module in range(from_module, to_module):
    write(finor_module, 'payload.input_masks.module_{}'.format(module), '1')
    write(finor_pre_module, 'payload.input_masks.module_{}'.format(module), '1')

output = ''
algo_dumps = {}
# used for the bits witch triggert on the finOR card
bit_help = ['01', '02', '04', '08', '10', '20']

# prepares cards and cables for output and sets them to 0
for module_index in range(from_module, to_module):
    for cable in range(3):
        write(devices[module_index], 'gt_mp7_tp_mux.tp_mux.out{}'.format(cable), '0x14')
        write(devices[module_index], 'gt_mp7_tp_mux.test_out{}'.format(cable), '0')

for module_index in range(from_module, to_module):
    for cable in range(3):
        # set one cable output to 1
        write(devices[module_index], 'gt_mp7_tp_mux.test_out{}'.format(cable), '1')
        time.sleep(0.1)
        # if the current cable is on the finOR pre module
        if cable == 2:
            # use the finOr pre card for the output
            write(finor_pre_module, 'payload.spy12_next_event', '1')
            algo_dumps[cable] = dump(finor_pre_module, 'payload.spymem')
        else:    #use the finOR module
            write(finor_module, 'payload.spy12_next_event', '1')
            algo_dumps[cable] = dump(finor_module, 'payload.spymem')
        # the variable output gets the value of the dump in line 10 and converts it into 0x and then into a string
        output = str(hex(algo_dumps[cable].finor()[10]))

        time.sleep(0.1)
        out_len = len(output)
        # here bit_h gets the int value of bit_help[moudle_index] eg. when the module number is 3 it gets 04 back and converts it to an int (4)
        bit_h = int(bit_help[module_index])
        # here the output message is made
        if cable == 1:
            should_out = '0x{}00'.format(int(bit_help[module_index])) # eg for module 1 it is 0x100
        elif cable == 0 or cable == 2:
            should_out = '0x100{}'.format(bit_help[module_index]) # eg 0x10001

        # if the output length is three is looks like this 0x0 then the cable isnt conneceted or no signal was sent
        if out_len == 3:
            err = True
            print 'error at module: {}'.format(devices[module_index])
            print '         cable : {}'.format(cables[cable])
            print 'cable not connected'
        # if the output length is 5 it looks like this 0x100 that means it can only come form the first 4 modules and is the veto cable
        elif out_len == 5:
            if int(output[2:3]) != bit_h and cable == 1:
                err = True
                print 'error at module: {}'.format(devices[module_index])
                print '         cable : {}'.format(cables[cable])
                print 'bit should be: {}    bits are: {}'.format(should_out, output)
        # if the output length is 6 it looks like ths 0x1000 that means it can only come form the last 2 module and is the veto cable
        elif out_len == 6:
            if int(output[2:4]) != bit_h and cable == 1:
                err = True
                print 'error at module: {}'.format(devices[module_index])
                print '         cable : {}'.format(cables[cable])
                print 'bit should be: {}    bits are: {}'.format(should_out, output)
        # if the length is 7 is looks like this 0x10001 that means it is either the finOR cable or the finOR pre cable
        elif out_len == 7:
            if int(output[5:]) != bit_h and cable != 1:
                err = True
                print 'error at module: {}'.format(devices[module_index])
                print '         cable : {}'.format(cables[cable])
                print 'bit should be: {}    bits are: {}'.format(should_out, output)
        write(devices[module_index], 'gt_mp7_tp_mux.test_out{}'.format(cable), '0')

print 'all cables checked'

# if any error was found err is true
if err:
    print 'Errors found!'
else:
    print 'no errors found'
