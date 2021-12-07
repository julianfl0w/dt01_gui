import dt01
import sys
import logging
import os
import math
from multiprocessing import Process
import RPi.GPIO as GPIO
import time
#from multiprocessing import shared_memory


logger = logging.getLogger('DT01')
formatter = logging.Formatter('{%(pathname)s:%(lineno)d %(message)s}')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(1)

logger.debug("Instantiating DT01")
polyphony = 512
filename = "dt01_" + str(int(polyphony)) + ".pkl"

logger.debug("initializing")
dt01_inst = dt01.DT01(polyphony = polyphony)

logger.debug("Applying a light touch")

if "t" in sys.argv:
	dt01_inst.voices[0].operators[6].formatAndSend(dt01.cmd_env, 2**14)
	dt01_inst.voices[0].operators[6].formatAndSend(dt01.cmd_increment, 2**11)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env, 2**16)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_increment, 2**23)
	
if "v" in sys.argv:
	dt01_inst.voices[0].formatAndSend(dt01.cmd_increment, 2**27)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env, 2**16)
	dt01_inst.voices[0].operators[7].formatAndSend(dt01.cmd_env, 2**7)
	
if "fb" in sys.argv:
	dt01_inst.voices[0].formatAndSend(dt01.cmd_increment, 2**27)
	dt01_inst.voices[0].formatAndSend(dt01.cmd_fm_algo, 0o77777770)
	dt01_inst.voices[0].formatAndSend(dt01.cmd_fbsrc, 0)
	dt01_inst.voices[0].formatAndSend(dt01.cmd_fbgain, 2**5)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env, 2**16)

if "test" in sys.argv:
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_increment, [2**12]*32)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env, [2**16]*32)

if "f" in sys.argv:
	dt01_inst.voices[0].formatAndSend(dt01.cmd_increment,2**27)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env, 2**16)
	dt01_inst.voices[0].operators[1].formatAndSend(dt01.cmd_env, 2**12)
	dt01_inst.voices[0].operators[2].formatAndSend(dt01.cmd_env, 2**12)
	dt01_inst.voices[0].operators[3].formatAndSend(dt01.cmd_env, 2**12)
	dt01_inst.voices[0].operators[4].formatAndSend(dt01.cmd_env, 2**7)
	dt01_inst.voices[0].operators[5].formatAndSend(dt01.cmd_env, 2**14)
	dt01_inst.voices[0].operators[6].formatAndSend(dt01.cmd_env, 2**16)
	dt01_inst.voices[0].formatAndSend(dt01.cmd_fm_algo, 0o77754321)
	
if "p" in sys.argv:
	dt01_inst.gather()
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env, 2**16)
	dt01_inst.voices[1].operators[0].formatAndSend(dt01.cmd_env, 2**16)
	dt01_inst.voices[0].formatAndSend(dt01.cmd_increment, 2**13)
	dt01_inst.voices[1].formatAndSend(dt01.cmd_increment, 2**13*3/2)
	dt01_inst.release()

if "env" in sys.argv:
	dt01_inst.voices[0].formatAndSend(dt01.cmd_fm_algo, 0o77777777)
	dt01_inst.formatAndSend(dt01.cmd_env_clkdiv, 2**8)
	dt01_inst.formatAndSend(dt01.cmd_shift, 2)
	#dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_envexp, envexp)
	envrate = 2**8
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_increment, 2**23)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_increment_rate, 2**18)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env, 2**16)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env_rate, envrate)

	while(not GPIO.input(37)):
		pass
		
	voiceno, opno = dt01.getIRQueue()
	
	dt01.formatAndSend(dt01.cmd_env_rate, voiceno, opno, 0)
	#dt01.formatAndSend(dt01.cmd_envexp,   voiceno, opno, envexp)
	dt01.formatAndSend(dt01.cmd_env,      voiceno, opno, 0)
	dt01.formatAndSend(dt01.cmd_env_rate, voiceno, opno, envrate)