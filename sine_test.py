
from dt01 import dt01
HWIDTH = 1 

import struct
import sys

	
	
dt01_inst = dt01()
mm_noteno = 0

dt01_inst.send("cmd_mastergain_right", 0, 0, 2**16) 
dt01_inst.send("cmd_mastergain_left" , 0, 1, 2**16)

# Gain
dt01_inst.send("cmd_gain_porta", 0, mm_noteno, 2**16)
dt01_inst.send("cmd_gain"      , 0, mm_noteno, 2**16)

# Frequency
dt01_inst.send("cmd_increment_porta", 0, mm_noteno, 2**30)
dt01_inst.send("cmd_increment"      , 0, mm_noteno, 123956524) # 32 bit incrementer 
 
# turn off flush
dt01_inst.send("cmd_flushspi", 0, 0, 0)
dt01_inst.send("cmd_passthrough", 0, 0, 0)

#while(1):
#	dt01_inst.send(cmd_flushspi, 0, 0, 1)) 
	