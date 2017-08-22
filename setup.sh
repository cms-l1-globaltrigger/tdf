#!/bin/bash
#
# Copyright 2013-2017 Bernhard Arnold <bernahrd.arnold@cern.ch>
#                     Johannes Wittmann <johannes.wittmann@cern.ch>
#
# Repository path   : $HeadURL: $
# Last committed    : $Revision: $
# Last changed by   : $Author: $
# Last changed date : $Date: $
#

export TDF_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH=$PYTHONPATH:$TDF_ROOT
export PATH=$TDF_ROOT/bin:$PATH

# Print paths for debug purposes.
echo TDF_ROOT: $TDF_ROOT
echo PYTHONPATH: $PYTHONPATH
echo PATH: $PATH

# Source argcompletion
if [ -f $TDF_ROOT/completion.sh ]; then
    . $TDF_ROOT/completion.sh
fi
