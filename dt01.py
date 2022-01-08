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

logger = logging.getLogger('DT01')

MIDINOTES      = 128
CONTROLCOUNT   = 128
OPERATORCOUNT  = 8
SOUNDINGOPS    = 6
SOUNDINGOPS    = 1

controlNum2Name = [""]*CONTROLCOUNT

# common midi controls https://professionalcomposers.com/midi-cc-list/

# begin voice parameters
controlNum2Name[0 ] = "ctrl_vibrato_env"  # modwheel. tie it to vibrato (Pitch LFO)
controlNum2Name[1 ] = "ctrl_tremolo_env"  # breath control
controlNum2Name[4 ] = "ctrl_fbgain"         
controlNum2Name[5 ] = "ctrl_fbsrc"          

controlNum2Name[7 ] = "ctrl_voicegain"       # common midi control
controlNum2Name[10] = "ctrl_pan"             # common midi control
controlNum2Name[11] = "ctrl_expression"      # common midi control


OPBASE = [0]*8
# begin operator parameters
controlNum2Name[13] = "ctrl_opno"            
OPBASE[0]  = 14
controlNum2Name[14] = "ctrl_env"            
controlNum2Name[15] = "ctrl_env_rate"      
controlNum2Name[17] = "ctrl_increment"      
controlNum2Name[18] = "ctrl_increment_rate"
controlNum2Name[20] = "ctrl_fmsrc"         
controlNum2Name[21] = "ctrl_amsrc"         
controlNum2Name[23] = "ctrl_sounding"         
   

# common midi controls
controlNum2Name[64] = "ctrl_sustain"         # common midi control
controlNum2Name[65] = "ctrl_ratemento"      # common midi control
controlNum2Name[71] = "ctrl_filter_resonance"# common midi control
controlNum2Name[74] = "ctrl_filter_cutoff"   # common midi control


# begin global params
controlNum2Name[111] = "ctrl_flushspi"       
controlNum2Name[112] = "ctrl_passthrough"    
controlNum2Name[113] = "ctrl_shift"          

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

def DT01_fromFile(filename):
	with open(filename, 'rb') as f:
		return pickle.load(f)

class DT01():

	def toFile(self, filename):
		with open(filename, 'wb+') as f:
			pickle.dump(self, f)
	
	def __init__(self, polyphony = 512):
		
		self.voices = 0
		self.polyphony = polyphony
		self.voicesPerPatch = min(self.polyphony, 64)
		self.patchesPerDT01 = int(round(self.polyphony / self.voicesPerPatch))
		self.voices = []
		self.voiceSets = []
		self.loanTime = [0]*self.patchesPerDT01
		self.maxPhaseCount = 10 # we store in memory up to 100 phases
		
		index = 0
		for i in range(self.patchesPerDT01):
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
	
	def setAllIncrements(self, modifier, lowestVoice, polyphony):
		# no way to avoid casting it seems
		logger.debug(self.baseIncrement   [lowestVoice.index:lowestVoice.index+polyphony])
		logger.debug(self.incrementScale  [lowestVoice.index:lowestVoice.index+polyphony])
		logger.debug(self.defaultIncrement[lowestVoice.index:lowestVoice.index+polyphony])
		logger.debug(modifier)
		self.tosend = (self.baseIncrement   [lowestVoice.index:lowestVoice.index+polyphony] + \
				 self.incrementScale  [lowestVoice.index:lowestVoice.index+polyphony] * \
				 self.defaultIncrement[lowestVoice.index:lowestVoice.index+polyphony] * modifier).astype(np.int32, copy = False)
		for op in lowestVoice.operators:
			op.formatAndSend(cmd_increment, self.tosend[:, op.index], voicemode = True)
	
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
	
		
class Voice():
		
	def __init__(self, index, dt01_inst):
		self.dt01_inst = dt01_inst
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
			self.operators += [Operator(self, opindex, dt01_inst)]
		
		self.channels = []
		self.channels += [Channel(self, 0)]
		self.channels += [Channel(self, 1)]
		
		self.allChildren = self.channels + self.operators 
		self.allIncrements = np.zeros((OPERATORCOUNT), dtype=np.int32)
	
		# state info
		self.envLevelAbsolute = np.zeros((self.dt01_inst.maxPhaseCount, OPERATORCOUNT), dtype=np.int32)
		self.envRatePerSample      = np.zeros((self.dt01_inst.maxPhaseCount, OPERATORCOUNT), dtype=np.int32)
		self.envTimeSeconds        = np.zeros((self.dt01_inst.maxPhaseCount, OPERATORCOUNT), dtype=np.float)
		self.envTimeSamples        = np.zeros((self.dt01_inst.maxPhaseCount, OPERATORCOUNT), dtype=np.int32)
		self.envStepAbsolute       = np.zeros((self.dt01_inst.maxPhaseCount, OPERATORCOUNT), dtype=np.int32)
	
	def setupOps(self, patchDict, sounding0indexed):
		for operator in self.operators:
			opDict = patchDict["Operator" + str(operator.index+1)]
			operator.setup(opDict, sounding0indexed)

	def setAllIncrements(self, modifier):
		for op in self.operators:
			logger.debug(modifier)
			self.allIncrements[op.index] = min(op.baseIncrement + op.incrementScale * op.voice.note.defaultIncrement * modifier, 2**30)
		self.formatAndSend(cmd_increment, self.allIncrements[:SOUNDINGOPS], voicemode = False)
	
	def setPhaseAllOps(self, phase):
		self.formatAndSend(cmd_env_rate, self.opZeros[:SOUNDINGOPS], voicemode=False)                               
		self.formatAndSend(cmd_env,      self.envLevelAbsolute[phase,:SOUNDINGOPS], voicemode=False)
		self.formatAndSend(cmd_env_rate, self.envRatePerSample[phase,:SOUNDINGOPS], voicemode=False)                           
		for op in self.operators:
			op.envelopePhase = phase
		
		return 0
		
	def silenceAllOps(self):              
		phases = []
		for op in self.operators:
			op.envelopePhase = op.phaseCount - 1
			phases += [op.envelopePhase]
		self.formatAndSend(cmd_env_rate, self.opZeros[:SOUNDINGOPS], voicemode=False)
		self.formatAndSend(cmd_env,      self.opZeros[:SOUNDINGOPS], voicemode=False)
		self.formatAndSend(cmd_env_rate, np.maximum(np.ones((6), dtype = np.int32), self.envStepAbsolute[phases[:SOUNDINGOPS],:SOUNDINGOPS]), voicemode=False)        
		
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
		self.formatAndSend(dt01.cmd_fm_algo, getFMAlgo(algo))
	
	def setAMSrc(self, opno, source):
		self.operators[opno].amsrc = source
		formatAndSendVal = 0
		for i in reversed(range(dt01.OPERATORCOUNT)):
			formatAndSendVal = int(formatAndSendVal) << 4
			formatAndSendVal += int(voice.operators[i].amsrc)
			#logger.debug(bin(formatAndSendVal))
		voice.formatAndSend(dt01.cmd_am_algo, formatAndSendVal)
		
	def applySounding(self, isSounding):
		formatAndSendVal = 0
		for i in reversed(range(dt01.OPERATORCOUNT)):
			formatAndSendVal = int(formatAndSendVal) << 1
			formatAndSendVal += int(voice.operators[i].sounding)
			#logger.debug(bin(formatAndSendVal))
		voice.formatAndSend(dt01.cmd_sounding, formatAndSendVal)
	
	def formatAndSend(self, param, value, voicemode = False):
		return formatAndSend(param, self.index, 0, value, voicemode)


class Channel():
	def __init__(self, voice, index):
		self.index = index
		self.voice = voice
		self.selected = False
		
	def formatAndSend(self, param, value):
		return formatAndSend(param, self.voice.index, self.index, value)
		
# OPERATOR DESCRIPTIONS
class Operator():
	def __init__(self, voice, index, dt01_inst):
		self.dt01_inst = dt01_inst
		self.index = index
		self.voice = voice
		self.base  = OPBASE[self.index]
		self.sounding = 1
		self.fmsrc    = 7
		self.amsrc    = 0
		self.selected = False
		self.baseIncrement = 0
		self.incrementScale = 1
		self.phaseCount     = 4
		
		self.envLevelAbsolute      = np.zeros((dt01_inst.maxPhaseCount), dtype=np.int32)
		self.envRatePerSample      = np.zeros((dt01_inst.maxPhaseCount), dtype=np.int32)
		self.envTimeSeconds        = np.zeros((dt01_inst.maxPhaseCount), dtype=np.float)
		self.envTimeSamples        = np.zeros((dt01_inst.maxPhaseCount), dtype=np.int32)
		self.envStepAbsolute       = np.zeros((dt01_inst.maxPhaseCount), dtype=np.int32)
		self.envelopePhase         = 3
		
	def formatAndSend(self, param, value, voicemode = False):
		return formatAndSend(param, self.voice.index, self.index, value, voicemode=voicemode)
	
	def freqSetup(self, opDict):
		if opDict["Oscillator Mode"] == "Frequency (Ratio)":
			self.baseIncrement  = 0
			self.incrementScale = opDict["Frequency"] * (1 + (opDict["Detune"] / 7.0) / 80)
			
		else:
			self.baseIncrement  = (2**32)*opDict["Frequency"] / SamplesPerSecond
			self.incrementScale = 0
				
		self.dt01_inst.baseIncrement [self.voice.index, self.index] = self.baseIncrement 
		self.dt01_inst.incrementScale[self.voice.index, self.index] = self.incrementScale
			
	
	def dx7setup(self, opDict, sounding0indexed):
	
		self.dt01_inst.phaseCount = 4 # always 4 phases with DX7 Patches
		self.freqSetup(opDict)
		
		self.envelopePhase = 3
		self.sounding = 1 if self.index in sounding0indexed else 0
			
		#https://github.com/google/music-synthesizer-for-android/blob/f67d41d313b7dc85f6fb99e79e515cc9d208cfff/app/src/main/jni/env.cc
		levellut = [0, 5, 9, 13, 17, 20, 23, 25, 27, 29, 31, 33, 35, 37, 39, 41, 42, 43, 45, 46]
		outlevel = opDict["Output Level"]
		if outlevel >= 20:
			self.outputLevelReal = 28 + outlevel
		else:
			self.outputLevelReal = levellut[outlevel];
		self.outputLevelReal /= 128.0
		
		maxSeconds = 10 # gets multiplied again by 4 if its a release (as opposed to attack)
		gamma = 4
		
		envDict = opDict["Envelope Generator"]
		if envDict["Rate 4"] == 0:
			envDict["Rate 4"] = 1
		
		for phase in range(4):
			self.setDx7EnvTimeSecondsAndLevelReal(sounding0indexed, phase, maxSeconds*pow(1-(envDict["Rate " + str(1+phase)]/127.0), gamma), self.outputLevelReal * (envDict["Level " + str(1+phase)]/127.0))
	
	def setEnvs2(self, phase):
		
		self.envTimeSamples   = self.envTimeSeconds * SamplesPerSecond
		self.envStepAbsolute  = np.abs(self.envLevelAbsolute - self.envLevelAbsolute[(phase+self.dt01_inst.phaseCount-1) % self.dt01_inst.phaseCount])
		# if new level is too close to old level, set to the smallest increase that makes time
		lastPhase = (phase + self.dt01_inst.phaseCount -1) % self.dt01_inst.phaseCount
		if abs(self.envLevelAbsolute - self.envLevelAbsolute[lastPhase]) < self.envTimeSamples:
			self.envLevelAbsolute = self.envLevelAbsolute[lastPhase] + self.envTimeSamples
			self.envStepAbsolute  = np.abs(self.envLevelAbsolute - self.envLevelAbsolute[(phase+self.dt01_inst.phaseCount-1) % self.dt01_inst.phaseCount])
			self.envRatePerSample = 1
		else:
			self.envRatePerSample = self.envStepAbsolute / self.envTimeSamples # scale the envelope rate to the difference between this step and the next
		
		# update dt01 array
		self.voice.envLevelAbsolute[self.index] = self.envLevelAbsolute
		self.voice.envRatePerSample     [self.index] = self.envRatePerSample     
		self.voice.envTimeSeconds       [self.index] = self.envTimeSeconds       
		self.voice.envTimeSamples       [self.index] = self.envTimeSamples       
		self.voice.envStepAbsolute      [self.index] = self.envStepAbsolute      
		
	
	def setEnvs(self, opDict):
		self.phaseCount = len(opDict["Time (seconds)"])
		self.envTimeSeconds       [:self.phaseCount] = opDict["Time (seconds)"]
		logger.debug(np.multiply(opDict["Level (unit interval)"], 2**29))
		logger.debug(self.envLevelAbsolute[:self.phaseCount])
		self.envLevelAbsolute[:self.phaseCount] = np.multiply(opDict["Level (unit interval)"], 2**29)
		self.envelopePhase = self.phaseCount- 1
		self.finalPhase = self.phaseCount- 1
		
		self.envTimeSamples   = self.envTimeSeconds * SamplesPerSecond
		logger.debug(self.envLevelAbsolute)
		logger.debug(np.roll(self.envLevelAbsolute, -1, axis = 0))
		j = 0
		# if new level is too close to old level, set to the smallest increase that makes time
		while sum(abs(self.envStepAbsolute) >= self.envTimeSamples):
			logger.debug("Adj " + str(j))
			j+=1
			envPreviousLevel      = np.roll(self.envLevelAbsolute, -1, axis = 0)
			self.envStepAbsolute  = np.abs(self.envLevelAbsolute - envPreviousLevel)
			envMinimumLevelHigh           = envPreviousLevel + self.envTimeSamples
			envMinimumLevelLow            = envPreviousLevel - self.envTimeSamples
			tooCloseGoingUp   = self.envLevelAbsolute < envMinimumLevelHigh
			tooCloseGoingDown = self.envLevelAbsolute > envMinimumLevelLow
			self.envLevelAbsolute = np.where(tooCloseGoingUp,   envMinimumLevelHigh, self.envLevelAbsolute)
			self.envLevelAbsolute = np.where(tooCloseGoingDown, envMinimumLevelLow , self.envLevelAbsolute)
			self.envRatePerSample = np.where(tooCloseGoingUp,    1, self.envRatePerSample)
			self.envRatePerSample = np.where(tooCloseGoingDown, -1, self.envRatePerSample)

		logger.debug("Finished adjustments")
		
		# update dt01 array
		self.voice.envLevelAbsolute[self.index] = self.envLevelAbsolute
		self.voice.envRatePerSample     [self.index] = self.envRatePerSample     
		self.voice.envTimeSeconds       [self.index] = self.envTimeSeconds       
		self.voice.envTimeSamples       [self.index] = self.envTimeSamples       
		self.voice.envStepAbsolute      [self.index] = self.envStepAbsolute      
		
		
		
	def setup(self, opDict, sounding0indexed):
	
		self.sounding = 1 if self.index in sounding0indexed else 0
		self.freqSetup(opDict)
		self.setEnvs(opDict)
	

	def setSounding(self, sounding):
		self.sounding = isSounding
		self.voice.applySounding() # need to update by voice because of memory layout in FPGA
		
	def setDx7EnvTimeSecondsAndLevelReal(self, sounding, phase, timeSeconds, levelReal):
	
		opno = self.index
		# sounding vs nonsounding difference?
		if opno in sounding:
			self.envLevelAbsolute = levelReal*(2**31)
		else:
			self.envLevelAbsolute = levelReal*(2**31)
			
		# Falling env is 4x slower than rising
		if self.envLevelAbsolute > self.envLevelAbsolute[(phase+self.dt01_inst.phaseCount-1) % self.dt01_inst.phaseCount]:
			timeSeconds *= 4
			
		#clip
		self.envTimeSeconds   = max(0.005, timeSeconds)
		self.setEnvs2()
		
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
		payload = struct.pack(">I", int(payload))
	payload_array = [paramNum, 1 << opno, (voicemode << 7) | (voiceno >> 8), voiceno] + [int(i) for i in payload] 
	logger.debug(str(payload_array[0]) + ": " + str([hex(p) for p in payload_array[:32]]))
	ret = spi_interface.send(payload_array)
	return ret
	
if __name__ == "__main__":
	fpga_interface_inst = fpga_interface()
	
	#for voiceno in range(fpga_interface_inst.POLYPHONYCOUNT):
	#	for opno in range(fpga_interface_inst.OPERATORCOUNT):
	#		for command in fpga_interface_inst.cmdName2number.keys():
	#			fpga_interface_inst.formatAndSend(command, opno, voiceno, 0)
				
	# run testbench
	
	logger = logging.getLogger('DT01')
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
		