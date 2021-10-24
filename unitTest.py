import dt01
import sys
import logging
import os

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
	dt01_inst = dt01.DT01_fromFile(filename)
	logger.debug("finished reading")
else:
	logger.debug("initializing from scratch")
	dt01_inst = dt01.DT01(polyphony = polyphony)
	logger.debug("saving to file")
	dt01_inst.toFile(filename)
	
logger.debug("Initializing")
dt01_inst.initialize()
logger.debug("Applying a light touch")

# TODO:
# fix vibrato
# implement actual envelopes

if "t" in sys.argv:
	dt01_inst.voices[0].operators[6].send(dt01.cmd_env, 2**14)
	dt01_inst.voices[0].operators[6].send(dt01.cmd_increment, 2**11)
	dt01_inst.voices[0].operators[0].send(dt01.cmd_env, 2**16)
	dt01_inst.voices[0].operators[0].send(dt01.cmd_increment, 2**23)
	
if "v" in sys.argv:
	dt01_inst.voices[0].send(dt01.cmd_increment, 2**27)
	dt01_inst.voices[0].operators[0].send(dt01.cmd_env, 2**16)
	dt01_inst.voices[0].operators[7].send(dt01.cmd_env, 2**7)
	
if "fb" in sys.argv:
	dt01_inst.voices[0].send(dt01.cmd_increment, 2**27)
	dt01_inst.voices[0].send(dt01.cmd_fm_algo, 0o77777770)
	dt01_inst.voices[0].send(dt01.cmd_fbsrc, 0)
	dt01_inst.voices[0].send(dt01.cmd_fbgain, 2**5)
	dt01_inst.voices[0].operators[0].send(dt01.cmd_env, 2**16)

if "test" in sys.argv:
	for i in range(1024):
		dt01_inst.voices[0].operators[0].send(dt01.cmd_env, 2**16)

if "f" in sys.argv:
	dt01_inst.voices[0].send(dt01.cmd_increment,2**27)
	dt01_inst.voices[0].operators[0].send(dt01.cmd_env, 2**16)
	dt01_inst.voices[0].operators[1].send(dt01.cmd_env, 2**12)
	dt01_inst.voices[0].operators[2].send(dt01.cmd_env, 2**12)
	dt01_inst.voices[0].operators[3].send(dt01.cmd_env, 2**12)
	dt01_inst.voices[0].operators[4].send(dt01.cmd_env, 2**7)
	dt01_inst.voices[0].operators[5].send(dt01.cmd_env, 2**14)
	dt01_inst.voices[0].operators[6].send(dt01.cmd_env, 2**16)
	dt01_inst.voices[0].send(dt01.cmd_fm_algo, 0o77754321)
	
if "p" in sys.argv:
	dt01_inst.fpga_interface_inst.gather()
	dt01_inst.voices[0].operators[0].send(dt01.cmd_env, 2**16)
	dt01_inst.voices[1].operators[0].send(dt01.cmd_env, 2**16)
	dt01_inst.voices[0].send(dt01.cmd_increment, 2**13)
	dt01_inst.voices[1].send(dt01.cmd_increment, 2**13*3/2)
	dt01_inst.fpga_interface_inst.release()
