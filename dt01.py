import spidev
import struct
#maxSpiSpeed = 120000000
maxSpiSpeed = 100000000
spi = spidev.SpiDev()
spi.open(1, 0)
spi.max_speed_hz=maxSpiSpeed
from bitarray import bitarray
import logging
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
from ilock import ILock
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

import logging

logger = logging.getLogger('DT01')

MIDINOTES      = 128
CONTROLCOUNT   = 128
OPERATORCOUNT  = 8

controlNum2ParamName = [""]*CONTROLCOUNT

# common midi controls https://professionalcomposers.com/midi-cc-list/

# begin voice parameters
controlNum2ParamName[0 ] = "vibrato_env"  # modwheel. tie it to vibrato (Pitch LFO)
controlNum2ParamName[1 ] = "tremolo_env"  # breath control
#controlNum2ParamName[1 ] = "vibrato_env"  # modwheel. tie it to vibrato (Pitch LFO)
#controlNum2ParamName[0 ] = "tremolo_env"  # breath control
controlNum2ParamName[4 ] = "fbgain"         
controlNum2ParamName[5 ] = "fbsrc"          

controlNum2ParamName[7 ]  = "voicegain"       # common midi control
controlNum2ParamName[9 ]  = "baseincrement"       # 
controlNum2ParamName[10] = "pan"             # common midi control
controlNum2ParamName[11] = "expression"      # common midi control


OPBASE = [0]*8
# begin operator parameters
controlNum2ParamName[13] = "opno"            
OPBASE[0]  = 14
controlNum2ParamName[14] = "env"            
controlNum2ParamName[15] = "env_porta"      
controlNum2ParamName[16] = "envexp"         
controlNum2ParamName[17] = "increment"      
controlNum2ParamName[18] = "increment_porta"
controlNum2ParamName[19] = "incexp"         
controlNum2ParamName[20] = "fmsrc"         
controlNum2ParamName[21] = "amsrc"         
controlNum2ParamName[22] = "static"         
controlNum2ParamName[23] = "sounding"         
   

# common midi controls
controlNum2ParamName[64] = "sustain"         # common midi control
controlNum2ParamName[65] = "portamento"      # common midi control
controlNum2ParamName[71] = "filter_resonance"# common midi control
controlNum2ParamName[74] = "filter_cutoff"   # common midi control


# begin global params
controlNum2ParamName[110] = "env_clkdiv"     
controlNum2ParamName[111] = "flushspi"       
controlNum2ParamName[112] = "passthrough"    
controlNum2ParamName[113] = "shift"          

paramName2Num = {}
for i, name in enumerate(controlNum2ParamName):
	paramName2Num[name] = i

import inspect

def DT01_fromFile(filename):
	with open(filename, 'rb') as f:
		return pickle.load(f)

class DT01():
	def toFile(self, filename):
		with open(filename, 'wb+') as f:
			pickle.dump(self, f)
	
	def __init__(self, polyphony = 512):
		self.fpga_interface_inst = fpga_interface()
		self.voices = 0
		self.polyphony = polyphony
		self.voicesPerPatch = min(self.polyphony, 32)
		self.patchesPerDT01 = int(round(self.polyphony / self.voicesPerPatch))
		self.voices = []
		self.voiceSets = []
		self.loanTime = [0]*self.patchesPerDT01
		
		index = 0
		for i in range(self.patchesPerDT01):
			newSet = []
			for j in range(self.voicesPerPatch):
				newVoice = Voice(index, self.fpga_interface_inst)
				self.voices += [newVoice]
				newSet      += [newVoice]
				index += 1
			self.voiceSets += [newSet]

	def getVoices(self):
		# return the longest since activation
		oldestSetIndex = np.argsort(self.loanTime)[0]
		return self.voiceSets[oldestSetIndex]
	
	def initialize(self):
		self.fpga_interface_inst.gather()
		self.allChildren = self.voices
		for voice in self.voices:
			#paramName, mm_opno,  voiceno,  payload
			voice.send("cmd_static"       , 0b11000000)
			voice.send("cmd_baseincrement", 2**15)
			voice.send("cmd_sounding"     , 0b00000001)
			voice.send("cmd_fm_algo"      , 0o77777777)
			voice.send("cmd_am_algo"      , 0o00000000)
			voice.send("cmd_fbgain"       , 0)
			voice.send("cmd_fbsrc"        , 0)
			for channel in voice.channels:
				channel.send("cmd_channelgain", 2**16) 
			for operator in voice.operators:
				operator.send("cmd_env"            , 0)
				operator.send("cmd_env_porta"      , 2**10)
				operator.send("cmd_envexp"         , 0x01)

				if operator.index < 6:
					operator.send("cmd_increment"      , 2**12) # * self.paramName2Real["increment"]
				else:
					operator.send("cmd_increment"      , 1) # * self.paramName2Real["increment"]

				operator.send("cmd_increment_porta", 2**13)
				operator.send("cmd_incexp"         , 0x01)

		self.fpga_interface_inst.release()
		self.send("cmd_flushspi"     , 0)
		self.send("cmd_passthrough"  , 0)
		self.send("cmd_shift"        , 2)
		self.send("cmd_env_clkdiv"   , 5)
	
	def send(self, param, value):
		self.fpga_interface_inst.send(param, 0, 0, value)
	
	

		
class Voice():
		
	def __init__(self, index, fpga_interface_inst):
		self.index = index
		self.fpga_interface_inst = fpga_interface_inst
		self.spawntime = 0
		self.index = index
		self.note = None
		self.sounding = False    
		self.defaultIncrement = 0
		self.indexInCluster = 0
		self.operators = []
		for opindex in range(OPERATORCOUNT):
			self.operators += [Operator(self, opindex, fpga_interface_inst)]
		
		self.channels = []
		self.channels += [Channel(self, 0, fpga_interface_inst)]
		self.channels += [Channel(self, 1, fpga_interface_inst)]
		
		self.allChildren = self.channels + self.operators 
			
	def send(self, param, value):
		self.fpga_interface_inst.send(param, 0, self.index, value)


class Channel():
	def __init__(self, voice, index, fpga_interface_inst):
		self.index = index
		self.voice = voice
		self.fpga_interface_inst = fpga_interface_inst
		self.selected = False
		
	def send(self, param, value):
		self.fpga_interface_inst.send(param, self.index, self.voice.index, value)
		

# OPERATOR DESCRIPTIONS
class Operator():
	def __init__(self, voice, index, fpga_interface_inst):
		self.index = index
		self.voice = voice
		self.base  = OPBASE[self.index]
		self.fpga_interface_inst = fpga_interface_inst
		self.sounding = 0
		self.fmsrc    = 7
		self.amsrc    = 0
		self.static   = 0 
		self.selected = False
		
	def send(self, param, value):
		self.fpga_interface_inst.send(param, self.index, self.voice.index, value)

	def __unicode__(self):
		if self.index != None:
			return str(str(type(self))) + " #" + str(self.index) + " of Voice " + str(self.voice) 
		else:
			return str(type(self)) + " #" + "ALL"


class fpga_interface():
	
	cmdName2number = {}
	cmdName2number["cmd_static"]  = 67
	cmdName2number["cmd_baseincrement"]  = 68
	cmdName2number["cmd_sounding"]  = 69
	cmdName2number["cmd_fm_algo"]  = 70
	cmdName2number["cmd_am_algo"  ]  = 71
	cmdName2number["cmd_fbgain"   ]  = 73
	cmdName2number["cmd_fbsrc"    ]  = 74
	cmdName2number["cmd_channelgain"    ] = 75
	cmdName2number["cmd_env"            ] = 76 
	cmdName2number["cmd_env_porta"      ] = 77 
	cmdName2number["cmd_envexp"         ] = 78 
	cmdName2number["cmd_increment"      ] = 79 
	cmdName2number["cmd_increment_porta"] = 80  
	cmdName2number["cmd_incexp"         ] = 81
	cmdName2number["cmd_flushspi"       ] = 120
	cmdName2number["cmd_passthrough"    ] = 121
	cmdName2number["cmd_shift"          ] = 122
	cmdName2number["cmd_env_clkdiv"     ] = 123 # turn this back to 123
		
	def __init__(self):
		self.gathering = False
		state = {}
		pass

	def format_command_real(self, mm_paramno, voiceno,  payload):
		payload = payload*(2**16)
		payload = struct.pack(">I", int(payload))
		payload = [mm_paramno, 0, 0, voiceno] + [int(i) for i in payload]
		#logger.debug([hex(p) for p in payload])
		return payload
		
	def format_command_word(self, mm_paramno, mm_opno,  voiceno, voicemode = 0):
		payload_array = [mm_paramno, 1 << mm_opno, (voicemode << 7) | (voiceno >> 8), voiceno]
		#logger.debug([hex(p) for p in payload_array])
		return payload_array
		
	def format_command_multiple(self, mm_paramno, mm_opno,  voiceno, payload, voicemode = 1):
		payload = np.array(payload, dtype=np.int)
		payload = payload.byteswap().tobytes()
		payload_array = [mm_paramno, 1 << mm_opno, (voicemode << 7) | (voiceno >> 8), voiceno] + [int(i) for i in payload] 
		#logger.debug([hex(p) for p in payload_array])
		return payload_array
		
	def format_command_int(self, mm_paramno, mm_opno,  voiceno,  payload, voicemode = 0):
		payload_packed = struct.pack(">I", int(payload))
		payload_array = [mm_paramno, 1 << mm_opno, (voicemode << 7) | (voiceno >> 8), voiceno] + [int(i) for i in payload_packed] 
		#logger.debug([hex(p) for p in payload_array])
		return payload_array
		
	def format_command_3bezier_targets(self, mm_paramno, voiceno,  bt0, bt1, bt2):
		payload = struct.pack(">I", (int(bt0*(2**28)) & 0x3FF00000) + (int(bt1*(2**18)) & 0x000FFC00) + (int(bt2*(2**8)) & 0x000003FF))
		payload = [mm_paramno, 0, 0, voiceno] + [int(p) for p in payload]
		#logger.debug([hex(p) for p in payload])
		return payload
		
	def sendMultiple(self, paramName, opno, voiceno, payload, voicemode = 0):
		#logger.debug(voicemode)
		tosend = self.format_command_multiple(self.cmdName2number[paramName], opno, voiceno, payload, voicemode = voicemode)
		#with ILock('jlock', lock_directory=sys.path[0]):
		logger.debug("voicemode: " + str(voicemode) + ": " + paramName + " voice: " + str(voiceno) + " opno: " + str(opno) + " PL(" + str(len(payload)) + "): " + str(payload[:8]))
		#logger.debug(payload)
		#logger.debug([hex(s) for s in tosend])
		spi.xfer2(tosend)
		#logger.debug("sent")
	
	def gather(self, voicemode = True):
		self.sendDictAcrossVoices = {}
		self.sendDictAcrossOperators = {}
		self.voicemode = voicemode
		self.gathering = True
		self.lowestVoiceIndex = 10000
		
	def release(self):
		#logger.debug("sendDictAcrossVoices")
		#logger.debug(self.sendDictAcrossVoices)
		if self.voicemode:
			for param, opdict in self.sendDictAcrossVoices.items():
				for opno, payloads in opdict.items():
					self.sendMultiple(param, opno, self.lowestVoiceIndex, payloads, voicemode = self.voicemode)
		
		else:
			logger.debug(self.sendDictAcrossOperators)
			for param, voicedict in self.sendDictAcrossOperators.items():
				for voiceno, payloads in voicedict.items():
					self.sendMultiple(param, 0, voiceno, payloads, voicemode = self.voicemode)
			
		self.gathering = False
	
	def send(self, paramName, mm_opno,  voiceno,  payload):
	
		# gather data if gathering is on
		if self.gathering: 
			
			#logger.debug("not sending " + paramName + " " + str(payload))
			# across voices 
			if self.voicemode:
				if paramName not in self.sendDictAcrossVoices.keys():          self.sendDictAcrossVoices[paramName] = {}
				if mm_opno not in self.sendDictAcrossVoices[paramName].keys(): self.sendDictAcrossVoices[paramName][mm_opno] = []
				self.sendDictAcrossVoices[paramName][mm_opno] += [payload]
			
			else:
				# within voice
				if paramName not in self.sendDictAcrossOperators.keys():          self.sendDictAcrossOperators[paramName] = {}
				if voiceno not in self.sendDictAcrossOperators[paramName].keys(): self.sendDictAcrossOperators[paramName][voiceno] = []
				self.sendDictAcrossOperators[paramName][voiceno] += [payload]
				
			self.lowestVoiceIndex = min(self.lowestVoiceIndex , voiceno)
		else:
			tosend = self.format_command_int(self.cmdName2number[paramName], mm_opno, voiceno, payload)
			#with ILock('jlock', lock_directory=sys.path[0]):
			logger.debug("sending " + paramName + "(" + str(self.cmdName2number[paramName]) + ")" + " operator:" + str(mm_opno) + " voice:" + str(voiceno) + " payload:" + str(payload))
			#logger.debug(tosend)
			spi.xfer2(tosend)
			#logger.debug("sent")
		
if __name__ == "__main__":
	fpga_interface_inst = fpga_interface()
	
	#for voiceno in range(fpga_interface_inst.POLYPHONYCOUNT):
	#	for opno in range(fpga_interface_inst.OPERATORCOUNT):
	#		for command in fpga_interface_inst.cmdName2number.keys():
	#			fpga_interface_inst.send(command, opno, voiceno, 0)
				
	# run testbench
	fpga_interface_inst.send("cmd_env_clkdiv", 0, 0, 0)
	
	opno = 0
	voiceno = 0
	fpga_interface_inst.send("cmd_channelgain_right", opno, voiceno, 2**16)
	fpga_interface_inst.send("cmd_gain_porta"      , opno, voiceno, 2**16)
	fpga_interface_inst.send("cmd_gain"            , opno, voiceno, 2**16)
	fpga_interface_inst.send("cmd_increment_porta" , opno, voiceno, 2**12)
	fpga_interface_inst.send("cmd_increment"       , opno, voiceno, 2**22)
	fpga_interface_inst.send("cmd_fm_algo"       , opno, voiceno, 1)

	opno = 1
	fpga_interface_inst.send("cmd_increment_porta", opno, voiceno, 2**30)
	fpga_interface_inst.send("cmd_increment"      , opno, voiceno, 2**22)
	fpga_interface_inst.send("cmd_fm_algo"      , opno, voiceno, 2)
	
	fpga_interface_inst.send("cmd_flushspi", 0, 0, 0)
	fpga_interface_inst.send("cmd_shift"   , 0, 0, 0)
		