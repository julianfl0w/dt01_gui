import spidev
import struct
maxSpiSpeed = 120000000
spi = spidev.SpiDev()
spi.open(1, 0)
spi.max_speed_hz=maxSpiSpeed
from bitarray import bitarray
import logging
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
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

import logging
import collections
import math
logger = logging.getLogger('DT01')

MIDINOTES      = 128
CONTROLCOUNT   = 128

controlNum2ParamName = [""]*CONTROLCOUNT

# common midi controls https://professionalcomposers.com/midi-cc-list/

# begin voice parameters
controlNum2ParamName[0 ] = "vibrato_env"  # modwheel. tie it to vibrato (Pitch LFO)
controlNum2ParamName[1 ] = "tremolo_env"  # breath control
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
# master class for FPGA elements
class FPGA_component:

	# need to call super.init
	def __init__(self, index, fpga_interface_inst, patch):
		self.patch = patch
		self.allChildren = []
		self.computedState  = dict()
		self.stateInFPGA    = dict()
		self.commonChildrenSensitivities = collections.defaultdict(list)
		self.fpga_interface_inst = fpga_interface_inst
		self.index = index
		
		# DT01-specific sensitivity list
		# if function contains key, add its sensitivity to value
		self.keyword2events = {}
		self.keyword2events["note"]       = ["note_off", "note_on"]
		self.keyword2events["pitchwheel"] = ["pitchwheel"]
		self.keyword2events["aftertouch"] = ["aftertouch"]
		self.keyword2events["polytouch"]  = ["polytouch"]
		for control in range(127):
			#keyword2events["control[" + str(control) + "]"]  = ["control" + str(control)]
			self.keyword2events["control[" + str(control) + "]"]  = ["control[" + str(control) + "]"]
		
		# initialize lists
		self.event2action  = collections.defaultdict(list)
		logger.debug("initialized " + str(self))
		
	def computeDicts(self, recursive = True):
		pass
		#logger.debug("computing dicts " + str(self))
		#self.allChildrenDict = collections.defaultdict(list)
		#self.allChildren = []
		#for membername, member in inspect.getmembers(self):
		#	# sometimes they may be elements of a list
		#	if isinstance(member,list):
		#		for v in member:
		#			if (isinstance(v, FPGA_component)):
		#				#logger.debug("child " + str(v))
		#				self.allChildrenDict[str(type(v))] += [v]
		#				self.allChildren += [v]
		#	
		#	# if its a function starting with fn
		#	#if membername.startswith("fn_") and callable(member):
		#	#	#logger.debug("found function " + membername)
		#	#	for keyword, events in self.keyword2events.items():
		#	#		#logger.debug("kw " + keyword)
		#	#		#logger.debug("events " + str(events))
		#	#		if keyword in inspect.getsource(member):
		#	#			#logger.debug(keyword + ", yeah its in " + str(inspect.getsource(member)))
		#	#			for event in events:
		#	#				#logger.debug("adding " + membername + " to " + event)
		#	#				self.event2action[event] += [(membername.replace("fn_", "cmd_"), member)]
		#	#				
		#	#	# if the function contains no keywords, send it
		#	#	if not any([keyword in inspect.getsource(member) for keyword in self.keyword2events.keys()]):
		#	#		self.computeAndSend((membername.replace("fn_", "cmd_"),member))
		#if recursive:
		#	for child in self.allChildren:
		#		child.computeDicts()
		
		# find common sensitivities in all children of a list
		#logger.debug(self.allChildrenDict.items())
		#for typename, children in self.allChildrenDict.items():
		#	# set of all triggering events
		#	triggeringEvents = [set([str(event) for event in child.event2action.keys()]) for child in children]
		#	logger.debug(str(triggeringEvents))
		#	#commonTriggeringEvents = set.intersection([tset for tset in triggeringEvents])
		#	# One-Liner to intersect a list of sets
		#	commonTriggeringEvents =  triggeringEvents[0].intersection(*triggeringEvents)
		#	logger.debug(str(commonTriggeringEvents))
		#	
		#	self.commonChildrenSensitivities[typename] = commonTriggeringEvents
		#logger.debug("CCC: \n" + str(self.commonChildrenSensitivities))
		
	#def processEvent(self, event, recursive = True):
	#	#logger.debug(str(self) + " processing " + event)
	#	for action in self.event2action[event]:
	#		action()
	#	
	#	if recursive:
	#		for child in self.allChildren:
	#			child.processEvent(event)
			
	def compute(self, param, fn):
		self.computedState[param] = fn()
		
	def computeAndSend(self, action):
		#logger.debug("running action " + str(action))
		param, fn = action
		self.compute(param, fn)
		# only write the thing if it changed
		if self.computedState[param] != self.stateInFPGA.get(param):
			self.send(param)
			self.stateInFPGA[param] = self.computedState[param]
		else:
			#logger.debug("Not sending " + param + " with value " + str(self.computedState[param]))
			pass
			
	def __unicode__(self):
		if self.index != None:
			return str(type(self)) + " #" + str(self.index) 
		else:
			return str(type(self)) + " #" + "ALL"

	def __str__(self):
		return self.__unicode__()
		
	def dumpState(self):
		logger.debug(self)
		logger.debug(json.dumps(self.stateInFPGA, indent = 4))

# heirarchy:
# patch controls
# voice controls
# operator
		
# patch holds all state, including note and control state
class Patch(FPGA_component):


	def fn_env_clkdiv (self) : return self.control[100]
	def fn_flushspi   (self) : return self.control[101]
	def fn_passthrough(self) : return self.control[102]
	def fn_shift      (self) : return self.control[103]
	
	def getVoices(self, controlPatch, voicesToGet = 32):
		toreturn = []
		with ILock('jlock', lock_directory=sys.path[0]):
			for i in range(voicesToGet):
				toreturn += [self.voices[self.voiceno]]
				self.voices[self.voiceno].controlPatch = controlPatch
				self.voiceno += 1
		return toreturn
		
	def send(self, param, value):
		self.fpga_interface_inst.send(param, 0, 0, value)
	
	def processControl(self, paramName, value):
		self.processEvent(mido.Message('control_change', control = paramName2Num [paramName], value = value)) #
		
	
	def __init__(self, fpga_interface_inst):
		logger.debug("patch init ")
		self.fpga_interface_inst  = fpga_interface_inst
		super().__init__(0, self.fpga_interface_inst, self)
		self.polyphony  = 1
				
		self.voicesPerNote = 1
		self.voices = []
		self.currVoiceIndex = 0
		self.currVoice = 0
		self.pitchwheel  = 8192
		self.pitchwheelReal  = 1
		self.aftertouch = 0
		self.aftertouchReal = 0
				
		self.allNotes = []
		for i in range(MIDINOTES):
			self.allNotes+= [Note(i)]
			
		self.voiceno = 0# round robin voice allocation
		
		for i in range(self.polyphony):
			newVoice = Voice(i, self.fpga_interface_inst, self)
			self.voices += [newVoice]

		self.allChildren = self.voices
		self.computeDicts(recursive = False)
	
		for voice in self.voices:
			logger.debug("claimed: " + str(voice.index))
			voice.note  = self.allNotes[0]
			voice.patch = self
				
		self.toRelease   = []
	
		self.control = [0]*CONTROLCOUNT
		self.controlReal = [0]*CONTROLCOUNT

		# establish defaults
		self.paramName2Val = {}
		self.paramName2Real= {}
		for paramName in controlNum2ParamName:
			self.paramName2Val [paramName] = 0
			self.paramName2Real[paramName] = 0
		
		self.processControl("vibrato_env", value = 0) #
		self.processControl("tremolo_env", value = 0) #
		self.processControl( "fbgain"       , value = 0)
		self.processControl( "fbsrc"        , value = 0)
		self.processControl( "baseincrement", value = 127)     # 
		self.processControl( "pan"          , value = 64) # common midi control
		self.processControl( "expression"   , value = 0) # common midi control
		
		self.processControl("opno"            , value = 0) #
		self.processControl( "voicegain"    , value = 127) # common midi control
		self.processControl("opno"            , value = 1) #
		self.processControl( "voicegain"    , value = 127) # common midi control
		
		self.processControl("opno"            , value = 0) #
		self.processControl("env"             , value = 127) #
		self.processControl("env_porta"       , value = 64  ) #
		self.processControl("envexp"          , value = 1  ) #
		self.processControl("increment"       , value = 127) #
		self.processControl("increment_porta" , value = 0  ) #
		self.processControl("incexp"          , value = 1  ) #
		self.processControl("fmsrc"           , value = 7  ) #fm off
		self.processControl("amsrc"           , value = 0  ) #am off
		self.processControl("static"          , value = 0  ) #
		self.processControl("sounding"        , value = 1  ) #
		
		self.processControl("opno"            , value = 1) #
		self.processControl("env"             , value = 0) #
		self.processControl("env_porta"       , value = 0  ) #
		self.processControl("envexp"          , value = 1  ) #
		self.processControl("increment"       , value = 0) #
		self.processControl("increment_porta" , value = 0  ) #
		self.processControl("incexp"          , value = 1  ) #
		self.processControl("fmsrc"           , value = 7  ) #fm off
		self.processControl("amsrc"           , value = 0  ) #am off
		self.processControl("static"          , value = 0  ) #
		self.processControl("sounding"        , value = 0  ) #
		
		self.processControl("opno"            , value = 2) #
		self.processControl("env"             , value = 0) #
		self.processControl("env_porta"       , value = 0  ) #
		self.processControl("envexp"          , value = 1  ) #
		self.processControl("increment"       , value = 0) #
		self.processControl("increment_porta" , value = 0  ) #
		self.processControl("incexp"          , value = 1  ) #
		self.processControl("fmsrc"           , value = 7  ) #fm off
		self.processControl("amsrc"           , value = 0  ) #am off
		self.processControl("static"          , value = 0  ) #
		self.processControl("sounding"        , value = 0  ) #
		
		self.processControl("opno"            , value = 3) #
		self.processControl("env"             , value = 0) #
		self.processControl("env_porta"       , value = 0  ) #
		self.processControl("envexp"          , value = 1  ) #
		self.processControl("increment"       , value = 0) #
		self.processControl("increment_porta" , value = 0  ) #
		self.processControl("incexp"          , value = 1  ) #
		self.processControl("fmsrc"           , value = 7  ) #fm off
		self.processControl("amsrc"           , value = 0  ) #am off
		self.processControl("static"          , value = 0  ) #
		self.processControl("sounding"        , value = 0  ) #
		
		self.processControl("opno"            , value = 4) #
		self.processControl("env"             , value = 0) #
		self.processControl("env_porta"       , value = 0  ) #
		self.processControl("envexp"          , value = 1  ) #
		self.processControl("increment"       , value = 0) #
		self.processControl("increment_porta" , value = 0  ) #
		self.processControl("incexp"          , value = 1  ) #
		self.processControl("fmsrc"           , value = 7  ) #fm off
		self.processControl("amsrc"           , value = 0  ) #am off
		self.processControl("static"          , value = 0  ) #
		self.processControl("sounding"        , value = 0  ) #
		
		self.processControl("opno"            , value = 5) #
		self.processControl("env"             , value = 0) #
		self.processControl("env_porta"       , value = 0  ) #
		self.processControl("envexp"          , value = 1  ) #
		self.processControl("increment"       , value = 0) #
		self.processControl("increment_porta" , value = 0  ) #
		self.processControl("incexp"          , value = 1  ) #
		self.processControl("fmsrc"           , value = 7  ) #fm off
		self.processControl("amsrc"           , value = 0  ) #am off
		self.processControl("static"          , value = 0  ) #
		self.processControl("sounding"        , value = 0  ) #
		
		self.processControl("opno"            , value = 6) #
		self.processControl("env"             , value = 0) #
		self.processControl("env_porta"       , value = 0  ) #
		self.processControl("envexp"          , value = 1  ) #
		self.processControl("increment"       , value = 0) #
		self.processControl("increment_porta" , value = 0  ) #
		self.processControl("incexp"          , value = 1  ) #
		self.processControl("fmsrc"           , value = 7  ) #fm off
		self.processControl("amsrc"           , value = 0  ) #am off
		self.processControl("static"          , value = 0  ) #
		self.processControl("sounding"        , value = 0  ) #
		
		self.processControl("opno"            , value = 7) #
		self.processControl("env"             , value = 0) #
		self.processControl("env_porta"       , value = 0  ) #
		self.processControl("envexp"          , value = 1  ) #
		self.processControl("increment"       , value = 0) #
		self.processControl("increment_porta" , value = 0  ) #
		self.processControl("incexp"          , value = 1  ) #
		self.processControl("fmsrc"           , value = 7  ) #fm off
		self.processControl("amsrc"           , value = 0  ) #am off
		self.processControl("static"          , value = 0  ) #
		self.processControl("sounding"        , value = 0  ) #
		
		# common midi controls
		self.processControl("sustain"         , value = 0)# common midi control
		self.processControl("portamento"      , value = 0)# common midi control
		self.processControl("filter_resonance", value = 0)# common midi control
		self.processControl("filter_cutoff"   , value = 0)# common midi control

		self.processControl("env_clkdiv"      , value = 8) #   
		self.processControl("flushspi"        , value = 0) #   
		self.processControl("passthrough"     , value = 0) #   
		self.processControl("shift"           , value = 2) #   
					
		self.processEvent(mido.Message('pitchwheel', pitch = 64))
		self.processEvent(mido.Message('aftertouch', value = 0))
		for note in self.allNotes:
			self.processEvent(mido.Message('polytouch', note = note.index, value = 0))
			
		self.processEvent(mido.Message('control_change', control = 114, value = 0)) #
	
	def getCtrlString(self, ctrlName):
		return "control[" + str(int(paramName2Num[ctrlName])) + "]"
	
	def processEvent(self, msg):
	
		#logger.debug("processing " + msg.type)
		voices = self.voices
			
		msgtype = msg.type
		voicesToUpdate = self.voices
		event = msg.type
		
		if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
			note = self.allNotes[msg.note] 
			note.velocity = 0 
			note.velocityReal = 0 
			voicesToUpdate = note.voices.copy()
			note.voices = []
			note.held = False
			
				
		elif msg.type == "note_on":
			note = self.allNotes[msg.note]
			note.velocity = msg.velocity
			note.velocityReal = msg.velocity/127.0
			note.held = True
			note.msg = msg
			# spawn some voices!
			for voiceno in range(self.voicesPerNote):
				self.currVoiceIndex = (self.currVoiceIndex + 1) % self.polyphony
				self.currVoice = self.voices[self.currVoiceIndex]
				self.currVoice.indexInCluser = voiceno
				self.currVoice.note = note
				note.voices += [self.currVoice]
			voicesToUpdate = note.voices
			self.processEvent(mido.Message('control_change', control = 114, value = 0)) #
				
		elif msg.type == 'pitchwheel':
			logger.debug("PW: " + str(msg.pitch))
			self.pitchwheel = msg.pitch
			amountchange = msg.pitch / 8192.0
			self.pitchwheelReal = pow(2, amountchange)
			logger.debug("PWREAL " + str(self.pitchwheelReal))
				
		elif msg.type == 'control_change':
		
			logger.debug("control : " + str(msg.control) + " (" + controlNum2ParamName[msg.control] +  "): " + str(msg.value))
			self.control[msg.control]     = msg.value
			self.controlReal[msg.control] = msg.value/127.0
			self.paramName2Val [controlNum2ParamName[msg.control]] = msg.value
			self.paramName2Real[controlNum2ParamName[msg.control]] = msg.value/127.0
			event = "control[" + str(msg.control) + "]"
			
			# forward some controls
			# PUT THIS BACK
			
			#if msg.control == 0:
			#	self.processEvent(mido.Message('control_change', control= paramName2Num["opno"      ], value = 6 ))
			#	self.processEvent(mido.Message('control_change', control= paramName2Num["env"      ], value = msg.value ))
			#if msg.control == 1:
			#	self.processEvent(mido.Message('control_change', control= paramName2Num["opno"      ], value = 7 ))
			#	self.processEvent(mido.Message('control_change', control= paramName2Num["env"      ], value = msg.value ))
				
			# route control3 to control 7 because sometimes 3 is volume control
			if msg.control == 3:
				self.processEvent(mido.Message('control_change', control= 7, value = msg.value ))
				
			if msg.control == paramName2Num["env_clkdiv"]:
				self.send("cmd_env_clkdiv" , self.paramName2Val["env_clkdiv"])
				
			if msg.control == paramName2Num["flushspi"]:
				self.send("cmd_flushspi", self.paramName2Val["flushspi"])
				
			if msg.control == paramName2Num["passthrough"]:
				self.send("cmd_passthrough", self.paramName2Val["passthrough"])
				
			if msg.control == paramName2Num["shift"]:
				self.send("cmd_shift" , self.paramName2Val["shift"])
				
			if msg.control == 114:
				logger.debug(self.stateInFPGA)
						
			
		elif msg.type == 'polytouch':
			self.allNotes[msg.note].polytouch = msg.value/127.0
			note = self.allNotes[msg.note]
			voicesToUpdate = note.voices
			
		elif msg.type == 'aftertouch':
			self.aftertouch = msg.value
			self.aftertouchReal = msg.value/127.0
						
		
		for voice in voicesToUpdate:
			#logger.debug("\n\n------------------\nselecting voice " + str(voice.index))
			voice.processEvent(msg)

		if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
			# implement rising mono porta
			for heldnote in self.allNotes[::-1]:
				if heldnote.held and self.polyphony == self.voicesPerNote :
					self.processEvent(heldnote.msg)
					break
			self.processEvent(mido.Message('control_change', control = 114, value = 0)) #
					
		

def noteToFreq(note):
	a = 440.0 #frequency of A (coomon value is 440Hz)
	return (a / 32) * (2 ** ((note - 9) / 12))

class Note:
	def __init__(self, index):
		self.index  = index
		self.voices = []
		self.velocity = 0
		self.velocityReal = 0
		self.held  = False
		self.polytouch = 0
		self.msg  = None
		self.defaultIncrement = 2**18 * (noteToFreq(index) / 96000.0)
		
class Voice(FPGA_component):
		
	def __init__(self, index, fpga_interface_inst, patch):
		super().__init__(index, fpga_interface_inst, patch)
		
	
		self.index = index
		self.note = None
		self.patch  = None
		self.sounding = False    
		self.defaultIncrement = 0
		self.indexInCluster = 0
		self.OPERATORCOUNT  = 8
		self.operators = []
		for opindex in range(self.OPERATORCOUNT):
			self.operators += [Operator(self, opindex, fpga_interface_inst, patch)]
		
		self.channels = []
		self.channels += [Channel(self, 0, fpga_interface_inst, patch)]
		self.channels += [Channel(self, 1, fpga_interface_inst, patch)]
		
		self.allChildren = self.channels + self.operators 
			
	def processEvent(self, msg):
	
		# first, update the children
		for child in self.allChildren:
			child.processEvent(msg)
			
		# base increment
		if msg.type == "note_on" or msg.type == "pitchwheel" or (msg.type == "control_change" and msg.control == paramName2Num["baseincrement"] and \
			self.patch.paramName2Val["opno"] == self.index) or msg.type == "aftertouch": 
			# send the base increment
			logger.debug(str(self.patch.paramName2Real["baseincrement"]) + " " + str(self.patch.pitchwheelReal) + " " + str(1 + self.patch.aftertouchReal) + " " +  str(self.note.defaultIncrement))
			self.send("cmd_baseincrement", self.patch.paramName2Real["baseincrement"] * self.patch.pitchwheelReal * (1 + self.patch.aftertouchReal) * self.note.defaultIncrement)
		
		# on control change
		if (msg.type == "control_change"):
			# FM Algo
			if msg.control == paramName2Num["fmsrc"]:
				sendVal = 0
				for i in reversed(range(self.OPERATORCOUNT)):
					sendVal = int(sendVal) << int(math.log2(self.OPERATORCOUNT))
					sendVal += int(self.operators[i].fmsrc)
					#logger.debug(bin(sendVal))
				self.send("cmd_fm_algo", sendVal)
			
			#am algo
			if msg.control == paramName2Num["amsrc"]:
				sendVal = 0
				for i in reversed(range(self.OPERATORCOUNT)):
					sendVal = int(sendVal) << int(math.log2(self.OPERATORCOUNT))
					sendVal += int(self.operators[i].amsrc)
					#logger.debug(bin(sendVal))
				self.send("cmd_am_algo", sendVal)
				
			if msg.control == paramName2Num["fbgain"]:
				self.send("cmd_fbgain"   , 2**16 * self.patch.paramName2Real["fbgain"]  )
				
			if msg.control == paramName2Num["fbsrc"]:
				self.send("cmd_fbsrc"    , self.patch.paramName2Val["fbsrc"]   )
	
			if msg.control == paramName2Num["sounding"]: 
				sendVal = 0
				for i in reversed(range(self.OPERATORCOUNT)):
					sendVal = int(sendVal) << 1
					sendVal += int(self.operators[i].sounding)
					#logger.debug(bin(sendVal))
				self.send("cmd_sounding", sendVal)
				
			if msg.control == paramName2Num["static"]: 
				sendVal = 0
				for i in reversed(range(self.OPERATORCOUNT)):
					sendVal = int(sendVal) << 1
					sendVal += int(self.operators[i].static)
				self.send("cmd_static", sendVal)
	
			if msg.control == 114:
				logger.debug(str(self) + " STATE :")
				logger.debug(self.stateInFPGA)
						
	def send(self, param, value):
		#if self.stateInFPGA.get(param) != value:
		if True: # better for debugging
			self.fpga_interface_inst.send(param, 0, self.index, value)
		self.stateInFPGA[param] = value


class Channel(FPGA_component):
	def __init__(self, voice, index, fpga_interface_inst, patch):
		super().__init__(index, fpga_interface_inst, patch)
		self.voice = voice
		self.fpga_interface_inst = fpga_interface_inst
		self.selected = False
		
	# control 7 = volume, 10 = pan
	def processEvent(self, msg):
		# on control change
		if msg.type == "control_change":
		
			# selection
			if msg.control == paramName2Num["opno"]:
				if msg.value == self.index:
					logger.debug("\n\n------------------\nselecting channel " + str(self.index))
					self.selected = True
				else:
					self.selected = False
					
			if self.selected:
				if msg.control == paramName2Num["voicegain"] or msg.control == paramName2Num["pan"] : 
					baseVolume = 2**16*self.patch.paramName2Real["voicegain"]
					if self.index == 0:
						self.send("cmd_voicegain", baseVolume*self.patch.paramName2Real["pan"]) # assume 2 channels
					else:
						#logger.debug(self.patch.controlReal[10])
						self.send("cmd_voicegain", baseVolume*(1 - self.patch.paramName2Real["pan"])) # assume 2 channels
	
			if msg.control == 114:
				logger.debug(str(self) + " STATE :")
				logger.debug(self.stateInFPGA)
							
	def send(self, param, value):
		#if self.stateInFPGA.get(param) != value:
		if True: # better for debugging
			self.fpga_interface_inst.send(param, self.index, self.voice.index, value)
		self.stateInFPGA[param] = value
		

# OPERATOR DESCRIPTIONS
class Operator(FPGA_component):
	def __init__(self, voice, index, fpga_interface_inst, patch):
		self.voice = voice
		super().__init__(index, fpga_interface_inst, patch)
		self.base  = OPBASE[self.index]
		self.sounding = 0
		self.fmsrc    = 7
		self.amsrc    = 0
		self.static   = 0 
		self.selected = False
		
		# establish defaults
		self.paramName2Val = {}
		self.paramName2Real= {}
		for paramName in controlNum2ParamName:
			self.paramName2Val [paramName] = 0
			self.paramName2Real[paramName] = 0
			
	def processEvent(self, msg):
		if msg.type == "note_on" or msg.type == "note_off":
			if (self.voice.stateInFPGA.get("cmd_static") is not None and (int(self.voice.stateInFPGA.get("cmd_static")) & (1 << self.index))):
				self.send("cmd_env"            , (2**16) * self.paramName2Real["env"]               )
			else:
				self.send("cmd_env"            , self.voice.note.velocityReal * (2**16) * self.paramName2Real["env"])

		# on control change
		if msg.type == "control_change":
		
			if msg.control == 114:
				logger.debug(str(self) + " STATE :")
				logger.debug(self.stateInFPGA)
				
			# selection
			if msg.control == paramName2Num["opno"]:
				if msg.value == self.index:
					logger.debug("\n\n------------------\nselecting opno " + str(self.index))
					#if self.index == 7:
					#	logger.debug(print(sys.exc_info()[2]))
					#	traceback.print_stack()
					self.selected = True
				else:
					self.selected = False
				
			if self.selected:
				self.paramName2Val [controlNum2ParamName[msg.control]] = msg.value
				self.paramName2Real[controlNum2ParamName[msg.control]] = msg.value/127.0
					
				if msg.control == paramName2Num["env"]: 
					self.send("cmd_env"            , self.voice.note.velocityReal * (2**16) * self.paramName2Real["env"])
						
				if msg.control == paramName2Num["env_porta"]: 
					self.send("cmd_env_porta"      , 2**12 * (1 - self.paramName2Real["env_porta"]) * (1 - self.patch.paramName2Real["portamento"]) )
		# static oscillators do not have velocity-dependant env
					
				if msg.control == paramName2Num["increment"]: 
					self.send("cmd_increment"      , 2**16 * self.paramName2Real["increment"]) # * self.paramName2Real["increment"]
					
				if msg.control == paramName2Num["increment_porta"]: 
					self.send("cmd_increment_porta", 2**12 * (1 - self.patch.paramName2Real["portamento"]) * (1 - self.paramName2Real["increment_porta"]))
					
				if msg.control == paramName2Num["incexp"]: 
					self.send("cmd_incexp"         , self.patch.paramName2Val["incexp"])  
					
				if msg.control == paramName2Num["envexp"]: 
					self.send("cmd_envexp"         , self.patch.paramName2Val["envexp"])
					
				if msg.control == paramName2Num["fmsrc"]: 
					self.fmsrc = self.paramName2Val["fmsrc"]
					
				if msg.control == paramName2Num["amsrc"]:
					self.amsrc  = self.paramName2Val["amsrc"]
					
				if msg.control == paramName2Num["static"]:
					self.static = self.paramName2Val["static"]
					
				if msg.control == paramName2Num["sounding"]:
					self.sounding = self.paramName2Val["sounding"]
					
							
				
	def send(self, param, value):
		#if self.stateInFPGA.get(param) != value:
		if True: # better for debugging
			self.fpga_interface_inst.send(param, self.index, self.voice.index, value)
		self.stateInFPGA[param] = value

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
	cmdName2number["cmd_voicegain"]      = 75
	cmdName2number["cmd_env"            ] = 76 
	cmdName2number["cmd_env_porta"      ] = 77 
	cmdName2number["cmd_envexp"         ] = 78 
	cmdName2number["cmd_increment"      ] = 79 
	cmdName2number["cmd_increment_porta"] = 80  
	cmdName2number["cmd_incexp"         ] = 81
	cmdName2number["cmd_flushspi"         ] = 120
	cmdName2number["cmd_passthrough"      ] = 121
	cmdName2number["cmd_shift"            ] = 122
	cmdName2number["cmd_env_clkdiv"       ] = 99 # turn this back to 123
		
	def __init__(self):
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
		packstring = ">" + str(int(len(payload)/4)) + "I"
		payload = np.array(payload, dtype=np.int)
		payload_packed = struct.pack(packstring, *payload)
		tosend = self.format_command_int(self.cmdName2number[paramName], opno, voiceno, 0)
		with ILock('jlock', lock_directory=sys.path[0]):
			logger.debug("tslen: " + str(len(tosend[:4])))
			spi.xfer2(tosend[:4] + payload_packed)
			#logger.debug("sent")
	
	def send(self, paramName, mm_opno,  voiceno,  payload):
		tosend = self.format_command_int(self.cmdName2number[paramName], mm_opno, voiceno, payload)
		with ILock('jlock', lock_directory=sys.path[0]):
			logger.debug("sending " + paramName + "(" + str(self.cmdName2number[paramName]) + ")" + " operator:" + str(mm_opno) + " voice:" + str(voiceno) + " payload:" + str(payload))
			#logger.debug(tosend)
			spi.xfer2(tosend)
			#logger.debug("sent")
		
if __name__ == "__main__":
	fpga_interface_inst = fpga_interface_inst()
	
	#for voiceno in range(fpga_interface_inst.POLYPHONYCOUNT):
	#	for opno in range(fpga_interface_inst.OPERATORCOUNT):
	#		for command in fpga_interface_inst.cmdName2number.keys():
	#			fpga_interface_inst.send(command, opno, voiceno, 0)
				
	# run testbench
	fpga_interface_inst.send("cmd_env_clkdiv", 0, 0, 0)
	
	opno = 0
	voiceno = 0
	fpga_interface_inst.send("cmd_voicegain_right", opno, voiceno, 2**16)
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
		