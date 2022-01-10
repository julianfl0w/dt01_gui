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

envrate = 2**8

if "passthrough" in sys.argv:
	dt01_inst.formatAndSend(dt01.cmd_passthrough, 1)
	dt01_inst.formatAndSend(dt01.cmd_shift      , 0)  
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_increment_rate, 0)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_increment, 2**24)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_increment_rate, 2**28)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env_rate, 0)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env, 2**28)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env_rate, 2**20)

	
if "c5" in sys.argv:
	dt01_inst.formatAndSend(dt01.cmd_shift      , 4)  
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_increment_rate, 0)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_increment, 23409809)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_increment_rate, 23409808/8)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env_rate, 0)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env, 2**28)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env_rate, 2**20)

if "t" in sys.argv:
	opno = 5
	dt01_inst.formatAndSend(dt01.cmd_sounding   , 1<<opno)  
	dt01_inst.formatAndSend(dt01.cmd_shift      , 4)  
	dt01_inst.voices[0].operators[6].formatAndSend(dt01.cmd_env_rate, 0)
	dt01_inst.voices[0].operators[6].formatAndSend(dt01.cmd_env, 2**29)
	dt01_inst.voices[0].operators[6].formatAndSend(dt01.cmd_env_rate, 2**28)
	dt01_inst.voices[0].operators[6].formatAndSend(dt01.cmd_increment_rate, 0)
	dt01_inst.voices[0].operators[6].formatAndSend(dt01.cmd_increment, 2**17)
	dt01_inst.voices[0].operators[6].formatAndSend(dt01.cmd_increment_rate, 2**28)
	
	dt01_inst.voices[0].operators[opno].formatAndSend(dt01.cmd_increment_rate, 0)
	dt01_inst.voices[0].operators[opno].formatAndSend(dt01.cmd_increment,      23409809/2)
	dt01_inst.voices[0].operators[opno].formatAndSend(dt01.cmd_increment_rate, 23409808/2/8)
	dt01_inst.voices[0].operators[opno].formatAndSend(dt01.cmd_env_rate, 0)
	dt01_inst.voices[0].operators[opno].formatAndSend(dt01.cmd_env, 2**28)
	dt01_inst.voices[0].operators[opno].formatAndSend(dt01.cmd_env_rate, 2**20)
	
if "v" in sys.argv:
	dt01_inst.voices[0].operators[7].formatAndSend(dt01.cmd_env_rate, 2**20)
	dt01_inst.voices[0].operators[7].formatAndSend(dt01.cmd_env, 2**19)
	dt01_inst.voices[0].operators[7].formatAndSend(dt01.cmd_increment_rate, 2**28)
	dt01_inst.voices[0].operators[7].formatAndSend(dt01.cmd_increment, 2**18)
	
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_increment_rate, 2**28)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env_rate, 2**20)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env, 2**30)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_increment, 2**23)
	
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
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env, 2**16)
	dt01_inst.voices[1].operators[0].formatAndSend(dt01.cmd_env, 2**16)
	dt01_inst.voices[0].formatAndSend(dt01.cmd_increment, 2**13)
	dt01_inst.voices[1].formatAndSend(dt01.cmd_increment, 2**13*3/2)

if "env" in sys.argv:
	dt01_inst.voices[0].formatAndSend(dt01.cmd_fm_algo, 0o77777777)
	dt01_inst.formatAndSend(dt01.cmd_shift, 0)
	#dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_envexp, envexp)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_increment_rate, 0)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_increment, 2**24)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_increment_rate, 2**28)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env_rate, 0)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env, 2**28)
	dt01_inst.voices[0].operators[0].formatAndSend(dt01.cmd_env_rate, 2**20)

	while(1):
		while(not GPIO.input(37)):
			pass
		
		voiceno, opno = dt01.getIRQueue()
		logger.debug("recvd irq (" + str(voiceno) + "," + str(opno) + ")")
		
		dt01.formatAndSend(dt01.cmd_env_rate, voiceno, opno, 0)
		#dt01.formatAndSend(dt01.cmd_envexp,   voiceno, opno, envexp)
		dt01.formatAndSend(dt01.cmd_env,      voiceno, opno, 0)
		dt01.formatAndSend(dt01.cmd_env_rate, voiceno, opno, 2**10)
		