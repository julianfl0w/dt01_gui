from dt01 import *
import sys
import logging

logger = logging.getLogger('DT01')
formatter = logging.Formatter('{%(pathname)s:%(lineno)d %(message)s}')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(1)

logger.debug("Instantiating DT01")
polyphony = 512
filename = "dt01_" + str(int(polyphony)) + ".pkl"

if os.path.exists(filename):
	logger.debug("reading from file")
	dt01_inst = DT01_fromFile(filename)
	logger.debug("finished reading")
else:
	logger.debug("initializing from scratch")
	dt01_inst = DT01(polyphony = polyphony)
	logger.debug("saving to file")
	dt01_inst.toFile(filename)
	
logger.debug("Initializing")
dt01_inst.initialize()
logger.debug("Applying a light touch")

# TODO:
# fix vibrato
# implement actual envelopes

if "t" in sys.argv:
	dt01_inst.voices[0].operators[6].send("cmd_env", 2**14)
	dt01_inst.voices[0].operators[0].send("cmd_env", 2**16)
	
if "v" in sys.argv:
	dt01_inst.voices[0].operators[7].send("cmd_env", 2**14)
	dt01_inst.voices[0].operators[0].send("cmd_env", 2**16)
	
if "fb" in sys.argv:
	dt01_inst.voices[0].send("cmd_baseincrement", 2**15)
	dt01_inst.voices[0].send("cmd_fbsrc", 0)
	dt01_inst.voices[0].send("cmd_fbgain", 2**16)
	dt01_inst.voices[0].operators[0].send("cmd_env", 2**16)


if "f" in sys.argv:
	dt01_inst.voices[0].send("cmd_baseincrement", 2**15)
	dt01_inst.voices[0].operators[0].send("cmd_env", 2**16)
	dt01_inst.voices[0].operators[1].send("cmd_env", 2**12)
	dt01_inst.voices[0].operators[2].send("cmd_env", 2**12)
	dt01_inst.voices[0].operators[3].send("cmd_env", 2**12)
	dt01_inst.voices[0].operators[4].send("cmd_env", 2**7)
	dt01_inst.voices[0].operators[5].send("cmd_env", 2**14)
	dt01_inst.voices[0].operators[6].send("cmd_env", 2**16)
	dt01_inst.voices[0].send("cmd_fm_algo", 0o77754321)
	
if "p" in sys.argv:
	dt01_inst.fpga_interface_inst.gather()
	dt01_inst.voices[0].operators[0].send("cmd_env", 2**16)
	dt01_inst.voices[1].operators[0].send("cmd_env", 2**16)
	dt01_inst.voices[0].send("cmd_baseincrement", 2**13)
	dt01_inst.voices[1].send("cmd_baseincrement", 2**13*3/2)
	dt01_inst.fpga_interface_inst.release()
