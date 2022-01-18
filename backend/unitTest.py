import dtfm
import sys
import logging
import os
import math
from multiprocessing import Process
import RPi.GPIO as GPIO
import time
#from multiprocessing import shared_memory


logger = logging.getLogger('dtfm')
formatter = logging.Formatter('{%(pathname)s:%(lineno)d %(message)s}')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(1)

logger.debug("Instantiating dtfm")
polyphony = 512
filename = "dtfm_" + str(int(polyphony)) + ".pkl"

logger.debug("initializing")
dtfm_inst = dtfm.dtfm(polyphony = polyphony)

logger.debug("Applying a light touch")

envrate = 2**8

if "passthrough" in sys.argv:
	dtfm_inst.formatAndSend(dtfm.cmd_passthrough, 1)
	dtfm_inst.formatAndSend(dtfm.cmd_shift      , 0)  
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_increment_rate, 0)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_increment, 2**24)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_increment_rate, 2**28)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_env_rate, 0)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_env, 2**28)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_env_rate, 2**20)

	
if "c5" in sys.argv:
	dtfm_inst.formatAndSend(dtfm.cmd_shift      , 4)  
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_increment_rate, 0)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_increment, 23409809)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_increment_rate, 23409808/8)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_env_rate, 0)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_env, 2**28)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_env_rate, 2**20)

if "t" in sys.argv:
	opno = 5
	dtfm_inst.formatAndSend(dtfm.cmd_sounding   , 1<<opno)  
	dtfm_inst.formatAndSend(dtfm.cmd_shift      , 4)  
	dtfm_inst.voices[0].operators[6].formatAndSend(dtfm.cmd_env_rate, 0)
	dtfm_inst.voices[0].operators[6].formatAndSend(dtfm.cmd_env, 2**29)
	dtfm_inst.voices[0].operators[6].formatAndSend(dtfm.cmd_env_rate, 2**28)
	dtfm_inst.voices[0].operators[6].formatAndSend(dtfm.cmd_increment_rate, 0)
	dtfm_inst.voices[0].operators[6].formatAndSend(dtfm.cmd_increment, 2**17)
	dtfm_inst.voices[0].operators[6].formatAndSend(dtfm.cmd_increment_rate, 2**28)
	
	dtfm_inst.voices[0].operators[opno].formatAndSend(dtfm.cmd_increment_rate, 0)
	dtfm_inst.voices[0].operators[opno].formatAndSend(dtfm.cmd_increment,      23409809/2)
	dtfm_inst.voices[0].operators[opno].formatAndSend(dtfm.cmd_increment_rate, 23409808/2/8)
	dtfm_inst.voices[0].operators[opno].formatAndSend(dtfm.cmd_env_rate, 0)
	dtfm_inst.voices[0].operators[opno].formatAndSend(dtfm.cmd_env, 2**28)
	dtfm_inst.voices[0].operators[opno].formatAndSend(dtfm.cmd_env_rate, 2**20)
	
if "v" in sys.argv:
	dtfm_inst.voices[0].operators[7].formatAndSend(dtfm.cmd_env_rate, 2**20)
	dtfm_inst.voices[0].operators[7].formatAndSend(dtfm.cmd_env, 2**19)
	dtfm_inst.voices[0].operators[7].formatAndSend(dtfm.cmd_increment_rate, 2**28)
	dtfm_inst.voices[0].operators[7].formatAndSend(dtfm.cmd_increment, 2**18)
	
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_increment_rate, 2**28)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_env_rate, 2**20)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_env, 2**30)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_increment, 2**23)
	
if "fb" in sys.argv:
	dtfm_inst.voices[0].formatAndSend(dtfm.cmd_increment, 2**27)
	dtfm_inst.voices[0].formatAndSend(dtfm.cmd_fm_algo, 0o77777770)
	dtfm_inst.voices[0].formatAndSend(dtfm.cmd_fbsrc, 0)
	dtfm_inst.voices[0].formatAndSend(dtfm.cmd_fbgain, 2**5)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_env, 2**16)

if "test" in sys.argv:
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_increment, [2**12]*32)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_env, [2**16]*32)

if "f" in sys.argv:
	dtfm_inst.voices[0].formatAndSend(dtfm.cmd_increment,2**27)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_env, 2**16)
	dtfm_inst.voices[0].operators[1].formatAndSend(dtfm.cmd_env, 2**12)
	dtfm_inst.voices[0].operators[2].formatAndSend(dtfm.cmd_env, 2**12)
	dtfm_inst.voices[0].operators[3].formatAndSend(dtfm.cmd_env, 2**12)
	dtfm_inst.voices[0].operators[4].formatAndSend(dtfm.cmd_env, 2**7)
	dtfm_inst.voices[0].operators[5].formatAndSend(dtfm.cmd_env, 2**14)
	dtfm_inst.voices[0].operators[6].formatAndSend(dtfm.cmd_env, 2**16)
	dtfm_inst.voices[0].formatAndSend(dtfm.cmd_fm_algo, 0o77754321)
	
if "p" in sys.argv:
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_env, 2**16)
	dtfm_inst.voices[1].operators[0].formatAndSend(dtfm.cmd_env, 2**16)
	dtfm_inst.voices[0].formatAndSend(dtfm.cmd_increment, 2**13)
	dtfm_inst.voices[1].formatAndSend(dtfm.cmd_increment, 2**13*3/2)

if "env" in sys.argv:
	dtfm_inst.voices[0].formatAndSend(dtfm.cmd_fm_algo, 0o77777777)
	dtfm_inst.formatAndSend(dtfm.cmd_shift, 0)
	#dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_envexp, envexp)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_increment_rate, 0)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_increment, 2**24)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_increment_rate, 2**28)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_env_rate, 0)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_env, 2**28)
	dtfm_inst.voices[0].operators[0].formatAndSend(dtfm.cmd_env_rate, 2**20)

	while(1):
		while(not GPIO.input(37)):
			pass
		
		voiceno, opno = dtfm.getIRQueue()
		logger.debug("recvd irq (" + str(voiceno) + "," + str(opno) + ")")
		
		dtfm.formatAndSend(dtfm.cmd_env_rate, voiceno, opno, 0)
		#dtfm.formatAndSend(dtfm.cmd_envexp,   voiceno, opno, envexp)
		dtfm.formatAndSend(dtfm.cmd_env,      voiceno, opno, 0)
		dtfm.formatAndSend(dtfm.cmd_env_rate, voiceno, opno, 2**10)
		