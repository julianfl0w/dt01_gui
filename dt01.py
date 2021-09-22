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
logger = logging.getLogger('DT01')

MIDINOTES      = 128
CONTROLCOUNT   = 128

controlNum2Name = [""]*CONTROLCOUNT

# common midi controls https://professionalcomposers.com/midi-cc-list/

# begin voice parameters
controlNum2Name[0 ] = "vibrato_env"  # modwheel. tie it to vibrato (Pitch LFO)
controlNum2Name[1 ] = "tremolo_env"  # breath control
controlNum2Name[2 ] = "algorithm"
controlNum2Name[3 ] = "voicegain"        
controlNum2Name[4 ] = "fbgain"         
controlNum2Name[5 ] = "fbsrc"          

controlNum2Name[7 ]  = "voicegain"       # common midi control
controlNum2Name[9 ]  = "baseincrement"       # 
controlNum2Name[10] = "pan"             # common midi control
controlNum2Name[11] = "expression"      # common midi control


OPBASE = [0]*8
# begin operator parameters
OPBASE[0]  = 14
controlNum2Name[14] = "op0_env"            
controlNum2Name[15] = "op0_env_porta"      
controlNum2Name[16] = "op0_envexp"         
controlNum2Name[17] = "op0_increment"      
controlNum2Name[18] = "op0_increment_porta"
controlNum2Name[19] = "op0_incexp"         
controlNum2Name[20] = "op0_fmsrc"         
controlNum2Name[21] = "op0_amsrc"         
controlNum2Name[22] = "op0_static"         
controlNum2Name[23] = "op0_sounding"         

OPBASE[1]  = 24
controlNum2Name[24] = "op1_env"            
controlNum2Name[25] = "op1_env_porta"      
controlNum2Name[26] = "op1_envexp"         
controlNum2Name[27] = "op1_increment"      
controlNum2Name[28] = "op1_increment_porta"
controlNum2Name[29] = "op1_incexp"         
controlNum2Name[30] = "op1_fmsrc"         
controlNum2Name[31] = "op1_amsrc"         
controlNum2Name[32] = "op1_static"         
controlNum2Name[33] = "op1_sounding"         


OPOFFSET = {}
OPOFFSET["env"            ] = 0
OPOFFSET["env_porta"      ] = 1
OPOFFSET["envexp"         ] = 2
OPOFFSET["increment"      ] = 3
OPOFFSET["increment_porta"] = 4
OPOFFSET["incexp"         ] = 5
OPOFFSET["fmsrc"          ] = 6
OPOFFSET["amsrc"          ] = 7
OPOFFSET["static"         ] = 8
OPOFFSET["sounding"       ] = 9

OPBASE[2]  = 34
controlNum2Name[34] = "op2_env"            
controlNum2Name[35] = "op2_env_porta"      
controlNum2Name[36] = "op2_envexp"         
controlNum2Name[37] = "op2_increment"      
controlNum2Name[38] = "op2_increment_porta"
controlNum2Name[39] = "op2_incexp"         
controlNum2Name[40] = "op2_fmsrc"         
controlNum2Name[41] = "op2_amsrc"         
controlNum2Name[42] = "op2_static"         
controlNum2Name[43] = "op2_sounding"         

OPBASE[3]  = 44
controlNum2Name[44] = "op3_env"            
controlNum2Name[45] = "op3_env_porta"      
controlNum2Name[46] = "op3_envexp"         
controlNum2Name[47] = "op3_increment"      
controlNum2Name[48] = "op3_increment_porta"
controlNum2Name[49] = "op3_incexp"         
controlNum2Name[50] = "op3_fmsrc"         
controlNum2Name[51] = "op3_amsrc"         
controlNum2Name[52] = "op3_static"         
controlNum2Name[53] = "op3_sounding"         


OPBASE[4]  = 54
controlNum2Name[54] = "op4_env"            
controlNum2Name[55] = "op4_env_porta"      
controlNum2Name[56] = "op4_envexp"         
controlNum2Name[57] = "op4_increment"      
controlNum2Name[58] = "op4_increment_porta"
controlNum2Name[59] = "op4_incexp"         
controlNum2Name[60] = "op4_fmsrc"         
controlNum2Name[61] = "op4_amsrc"         
controlNum2Name[62] = "op4_static"         
controlNum2Name[63] = "op4_sounding"         

# common midi controls
controlNum2Name[64] = "sustain"         # common midi control
controlNum2Name[65] = "portamento"      # common midi control
controlNum2Name[71] = "filter_resonance"# common midi control
controlNum2Name[74] = "filter_cutoff"   # common midi control

OPBASE[4]  = 75
controlNum2Name[75] = "op5_env"            
controlNum2Name[76] = "op5_env_porta"      
controlNum2Name[77] = "op5_envexp"         
controlNum2Name[78] = "op5_increment"      
controlNum2Name[79] = "op5_increment_porta"
controlNum2Name[80] = "op5_incexp"         
controlNum2Name[81] = "op5_fmsrc"         
controlNum2Name[82] = "op5_amsrc"         
controlNum2Name[83] = "op5_static"         
controlNum2Name[84] = "op5_sounding"         

OPBASE[6]  = 85
controlNum2Name[85] = "vibrato_env"            
controlNum2Name[86] = "vibrato_env_porta"      
controlNum2Name[87] = "vibrato_envexp"         
controlNum2Name[88] = "vibrato_increment"      
controlNum2Name[89] = "vibrato_increment_porta"
controlNum2Name[90] = "vibrato_incexp"         
controlNum2Name[91] = "vibrato_fmsrc"         
controlNum2Name[92] = "vibrato_amsrc"         
controlNum2Name[93] = "vibrato_static"         
controlNum2Name[94] = "vibrato_sounding"         


OPBASE[7]  = 93
controlNum2Name[95]  = "tremolo_env"            
controlNum2Name[96]  = "tremolo_env_porta"      
controlNum2Name[97]  = "tremolo_envexp"         
controlNum2Name[98]  = "tremolo_increment"      
controlNum2Name[99]  = "tremolo_increment_porta"
controlNum2Name[100] = "tremolo_incexp"         
controlNum2Name[101] = "tremolo_fmsrc"         
controlNum2Name[102] = "tremolo_amsrc"         
controlNum2Name[103] = "tremolo_static"         
controlNum2Name[104] = "tremolo_sounding"         


# begin global params
controlNum2Name[110] = "env_clkdiv"     
controlNum2Name[111] = "flushspi"       
controlNum2Name[112] = "passthrough"    
controlNum2Name[113] = "shift"          

controlName2Num = {}
for i, name in enumerate(controlNum2Name):
	controlName2Num[name] = i

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
		self.fpga_interface_inst = fpga_interface_inst
		
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
		
	def processEvent(self, event, recursive = True):
		#logger.debug(str(self) + " processing " + event)
		for action in self.event2action[event]:
			action()
		
		if recursive:
			for child in self.allChildren:
				child.processEvent(event)
			
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
		
	def send(self, param):
		self.fpga_interface_inst.send(param, 0, 0, self.computedState[param])
		
	def __init__(self, fpga_interface_inst):
		logger.debug("patch init ")
		self.fpga_interface_inst  = fpga_interface_inst
		super().__init__(0, self.fpga_interface_inst, self)
		self.polyphony  = 2
				
		self.control = [0]*CONTROLCOUNT
		self.controlReal = [0]*CONTROLCOUNT
		self.control[0]  = 0    #"vibrato_env"  # modwheel. tie it to vibrato (Pitch LFO)
		self.control[1]  = 1  # tremolo_env  # breath control
		self.control[controlName2Num["algorithm"]]  = 0    #
		self.control[controlName2Num["volume"   ]]  = 127  #         
		self.control[controlName2Num["fbgain"   ]]  = 0    #          
		self.control[controlName2Num["fbsrc"    ]]  = 0    #          
		self.control[controlName2Num["am_algo"  ]]  = 0    #            
		
		self.control[controlName2Num["voicegain"       ]] = 127    #   # common midi control
		self.control[controlName2Num["sounding"        ]] = 1      #
		self.control[controlName2Num["baseincrement"   ]] = 127    #              
		self.control[controlName2Num["pan"             ]] = 64      #   # common midi control
		self.control[controlName2Num["expression"      ]] = 0       #   # common midi 
		self.control[controlName2Num["sustain"         ]] = 0       ## common midi control
		self.control[controlName2Num["portamento"      ]] = 0       ## common midi control
		self.control[controlName2Num["filter_resonance"]] = 0       ## common midi control
		self.control[controlName2Num["filter_cutoff"   ]] = 0       ## common midi control
		
		self.control[controlName2Num["op0_env"            ]] = 127 # 
		self.control[controlName2Num["op0_env_porta"      ]] = 0   # 
		self.control[controlName2Num["op0_envexp"         ]] = 1   # 
		self.control[controlName2Num["op0_increment"      ]] = 127 # 
		self.control[controlName2Num["op0_increment_porta"]] = 0   # 
		self.control[controlName2Num["op0_incexp"         ]] = 1   # 
		self.control[controlName2Num["op0_fmsrc"          ]] = 0   # 
		self.control[controlName2Num["op0_amsrc"          ]] = 0   # 
		self.control[controlName2Num["op0_static"         ]] = 0   # 
		self.control[controlName2Num["op0_sounding"       ]] = 1   # 
		
		self.control[controlName2Num["op1_env"            ]] = 127 # 
		self.control[controlName2Num["op1_env_porta"      ]] = 0   # 
		self.control[controlName2Num["op1_envexp"         ]] = 1   # 
		self.control[controlName2Num["op1_increment"      ]] = 127 # 
		self.control[controlName2Num["op1_increment_porta"]] = 0   # 
		self.control[controlName2Num["op1_incexp"         ]] = 1   # 
		self.control[controlName2Num["op1_fmsrc"          ]] = 0   # 
		self.control[controlName2Num["op1_amsrc"          ]] = 0   # 
		self.control[controlName2Num["op1_static"         ]] = 0   # 
		self.control[controlName2Num["op1_sounding"       ]] = 0   # 
		
		self.control[controlName2Num["op2_env"            ]] = 127 # 
		self.control[controlName2Num["op2_env_porta"      ]] = 0   # 
		self.control[controlName2Num["op2_envexp"         ]] = 1   # 
		self.control[controlName2Num["op2_increment"      ]] = 127 # 
		self.control[controlName2Num["op2_increment_porta"]] = 0   # 
		self.control[controlName2Num["op2_incexp"         ]] = 1   # 
		self.control[controlName2Num["op2_fmsrc"          ]] = 0   # 
		self.control[controlName2Num["op2_amsrc"          ]] = 0   # 
		self.control[controlName2Num["op2_static"         ]] = 0   # 
		self.control[controlName2Num["op2_sounding"       ]] = 0   # 
		
		self.control[controlName2Num["op3_env"            ]] = 127 # 
		self.control[controlName2Num["op3_env_porta"      ]] = 0   # 
		self.control[controlName2Num["op3_envexp"         ]] = 1   # 
		self.control[controlName2Num["op3_increment"      ]] = 127 # 
		self.control[controlName2Num["op3_increment_porta"]] = 0   # 
		self.control[controlName2Num["op3_incexp"         ]] = 1   # 
		self.control[controlName2Num["op3_fmsrc"          ]] = 0   # 
		self.control[controlName2Num["op3_amsrc"          ]] = 0   # 
		self.control[controlName2Num["op3_static"         ]] = 0   # 
		self.control[controlName2Num["op3_sounding"       ]] = 0   # 
		
		self.control[controlName2Num["op4_env"            ]] = 127 # 
		self.control[controlName2Num["op4_env_porta"      ]] = 0   # 
		self.control[controlName2Num["op4_envexp"         ]] = 1   # 
		self.control[controlName2Num["op4_increment"      ]] = 127 # 
		self.control[controlName2Num["op4_increment_porta"]] = 0   # 
		self.control[controlName2Num["op4_incexp"         ]] = 1   # 
		self.control[controlName2Num["op4_fmsrc"          ]] = 0   # 
		self.control[controlName2Num["op4_amsrc"          ]] = 0   # 
		self.control[controlName2Num["op4_static"         ]] = 0   # 
		self.control[controlName2Num["op4_sounding"       ]] = 0   # 
		
		self.control[controlName2Num["op5_env"            ]] = 127 # 
		self.control[controlName2Num["op5_env_porta"      ]] = 0   # 
		self.control[controlName2Num["op5_envexp"         ]] = 1   # 
		self.control[controlName2Num["op5_increment"      ]] = 127 # 
		self.control[controlName2Num["op5_increment_porta"]] = 0   # 
		self.control[controlName2Num["op5_incexp"         ]] = 1   # 
		self.control[controlName2Num["op5_fmsrc"          ]] = 0   # 
		self.control[controlName2Num["op5_amsrc"          ]] = 0   # 
		self.control[controlName2Num["op5_static"         ]] = 0   # 
		self.control[controlName2Num["op5_sounding"       ]] = 0   # 
		
		self.control[controlName2Num["op6_env"            ]] = 127 # 
		self.control[controlName2Num["op6_env_porta"      ]] = 0   # 
		self.control[controlName2Num["op6_envexp"         ]] = 1   # 
		self.control[controlName2Num["op6_increment"      ]] = 127 # 
		self.control[controlName2Num["op6_increment_porta"]] = 0   # 
		self.control[controlName2Num["op6_incexp"         ]] = 1   # 
		self.control[controlName2Num["op6_fmsrc"          ]] = 0   # 
		self.control[controlName2Num["op6_amsrc"          ]] = 0   # 
		self.control[controlName2Num["op6_static"         ]] = 0   # 
		self.control[controlName2Num["op6_sounding"       ]] = 0   # 
		
		self.control[controlName2Num["op7_env"            ]] = 127 # 
		self.control[controlName2Num["op7_env_porta"      ]] = 0   # 
		self.control[controlName2Num["op7_envexp"         ]] = 1   # 
		self.control[controlName2Num["op7_increment"      ]] = 127 # 
		self.control[controlName2Num["op7_increment_porta"]] = 0   # 
		self.control[controlName2Num["op7_incexp"         ]] = 1   # 
		self.control[controlName2Num["op7_fmsrc"          ]] = 0   # 
		self.control[controlName2Num["op7_amsrc"          ]] = 0   # 
		self.control[controlName2Num["op7_static"         ]] = 0   # 
		self.control[controlName2Num["op7_sounding"       ]] = 0   # 
		
		
		self.control[controlName2Num["env_clkdiv" ]] = 8 #    
		self.control[controlName2Num["flushspi"   ]] = 0 #    
		self.control[controlName2Num["passthrough"]] = 0 #    
		self.control[controlName2Num["shift"      ]] = 2 #    
		
		for i in range(len(self.controlReal)):
			self.controlReal[i] = self.control[i] / 128.0
			
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
	
		self.event2action["control[100]"] = [self.fn_env_clkdiv ]
		self.event2action["control[101]"] = [self.fn_flushspi   ]
		self.event2action["control[102]"] = [self.fn_passthrough]
		self.event2action["control[103]"] = [self.fn_shift      ]
			
		for voice in self.voices:
			logger.debug("claimed: " + str(voice.index))
			voice.note  = self.allNotes[0]
			voice.patch = self
				
		self.toRelease   = []
	
		#defaults!
		for i, val in enumerate(self.control):
			logger.debug(val)
			self.processEvent(mido.Message('control_change', control=  i, value = int(val)))
		self.processEvent(mido.Message('pitchwheel', pitch = 64))
		self.processEvent(mido.Message('aftertouch', value = 0))
		for note in self.allNotes:
			self.processEvent(mido.Message('polytouch', note = note.index, value = 0))
	
	
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
				
		elif msg.type == 'pitchwheel':
			logger.debug("PW: " + str(msg.pitch))
			self.pitchwheel = msg.pitch
			amountchange = msg.pitch / 8192.0
			self.pitchwheelReal = pow(2, amountchange)
				
		elif msg.type == 'control_change':
			logger.debug("control : " + str(msg.control) + ": " + str(msg.value))
			self.control[msg.control]     = msg.value
			self.controlReal[msg.control] = msg.value/127.0
			event = "control[" + str(msg.control) + "]"
			
			# forward some controls
			if msg.control == 0:
				self.processEvent(mido.Message('control_change', control= 80, value = msg.value ))
				self.processEvent(mido.Message('control_change', control= 90, value = msg.value ))
			if msg.control == 1:
				self.processEvent(mido.Message('control_change', control= 80, value = msg.value ))
				self.processEvent(mido.Message('control_change', control= 90, value = msg.value ))
				
			
		elif msg.type == 'polytouch':
			self.allNotes[msg.note].polytouch = msg.value/127.0
			note = self.allNotes[msg.note]
			voicesToUpdate = note.voices
			
		elif msg.type == 'aftertouch':
			self.aftertouch = msg.value
			self.aftertouchReal = msg.value/127.0
						
		
		for voice in voicesToUpdate:
			voice.processEvent(event)

		if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
			# implement rising mono porta
			for heldnote in self.allNotes[::-1]:
				if heldnote.held and self.polyphony == self.voicesPerNote :
					self.processEvent(heldnote.msg)
					break

class Channel(FPGA_component):
	def __init__(self, voice, index, fpga_interface_inst, patch):
		super().__init__(index, fpga_interface_inst, patch)
		self.voice = voice
		self.event2action["control[3]"]   = [self.fn_voicegain]
		self.event2action["control[7]"]   = [self.fn_voicegain]
		self.event2action["control[10]"]  = [self.fn_voicegain]
		self.fpga_interface_inst = fpga_interface_inst
		
	# control 7 = volume, 10 = pan
	def fn_voicegain (self)   : 
		baseVolume = 2**16*self.patch.controlReal[7]*self.patch.controlReal[3]
		if self.index == 0:
			self.send("cmd_voicegain", baseVolume*self.patch.controlReal[10]) # assume 2 channels
		else:
			#logger.debug(self.patch.controlReal[10])
			self.send("cmd_voicegain", baseVolume*(1 - self.patch.controlReal[10])) # assume 2 channels
	
	def send(self, param, value):
		if self.stateInFPGA.get(param) != value:
			self.fpga_interface_inst.send(param, self.index, self.voice.index, value)
		self.stateInFPGA[param] = value

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
			
		self.event2action["note_on"]      = [self.fn_baseincrement ]
		self.event2action["pitchwheel"]   = [self.fn_baseincrement ]
		self.event2action["aftertouch"]   = [self.fn_baseincrement ]
		self.event2action["control[2]"]   = [self.fn_algorithm     ]
		self.event2action["control[4]"]   = [self.fn_fbgain        ]
		self.event2action["control[5]"]   = [self.fn_fbsrc         ]
		self.event2action["control[6]"]   = [self.fn_am_algo       ]
		self.event2action["control[9]"]   = [self.fn_baseincrement ]
		self.event2action["control[8]"]   = [self.fn_sounding      ]
		self.event2action["control[12]"]  = [self.fn_static        ]
		self.event2action["control[13]"]  = [self.fn_static        ]
	
	# match DX7
	def fn_algorithm (self)         : self.send("cmd_algorithm", self.patch.control[2]                                  ) 
	def fn_am_algo   (self)         : self.send("cmd_am_algo"  , self.patch.control[6]                                  )
	def fn_fbgain    (self)         : self.send("cmd_fbgain"   , 2**16 * self.patch.controlReal[4]                      )
	def fn_fbsrc     (self)         : self.send("cmd_fbsrc"    , self.patch.control[5]                                  )
	def fn_sounding  (self)         : self.send("cmd_sounding" , self.patch.control[8]                                  )
	def fn_static    (self)         : self.send("cmd_static"   , self.patch.control[12] + (self.patch.control[13] << 4) )
	
	def fn_baseincrement (self)     : 
		logger.debug(str(self.patch.controlReal[9]) + " " + str(self.patch.pitchwheelReal) + " " + str(1 + self.patch.aftertouchReal) + " " +  str(self.note.defaultIncrement))
		self.send("cmd_baseincrement", self.patch.controlReal[9] * self.patch.pitchwheelReal * (1 + self.patch.aftertouchReal) * self.note.defaultIncrement)

	def send(self, param, value):
		if self.stateInFPGA.get(param) != value:
			self.fpga_interface_inst.send(param, 0, self.index, value)
		self.stateInFPGA[param] = value

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

# OPERATOR DESCRIPTIONS
class Operator(FPGA_component):
	def __init__(self, voice, index, fpga_interface_inst, patch):
		self.voice = voice
		super().__init__(index, fpga_interface_inst, patch)
		self.base  = OPBASE[self.index]
		# provide a set of actions to be run when event happens
		self.event2action["note_on"]                           = [self.fn_env]
		self.event2action["note_off"]                          = [self.fn_env]
		self.event2action["pitchwheel"]                        = []
		self.event2action["aftertouch"]                        = []
		self.event2action["polytouch"]                         = []
		self.event2action[self.getCtrlNum("env"            )]  = [self.fn_env            ]
		self.event2action[self.getCtrlNum("env_porta"      )]  = [self.fn_env_porta      ]
		self.event2action[self.getCtrlNum("envexp"         )]  = [self.fn_envexp         ]
		self.event2action[self.getCtrlNum("increment"      )]  = [self.fn_increment      ]
		self.event2action[self.getCtrlNum("increment_porta")]  = [self.fn_increment_porta]
		self.event2action[self.getCtrlNum("incexp"         )]  = [self.fn_incexp         ]
		
		
	
	def getCtrlNum(self, paramName):
		return "control[" + str(int(self.base + OPOFFSET[paramName])) + "]"
		
	def fn_env_porta      (self) : self.send("cmd_env_porta"      , 2**8 * (1 - self.patch.controlReal[self.base + OPOFFSET["env_porta"]]) * (1 - self.patch.controlReal[65]) )# 65 is portamento self.patch.control
	# static oscillators do not have velocity-dependant env
	def fn_env            (self) : 
		if (self.voice.stateInFPGA.get("cmd_static") is not None and self.voice.stateInFPGA.get("cmd_static") & (1 << self.index)):
			self.send("cmd_env"            , (2**16) * self.patch.controlReal[self.base + OPOFFSET["env"]]               )
		else:
			self.send("cmd_env"            , self.voice.note.velocityReal * (2**16) * self.patch.controlReal[self.base + OPOFFSET["env"]]                 )
	def fn_increment      (self) : self.send("cmd_increment"      , 2**16 * self.patch.controlReal[self.base + OPOFFSET["increment"]]                     ) # * self.patch.controlReal[self.base + OPOFFSET["increment"]]
	def fn_increment_porta(self) : self.send("cmd_increment_porta", 2**12 * (1 - self.patch.controlReal[OPBASE[self.index] + OPOFFSET["increment_porta"]]))
	def fn_incexp         (self) : self.send("cmd_incexp"         , int(self.patch.control[self.base + OPOFFSET["incexp"]])                               )
	def fn_envexp         (self) : self.send("cmd_envexp"         , int(self.patch.control[self.base + OPOFFSET["envexp"]])                               )

	def send(self, param, value):
		if self.stateInFPGA.get(param) != value:
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
	cmdName2number["cmd_algorithm"]  = 70
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
	fpga_interface_inst.send("cmd_algorithm"       , opno, voiceno, 1)

	opno = 1
	fpga_interface_inst.send("cmd_increment_porta", opno, voiceno, 2**30)
	fpga_interface_inst.send("cmd_increment"      , opno, voiceno, 2**22)
	fpga_interface_inst.send("cmd_algorithm"      , opno, voiceno, 2)
	
	fpga_interface_inst.send("cmd_flushspi", 0, 0, 0)
	fpga_interface_inst.send("cmd_shift"   , 0, 0, 0)
		