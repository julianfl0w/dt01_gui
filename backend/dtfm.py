import spi_interface
import struct
from bitarray import bitarray
import logging
import sys
import numpy as np 
import time
import rtmidi
from rtmidi.midiutil import *
import math
import hjson as json
import socket
import os
import traceback
import pickle
import RPi.GPIO as GPIO
import logging
import faulthandler; faulthandler.enable()

logger = logging.getLogger('dtfm')

MIDINOTES      = 128
CONTROLCOUNT   = 128
OPERATORCOUNT  = 8
SOUNDINGOPS    = 6
#SOUNDINGOPS    = 1

controlNum2Name = [""]*CONTROLCOUNT

# common midi controls https://professionalcomposers.com/midi-cc-list/

# begin voice parameters
controlNum2Name[0 ] = "ctrl_vibrato_env"  # modwheel. tie it to vibrato (Pitch LFO)
controlNum2Name[1 ] = "ctrl_tremolo_env"  # breath control
controlNum2Name[11] = "ctrl_expression"      # common midi control
controlNum2Name[33] = "ctrl_silence"      # common midi control

   

# common midi controls
controlNum2Name[64] = "ctrl_sustain"         # common midi control


controlName2Num = {}
for i, name in enumerate(controlNum2Name):
	controlName2Num[name] = i
	if name:
		exec(name + " = " + str(i))

cmdName2number = {}
cmdName2number["cmd_readirqueue"    ] = 64
cmdName2number["cmd_readaudio"      ] = 65
cmdName2number["cmd_readid"         ] = 66

cmdName2number["cmd_sounding"       ] = 69
cmdName2number["cmd_fm_algo"        ] = 70
cmdName2number["cmd_am_algo"        ] = 71
cmdName2number["cmd_fbgain"         ] = 73
cmdName2number["cmd_fbsrc"          ] = 74
cmdName2number["cmd_channelgain"    ] = 75
cmdName2number["cmd_env"            ] = 76 
cmdName2number["cmd_env_rate"       ] = 77 
cmdName2number["cmd_increment"      ] = 79 
cmdName2number["cmd_increment_rate" ] = 80 
cmdName2number["cmd_flushspi"       ] = 120
cmdName2number["cmd_passthrough"    ] = 121
cmdName2number["cmd_shift"          ] = 122

cmdNum2Name = ["0"]*128
for name, number in cmdName2number.items():
	cmdNum2Name[number] = name
		
for name, number in cmdName2number.items():
	if name:
		#print(name + " = " + str(number))
		exec(name + " = " + str(number))


SamplesPerSecond = 96e3
SamplePeriodSeconds = 1.0/SamplesPerSecond

import inspect

def dtfm_fromFile(filename):
	with open(filename, 'rb') as f:
		return pickle.load(f)
	
class JObject():
	def __str__(self):
		return (str(type(self)) + " #" + str(self.index))

def getRateAndLevel(opDict, output_level, maxout = 2**29):
	TIMEARRAY      = opDict["Time (seconds)"]
	LEVELARRAY     = [o * output_level / 100 for o in opDict["Level (unit interval)"]]
	logger.debug(LEVELARRAY)
	if sum(LEVELARRAY) == 0:
		return [0], [0]
	
	while(LEVELARRAY[-2] == 0 and LEVELARRAY[-1] == 0):
		TIMEARRAY = TIMEARRAY[:-1]
		LEVELARRAY= LEVELARRAY[:-1]
	logger.debug("TIMEARRAY " + str(TIMEARRAY))
	logger.debug("LEVELARRAY " + str(LEVELARRAY))
	phaseCount     = len(TIMEARRAY)
	envTimeSeconds = TIMEARRAY
	envThisLevel   = np.multiply(LEVELARRAY, maxout)
	phase  = phaseCount- 1
	finalPhase     = phaseCount- 1

	envTimeSamples   = np.multiply(envTimeSeconds, SamplesPerSecond)
	j = 0
	# if new level is too close to old level, set to the smallest increase that makes time
	tooClose         = np.zeros((phaseCount))
	envRatePerSample = np.zeros((phaseCount))
	# last level always 0
	envThisLevel[phaseCount-1] = 0

	finished = False
	while not finished:
		
		#     L0
		#     /\
		#    /  \R1
		#   /    \________L2 (hodl)
		#  /R0    L1  R2  \               
		# /                \R3
		#/                  \L3 = 0
		roll = 1
		for phase in range(phaseCount):
			#logger.debug("\n\nphase " + str(phase))
			envPrevLevel            = np.roll(envThisLevel[:phaseCount], roll, axis = 0)
			envStepToThisOne        = envThisLevel[:phaseCount] - envPrevLevel[:phaseCount]

			goingUp  = envThisLevel[phase] >= envPrevLevel[phase]
			tooClose [phase] = envPrevLevel[phase] + envTimeSamples[phase] > envThisLevel[phase] > envPrevLevel[phase] - envTimeSamples[phase] 

			# change previous env if this is the final one (always 0) 
			# otherwise change this env 
			if tooClose[phase]:
				if phase == 0:
					#logger.debug("adjusting first")
					envThisLevel[0] = envThisLevel[phase-1] + envTimeSamples[0] 

				else:
					if goingUp:
						envThisLevel[phase] = envPrevLevel[phase] + envTimeSamples[phase] 
					else:
						envThisLevel[phase] = envPrevLevel[phase] - envTimeSamples[phase] 

			if roll == 1:
				envRatePerSample= envStepToThisOne / envTimeSamples

		#input()
				
		envPrevLevel            = np.roll(envThisLevel[:phaseCount], roll, axis = 0)
		
		minup  = (envPrevLevel + envTimeSamples)
		mindown= (envPrevLevel - envTimeSamples)
		#logger.debug("envThisLevel     : " + str(envThisLevel    ))
		#logger.debug("envTimeSamples     : " + str(envTimeSamples       ))
		#logger.debug("envPrevLevel        : " + str(envPrevLevel       ))
		#logger.debug("goingUp             : " + str(goingUp  ))
		#logger.debug("envRatePerSample : " + str(envRatePerSample))
		#logger.debug("tooClose         : " + str(tooClose        ))
		#logger.debug("minup : " + str(minup))
		#logger.debug("mindown         : " + str(mindown        ))
		tooClose = np.logical_and(np.less(envThisLevel[:phaseCount], minup),  np.greater(envThisLevel[:phaseCount],mindown))

		finished = not any(tooClose)

	logger.debug("envRatePerSample " + str(envRatePerSample))
	logger.debug("envThisLevel " + str(envThisLevel))
	return envRatePerSample, envThisLevel
	
class dtfm(JObject):

	def toFile(self, filename):
		with open(filename, 'wb+') as f:
			pickle.dump(self, f)
	
	def __init__(self, polyphony = 512):
		
		self.voices = 0
		self.polyphony = polyphony
		self.voicesPerPatch = min(self.polyphony, 512)
		self.patchesPerdtfm = int(round(self.polyphony / self.voicesPerPatch))
		self.voices = []
		self.voiceSets = []
		self.loanTime = [0]*self.patchesPerdtfm
		self.maxPhaseCount = 10 # we store in memory up to 100 phases
		
		index = 0
		for i in range(self.patchesPerdtfm):
			newSet = []
			for j in range(self.voicesPerPatch):
				newVoice = Voice(index, self)
				self.voices += [newVoice]
				newSet      += [newVoice]
				index += 1
			self.voiceSets += [newSet]
		
	
		initDict = {}
		initDict["sounding"] = 0b00000001
		initDict["fm_algo" ] = 0x77777777
		initDict["am_algo" ] = 0x00000000
		initDict["fbgain"  ] = 0         
		initDict["fbsrc"   ] = 0         
		initDict["channelgain"] = [2**16/8, 2**16/8]         
		initDict["env"]       = [0    , 0    , 0    , 0    , 0    , 0    , 0    , 0    ]
		initDict["env_rate" ] = [2**27, 2**27, 2**27, 2**27, 2**27, 2**27, 2**27, 2**27]
		
		initDict["increment"      ] = [0    , 0    , 0    , 0    , 0    , 0    , 2**12, 2**12]
		initDict["increment_rate" ] = [2**29, 2**29, 2**29, 2**29, 2**29, 2**29, 2**29, 2**29]
		
		initDict["flushspi"    ] = 0
		initDict["passthrough" ] = 0
		initDict["shift"       ] = 4
		
		self.baseIncrement    = np.zeros((self.polyphony, OPERATORCOUNT))
		self.incrementScale   = np.zeros((self.polyphony, OPERATORCOUNT))
		self.defaultIncrement = np.zeros((self.polyphony, OPERATORCOUNT))
		self.tosend           = np.zeros((self.polyphony, OPERATORCOUNT), dtype = np.int32)
		
		self.initialize(initDict)
		
	def getVoices(self):
		# return the longest since activation
		oldestSetIndex = np.argsort(self.loanTime)[0]
		return self.voiceSets[oldestSetIndex]
	
	def initialize(self, initDict, voices = None):
		if voices == None:
			voices = self.voices
		lowestVoiceIndex = min([v.index for v in voices])
		initIRQueue()
		
		print(initDict["sounding"])
		print([initDict["sounding"]]*len(voices))
		formatAndSend(cmd_sounding     , lowestVoiceIndex, 0, [initDict["sounding"]]*len(voices))
		formatAndSend(cmd_fm_algo      , lowestVoiceIndex, 0, [initDict["fm_algo" ]]*len(voices))
		formatAndSend(cmd_am_algo      , lowestVoiceIndex, 0, [initDict["am_algo" ]]*len(voices))
		formatAndSend(cmd_fbgain       , lowestVoiceIndex, 0, [initDict["fbgain"  ]]*len(voices))
		formatAndSend(cmd_fbsrc        , lowestVoiceIndex, 0, [initDict["fbsrc"   ]]*len(voices))
		
		for channel in range(2):
			formatAndSend(cmd_channelgain, lowestVoiceIndex, channel, [initDict["channelgain"][channel]]*len(voices))
			
		#paramNum, mm_opno,  voiceno,  payload
		for opno in range(OPERATORCOUNT):
			formatAndSend(cmd_env            , lowestVoiceIndex, opno, [initDict["env"]      [opno]]*len(voices))
			formatAndSend(cmd_env_rate       , lowestVoiceIndex, opno, [initDict["env_rate" ][opno]]*len(voices))

			formatAndSend(cmd_increment      , lowestVoiceIndex, opno, [initDict["increment"      ][opno]]*len(voices)) # * self.paramNum2Real[increment]
			formatAndSend(cmd_increment_rate , lowestVoiceIndex, opno, [initDict["increment_rate" ][opno]]*len(voices)) # * self.paramNum2Real[increment]

		formatAndSend(cmd_flushspi     , 0, 0, initDict["flushspi"    ])    
		formatAndSend(cmd_passthrough  , 0, 0, initDict["passthrough" ])    
		formatAndSend(cmd_shift        , 0, 0, initDict["shift"       ])    # -4
		return 0
		
	def formatAndSend(self, param, value, voicemode = True):
		return formatAndSend(param, 0, 0, value, voicemode = voicemode)
	
		
class Voice(JObject):
		
	def __init__(self, index, dtfm_inst):
		self.dtfm_inst = dtfm_inst
		self.index = index
		self.spawntime = 0
		self.index = index
		self.note = None
		self.sounding = False    
		self.defaultIncrement = 0
		self.indexInCluster = 0
		self.operators = []
		self.opZeros = np.array([0]* OPERATORCOUNT, dtype=np.int32)

		for opindex in range(OPERATORCOUNT):
			self.operators += [Operator(self, opindex, dtfm_inst)]
		
		self.channels = []
		self.channels += [Channel(self, 0)]
		self.channels += [Channel(self, 1)]
		
		self.allChildren = self.channels + self.operators 
	
	def setAllIncrements(self, modifier):
		logger.debug("setting all increments")
		val = np.minimum(self.patch.baseIncrement[self.index] + self.cluster.strikeIncrement[self.index] * modifier, 2**30).astype(np.int32)
		self.formatAndSend(cmd_increment, val[:SOUNDINGOPS], voicemode = False)
	
	
	def setPhaseAllOps(self, phase):
		logger.debug("setPhaseAllOps")
		self.formatAndSend(cmd_env_rate, self.opZeros[:SOUNDINGOPS], voicemode=False)                               
		self.formatAndSend(cmd_env,      self.patch.envThisLevel[:SOUNDINGOPS, phase], voicemode=False)
		self.formatAndSend(cmd_env_rate, self.patch.envRatePerSample[:SOUNDINGOPS, phase], voicemode=False)                           
		for op in self.operators:
			op.phase = phase
		
		return 0
		
	def silenceAllOps(self):
		rates  = []
		for op in self.operators[:6]:
			rates  += [self.patch.envRatePerSample[op.index, self.patch.phaseCount[op.index] - 1]]
			op.phase = self.patch.phaseCount[op.index] - 1
		#logger.debug(rates)
		self.formatAndSend(cmd_env_rate, self.opZeros[:SOUNDINGOPS], voicemode=False)
		self.formatAndSend(cmd_env,      self.opZeros[:SOUNDINGOPS], voicemode=False)
		self.formatAndSend(cmd_env_rate, rates, voicemode=False)        
		
		return 0
		
	def setFBGainReal(self, fbgainreal):
		self.formatAndSend(cmd_fbgain, 2**16*fbgainreal)
		
	def setFBSource(self, source):
		self.formatAndSend(cmd_fbsrc, source)
	
	def getFMAlgo(self, algo):
		formatAndSendVal = 0
		logger.debug(algo)
		for i in reversed(range(6)):
			formatAndSendVal = int(formatAndSendVal) << 4
			formatAndSendVal += int(algo[i] - 1)
			#logger.debug(bin(formatAndSendVal))
		return formatAndSendVal
		
	def setFMAlgo(self, algo):
		self.formatAndSend(dtfm.cmd_fm_algo, getFMAlgo(algo))
	
	def setAMSrc(self, opno, source):
		self.operators[opno].amsrc = source
		formatAndSendVal = 0
		for i in reversed(range(dtfm.OPERATORCOUNT)):
			formatAndSendVal = int(formatAndSendVal) << 4
			formatAndSendVal += int(voice.operators[i].amsrc)
			#logger.debug(bin(formatAndSendVal))
		voice.formatAndSend(dtfm.cmd_am_algo, formatAndSendVal)
		
	def applySounding(self, isSounding):
		formatAndSendVal = 0
		for i in reversed(range(dtfm.OPERATORCOUNT)):
			formatAndSendVal = int(formatAndSendVal) << 1
			formatAndSendVal += int(voice.operators[i].sounding)
			#logger.debug(bin(formatAndSendVal))
		voice.formatAndSend(dtfm.cmd_sounding, formatAndSendVal)
	
	def formatAndSend(self, param, value, voicemode = False):
		return formatAndSend(param, self.index, 0, value, voicemode)


class Channel(JObject):
	def __init__(self, voice, index):
		self.index = index
		self.voice = voice
		self.selected = False
		
	def formatAndSend(self, param, value):
		return formatAndSend(param, self.voice.index, self.index, value)
		
# OPERATOR DESCRIPTIONS
class Operator(JObject):
	def __init__(self, voice, index, dtfm_inst):
		self.dtfm_inst = dtfm_inst
		self.index = index
		self.voice = voice
		self.sounding = 1
		self.fmsrc    = 7
		self.amsrc    = 0
		self.selected = False
		self.baseIncrement = 0
		self.incrementScale = 1
		
		self.phase         = 3
		
	def formatAndSend(self, param, value, voicemode = False):
		return formatAndSend(param, self.voice.index, self.index, value, voicemode=voicemode)
	
	def setSounding(self, sounding):
		self.sounding = isSounding
		self.voice.applySounding() # need to update by voice because of memory layout in FPGA
				
	def __unicode__(self):
		if self.index != None:
			return str(str(type(self))) + " #" + str(self.index) + " of Voice " + str(self.voice) 
		else:
			return str(type(self)) + " #" + "ALL"

def initIRQueue():

	# IRQUEUE Considerations
	# IRQUEUE Considerations
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(37 , GPIO.IN)
	# flush queue
	while(GPIO.input(37)):
		getIRQueue()

def getIRQueue():

	spi_interface.spi.max_speed_hz=45000000
	formatAndSend(cmd_readirqueue, 0, 0, 0)
	res = formatAndSend(0, 0, 0, 0)
	opnos = []
	opres = (res[1]<<7) + (res[2]>>1)
	#logger.debug("res: " + str(hex(opres)))
	for opno in range(8):
		if (opres >> opno) & 0x01:
			opnos += [opno]
	voiceno = int(((res[2] & 0x01)<<8) + res[3])
	#logger.debug("IRQUEUE! voice:" + str(voiceno) + " op:"+ str(opno))
	spi_interface.spi.max_speed_hz=115000000
	
	return voiceno, opnos

def formatAndSend(paramNum, voiceno, opno, payload, voicemode = 1):
	if type(payload) == list:
		logger.debug("preparing (" + "v"+str(voicemode) + " : " + str(voiceno) + ":" + str(opno) + ") " + cmdNum2Name[paramNum] + " len " + str(len(payload)) + " : "  + str(payload[0:8]))
		payload = np.array(payload, dtype=np.int32)
		payload = payload.byteswap().tobytes()
	elif type(payload) == np.ndarray:
		logger.debug("preparing (" + "v"+str(voicemode) + " : " + str(voiceno) + ":" + str(opno) + ") " + cmdNum2Name[paramNum] + " len " + str(len(payload)) + " : "  + str(payload[0:8]))
		if payload.dtype == np.int32:
			payload = payload.byteswap().tobytes()
		else:
			logger.warning("USE INT PAYLOADS! " + cmdNum2Name[paramNum])
			payload = np.array(payload, dtype=np.int32)
			payload = payload.byteswap().tobytes()
			
	else:
		if paramNum != cmd_readirqueue and paramNum != 0: 
			logger.debug("sending (" + str(voiceno) + ":" + str(opno) + ") " + cmdNum2Name[paramNum] + " " + str(payload))
		payload = struct.pack(">i", np.int32(payload))
	payload_array = [paramNum, 1 << opno, (voicemode << 7) | (voiceno >> 8), voiceno] + [int(i) for i in payload] 
	#logger.debug(str(payload_array[0]) + ": " + str([hex(p) for p in payload_array[:32]]))
	ret = spi_interface.send(payload_array)
	return ret
	
if __name__ == "__main__":
	fpga_interface_inst = fpga_interface()
	
	#for voiceno in range(fpga_interface_inst.POLYPHONYCOUNT):
	#	for opno in range(fpga_interface_inst.OPERATORCOUNT):
	#		for command in fpga_interface_inst.cmdName2number.keys():
	#			fpga_interface_inst.formatAndSend(command, opno, voiceno, 0)
				
	# run testbench
	
	logger = logging.getLogger('dtfm')
	#formatter = logging.Formatter('{"debug": %(asctime)s {%(pathname)s:%(lineno)d} %(message)s}')
	formatter = logging.Formatter('{{%(pathname)s:%(lineno)d %(message)s}')
	ch = logging.StreamHandler()
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	logger.setLevel(1)
		
	
	def bitrev(n):
		return n
		return int('{:08b}'.format(n)[::-1], 2)
	
	for i in range(1):
		print([hex(bitrev(a)) for a in fpga_interface_inst.getID()])
		#print([hex(bitrev(a)) for a in fpga_interface_inst.getStream(cmd_readaudio)])
		#print([hex(bitrev(a)) for a in fpga_interface_inst.getID()])
		#print([hex(bitrev(a)) for a in fpga_interface_inst.getStream(cmd_readaudio)])
	
	opno = 0
	voiceno = 0
	fpga_interface_inst.formatAndSend("cmd_channelgain_right", opno, voiceno, 2**16)
	fpga_interface_inst.formatAndSend("cmd_gain_rate"      , opno, voiceno, 2**16)
	fpga_interface_inst.formatAndSend("cmd_gain"            , opno, voiceno, 2**16)
	fpga_interface_inst.formatAndSend("cmd_increment_rate" , opno, voiceno, 2**16)
	fpga_interface_inst.formatAndSend("cmd_increment"       , opno, voiceno, 2**22)
	fpga_interface_inst.formatAndSend("cmd_fm_algo"       , opno, voiceno, 1)

	opno = 1
	fpga_interface_inst.formatAndSend("cmd_increment_rate", opno, voiceno, 2**30)
	fpga_interface_inst.formatAndSend("cmd_increment"      , opno, voiceno, 2**22)
	fpga_interface_inst.formatAndSend("cmd_fm_algo"      , opno, voiceno, 2)
	
	fpga_interface_inst.formatAndSend("cmd_flushspi", 0, 0, 0)
	fpga_interface_inst.formatAndSend("cmd_shift"   , 0, 0, 2)
		
