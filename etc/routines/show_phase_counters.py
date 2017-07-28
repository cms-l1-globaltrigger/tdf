# show_phase_counters.py
# BA 2015-05-28: created
# dumping phase counters

from tdf.core.xmlmenu import XmlMenu
from tdf.extern import argparse

NR_OF_BITS = 64
NR_OF_SAMPLES = 6

def rotate(strg,n):
    return strg[n:] + strg[:n]

# -----------------------------------------------------------------------------
#  Parse arguments
# -----------------------------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument('device')
args = parser.parse_args(TDF_ARGS)

for bit in range(64):
  # -----------------------------------------------------------------------------
  #  Read current phase value
  # -----------------------------------------------------------------------------
  phaseValue = read(args.device, "payload.phase_shift_regs.phase_shift_{0:02d}".format(bit))

  # -----------------------------------------------------------------------------
  #  Send counter read pulse
  # -----------------------------------------------------------------------------
  write(args.device, "payload.phase_cntr_read_pulse", "1")

  # -----------------------------------------------------------------------------
  #  Read phase counter values
  # -----------------------------------------------------------------------------
  phaseCounterLo = read(args.device, "payload.phase_counter_regs.phase_counter_lo_{0:02d}".format(bit))
  phaseCounterHi = read(args.device, "payload.phase_counter_regs.phase_counter_hi_{0:02d}".format(bit))

  # -----------------------------------------------------------------------------
  #  Split the values to 6 variables
  # -----------------------------------------------------------------------------
  phaseCounter0 = (phaseCounterLo & int('000000ff', 16)) >> 0
  phaseCounter1 = (phaseCounterLo & int('0000ff00', 16)) >> 8
  phaseCounter2 = (phaseCounterLo & int('00ff0000', 16)) >> 16
  phaseCounter3 = (phaseCounterLo & int('ff000000', 16)) >> 24
  phaseCounter4 = (phaseCounterHi & int('000000ff', 16)) >> 0
  phaseCounter5 = (phaseCounterHi & int('0000ff00', 16)) >> 8

  # -----------------------------------------------------------------------------
  #  Generate a string for the table output
  # -----------------------------------------------------------------------------
  showCurrentValue = rotate("*     ", (-1)*phaseValue)

  print ""
  print "Current phase selection for ExtCond bit #{0:02d}: {1}".format(bit, phaseValue)
  print ""
  print "Sampling points:"
  print "| #0 | #1 | #2 | #3 | #4 | #5 |"
  print "| {0:02x} | {1:02x} | {2:02x} | {3:02x} | {4:02x} | {5:02x} |".format(phaseCounter0, phaseCounter1, phaseCounter2, phaseCounter3, phaseCounter4, phaseCounter5)
  print "|  {0} |  {1} |  {2} |  {3} |  {4} |  {5} |".format(showCurrentValue[0], showCurrentValue[1], showCurrentValue[2], showCurrentValue[3], showCurrentValue[4], showCurrentValue[5])
  print ""
  print ""
  print "(* ... current sampling point)"
  print ""
