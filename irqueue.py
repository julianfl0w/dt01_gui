import spidev
import struct
#maxSpiSpeed = 120000000
maxSpiSpeed = 120000000
spi = spidev.SpiDev()
spi.open(1, 0)
spi.max_speed_hz=maxSpiSpeed
from bitarray import bitarray
import logging
import RPi.GPIO as GPIO
from ilock import ILock
import json
import sys
import numpy as np 
import time
import rtmidi
from rtmidi.midiutil import *
import mido
import math
import hjson as json
import socket
import os
import traceback
import pickle
import dt01
import logging
import collections
import math
from multiprocessing import Process
#from multiprocessing import shared_memory
import RPi.GPIO as GPIO
import SharedArray as sa
logger = logging.getLogger('DT01')
	
MIDINOTES      = 128
CONTROLCOUNT   = 128
					
def envServiceProc():
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(37 , GPIO.IN)
	envelopePhase = sa.attach("shm://envelopePhase")
	baseEnv = sa.attach("shm://baseEnv")
	fpga_interface_inst = dt01.fpga_interface()
	# flush queue
	while(GPIO.input(37)):
		fpga_interface_inst.getIRQueue()
	
	while(1):
		try:
			if(GPIO.input(37)):
				res = fpga_interface_inst.getIRQueue()
				opno = int(math.log2((res[1]<<7) + (res[2]>>1)))
				voiceno = int(((res[2] & 0x01)<<8) + res[3])
				logger.debug("IRQUEUE! voice:" + str(voiceno) + " op:"+ str(opno))
				currPhase = envelopePhase[voiceno, opno]
					
				logger.debug("IRQUEUE! voice:" + str(voiceno) + " op:"+ str(opno) + " phase:" + str(currPhase))
				if np.sum(res) == 0:
					continue
				if currPhase >= self.phaseCount - 1:
					logger.debug("STOP PHASE")
					continue
				logger.debug(envelopePhase[0,:])
				#logger.debug("self.envelopeExp "   + str(self.envelopeExp  [opno][currPhase]))
				#logger.debug("self.envelopeLevel " + str(self.envelopeLevel[opno][currPhase]*baseEnv))
				#logger.debug("self.envelopeRate "  + str(self.envelopeRate [opno][currPhase]))
				
				logger.debug(res)
				
				fpga_interface_inst.send(dt01.cmd_env_rate, opno, voiceno, 0)
				fpga_interface_inst.send(dt01.cmd_envexp,   opno, voiceno, self.envelopeExp  [opno][currPhase])
				fpga_interface_inst.send(dt01.cmd_env,      opno, voiceno, self.envelopeLevel[opno][currPhase])
				fpga_interface_inst.send(dt01.cmd_env_rate, opno, voiceno, self.envelopeRate [opno][currPhase])
				envelopePhase[voiceno, opno] = (envelopePhase[voiceno, opno] + 1) % self.phaseCount
		except:
			currPhase = 0
				
				
if __name__ == "__main__":
	logger = logging.getLogger('DT01')
	envServiceProc()