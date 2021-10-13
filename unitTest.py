from dt01 import *
import sys
import logging

logger = logging.getLogger('DT01')
formatter = logging.Formatter('{"debug": %(asctime)s {%(pathname)s:%(lineno)d} %(message)s}')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(1)

logger.debug("Instantiating DT01")
polyphony =2 
dt01_inst = DT01(polyphony = polyphony)
logger.debug("Initializing")
dt01_inst.initialize()
logger.debug("Applying a light touch")
dt01_inst.voices[0].operators[0].send("cmd_env", 2**16)

if "t" in sys.argv:
	dt01_inst.voices[0].operators[6].send("cmd_env", 2**14)
	
if "v" in sys.argv:
	dt01_inst.voices[0].operators[7].send("cmd_env", 2**14)
	
if "p" in sys.argv:
	dt01_inst.fpga_interface_inst.gather(polyphony)
	dt01_inst.voices[0].operators[0].send("cmd_env", 2**16)
	dt01_inst.voices[1].operators[0].send("cmd_env", 2**16)
	dt01_inst.voices[0].send("cmd_baseincrement", 2**12)
	dt01_inst.voices[1].send("cmd_baseincrement", 2**12*3/2)
	dt01_inst.fpga_interface_inst.release()