import spidev
import struct
maxSpiSpeed = 100000000
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

controlName = [""]*CONTROLCOUNT

# common midi controls https://professionalcomposers.com/midi-cc-list/

# begin voice parameters
controlName[0] = "vibrato_env"  # modwheel. tie it to vibrato (Pitch LFO)
controlName[1] = "tremolo_env"  # breath control
controlName[2] = "algorithm"
controlName[3] = "am_algo"        
controlName[4] = "fbgain"         
controlName[5] = "fbsrc"          


controlName[7]  = "voicegain"       # common midi control
controlName[10] = "pan"             # common midi control
controlName[11] = "expression"      # common midi control
controlName[64] = "sustain"         # common midi control
controlName[65] = "portamento"      # common midi control
controlName[71] = "filter_resonance"# common midi control
controlName[74] = "filter_cutoff"   # common midi control


OPBASE = [0]*8
# begin operator parameters
OPBASE[0]  = 14
controlName[14] = "op0_env"            
controlName[15] = "op0_env_porta"      
controlName[16] = "op0_envexp"         
controlName[17] = "op0_increment"      
controlName[18] = "op0_increment_porta"
controlName[19] = "op0_incexp"         

OPBASE[1]  = 20
controlName[20] = "op1_env"            
controlName[21] = "op1_env_porta"      
controlName[22] = "op1_envexp"         
controlName[23] = "op1_increment"      
controlName[24] = "op1_increment_porta"
controlName[25] = "op1_incexp"         


OPOFFSET = {}
OPOFFSET["env"            ] = 0
OPOFFSET["env_porta"      ] = 1
OPOFFSET["envexp"         ] = 2
OPOFFSET["increment"      ] = 3
OPOFFSET["increment_porta"] = 4
OPOFFSET["incexp"         ] = 5

OPBASE[2]  = 30
controlName[30] = "op2_env"            
controlName[31] = "op2_env_porta"      
controlName[32] = "op2_envexp"         
controlName[33] = "op2_increment"      
controlName[34] = "op2_increment_porta"
controlName[35] = "op2_incexp"         

OPBASE[3]  = 40
controlName[40] = "op3_env"            
controlName[41] = "op3_env_porta"      
controlName[42] = "op3_envexp"         
controlName[43] = "op3_increment"      
controlName[44] = "op3_increment_porta"
controlName[45] = "op3_incexp"         


OPBASE[4]  = 50
controlName[50] = "op4_env"            
controlName[51] = "op4_env_porta"      
controlName[52] = "op4_envexp"         
controlName[53] = "op4_increment"      
controlName[54] = "op4_increment_porta"
controlName[55] = "op4_incexp"         


OPBASE[5]  = 56
controlName[56] = "op5_env"            
controlName[57] = "op5_env_porta"      
controlName[58] = "op5_envexp"         
controlName[59] = "op5_increment"      
controlName[60] = "op5_increment_porta"
controlName[61] = "op5_incexp"         

OPBASE[6]  = 80
controlName[80] = "vibrato_env"            
controlName[81] = "vibrato_env_porta"      
controlName[82] = "vibrato_envexp"         
controlName[83] = "vibrato_increment"      
controlName[84] = "vibrato_increment_porta"
controlName[85] = "vibrato_incexp"         



OPBASE[7]  = 90
controlName[90] = "tremolo_env"            
controlName[91] = "tremolo_env_porta"      
controlName[92] = "tremolo_envexp"         
controlName[93] = "tremolo_increment"      
controlName[94] = "tremolo_increment_porta"
controlName[95] = "tremolo_incexp"         


# begin global params
controlName[100] = "env_clkdiv"     
controlName[101] = "flushspi"       
controlName[102] = "passthrough"    
controlName[103] = "shift"          


import inspect
# master class for FPGA elements
class FPGA_component:

	# need to call super.init
	def __init__(self, index, fpga_interface_inst):
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
		
	def computeAndSendEvent(self, event, recursive = True):
		#logger.debug(str(self) + " processing " + event)
		for actionTuple in self.event2action[event]:
			param, fn = actionTuple
			self.compute(param, fn)
			self.send(param)
		
		if recursive:
			for child in self.allChildren:
				child.computeAndSendEvent(event)
			
	def computeAndSendAll(self):
		#logger.debug("updating all")
		
		# run ALL the Actions!
		for event, actionList in self.event2action.items():
			for actionTuple in actionList:
				self.computeAndSend(actionTuple)
		
		#send to all children that are of type FPGA_component
		for child in self.allChildren:
			child.computeAndSendAll()
		
	def compute(self, param, fn):
		self.computedState[param] = fn()
		
	def computeAndSend(self, actionTuple):
		#logger.debug("running action " + str(actionTuple))
		param, fn = actionTuple
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
class Patch:

	def __init__(self, fpga_interface_inst):
		logger.debug("patch init ")
				
		self.control = [0]*CONTROLCOUNT
		self.control[0] = 0  #"vibrato_env"  # modwheel. tie it to vibrato (Pitch LFO)
		self.control[1] = 0  #"tremolo_env"  # breath control
		self.control[2] = 0  #"algorithm"
		self.control[3] = 0  #"am_algo"            
		self.control[4] = 0  #"fbgain"             
		self.control[5] = 0  #"fbsrc"              

		self.control[7]  = 127 #"voicegain"       # common midi control
		self.control[10] = 64  #"pan"             # common midi control
		self.control[11] = 0   #"expression"      # common midi control
		self.control[64] = 0   #"sustain"         # common midi control
		self.control[65] = 0   #"portamento"      # common midi control
		self.control[71] = 0 #"filter_resonance"# common midi control
		self.control[74] = 0 #"filter_cutoff"   # common midi control

		self.control[14] = 1 # "op0_env"            
		self.control[15] = 0 # "op0_env_porta"      
		self.control[16] = 1 # "op0_envexp"         
		self.control[17] = 1 # "op0_increment"      
		self.control[18] = 0 # "op0_increment_porta"
		self.control[19] = 1 # "op0_incexp"         

		self.control[20] = 1 # "env"            
		self.control[21] = 0 # "env_porta"      
		self.control[22] = 1 # "envexp"         
		self.control[23] = 1 # "increment"      
		self.control[24] = 0 # "increment_porta"
		self.control[25] = 1 # "incexp"         

		self.control[30] = 1 # "env"            
		self.control[31] = 0 # "env_porta"      
		self.control[32] = 1 # "envexp"         
		self.control[33] = 1 # "increment"      
		self.control[34] = 0 # "increment_porta"
		self.control[35] = 1 # "incexp"         

		self.control[40] = 1 # "env"            
		self.control[41] = 0 # "env_porta"      
		self.control[42] = 1 # "envexp"         
		self.control[43] = 1 # "increment"      
		self.control[44] = 0 # "increment_porta"
		self.control[45] = 1 # "incexp"         

		self.control[50] = 1 # "env"            
		self.control[51] = 0 # "env_porta"      
		self.control[52] = 1 # "envexp"         
		self.control[53] = 1 # "increment"      
		self.control[54] = 0 # "increment_porta"
		self.control[55] = 1 # "incexp"         

		self.control[56] = 1 # "env"            
		self.control[57] = 0 # "env_porta"      
		self.control[58] = 1 # "envexp"         
		self.control[59] = 1 # "increment"      
		self.control[60] = 0 # "increment_porta"
		self.control[61] = 1 # "incexp"         

		self.control[80] = 1 # "env"            
		self.control[81] = 0 # "env_porta"      
		self.control[82] = 1 # "envexp"         
		self.control[83] = 1 # "increment"      
		self.control[84] = 0 # "increment_porta"
		self.control[85] = 1 # "incexp"         

		self.control[90] = 1 # "env"            
		self.control[91] = 0 # "env_porta"      
		self.control[92] = 1 # "envexp"         
		self.control[93] = 1 # "increment"      
		self.control[94] = 0 # "increment_porta"
		self.control[95] = 1 # "incexp"         

		self.control[100] = 5 #"env_clkdiv"     
		self.control[101] = 0 #"flushspi"       
		self.control[102] = 0 #"passthrough"    
		self.control[103] = 2 #"shift"          

		# each patch has its own controls so they can be independantly initialized
		self.control     = np.zeros((CONTROLCOUNT), dtype=int)
		
		self.voicesPerNote = 1
		self.polyphony  = 2
		self.fpga_interface_inst  = fpga_interface_inst
		self.voices = []
		self.currVoiceIndex = 0
		self.currVoice = 0
		self.pitchwheel  = 1
		self.aftertouch = 0
				
		self.allNotes = []
		for i in range(MIDINOTES):
			self.allNotes+= [Note(i)]
			
		self.voices = self.fpga_interface_inst.getVoices(self, self.polyphony)
		
		for voice in self.voices:
			logger.debug("claimed: " + str(voice.index))
			voice.note  = self.allNotes[0]
			voice.patch = self
			voice.computeDicts()
			voice.computeAndSendAll()
				
		self.toRelease   = []
	
		#defaults!
		for i, val in enumerate(self.control):
			self.processEvent(mido.Message('control_change', control=  i, value = val)) # volume
	
	
	def processEvent(self, msg):
	
		logger.debug("processing " + msg.type)
		voices = self.voices
			
		msgtype = msg.type
		voicesToUpdate = self.voices
		event = msg.type
		
		if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
			note = self.allNotes[msg.note] 
			note.velocity = 0 
			voicesToUpdate = note.voices.copy()
			note.voices = []
			note.held = False
			
			
				
		elif msg.type == "note_on":
			note = self.allNotes[msg.note]
			note.velocity = msg.velocity
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
			amountchange = msg.pitch / 8192.0
			self.pitchwheel = pow(2, amountchange)
				
		elif msg.type == 'control_change':
			self.control[msg.control] = msg.value
			event = "control[" + str(msg.control) + "]"
			
		elif msg.type == 'polytouch':
			self.allNotes[msg.note].polytouch = msg.value/128.0
			note = self.allNotes[msg.note]
			voicesToUpdate = note.voices
			
		elif msg.type == 'aftertouch':
			self.aftertouch = msg.value/128.0
						
		for voice in voicesToUpdate:
			voice.computeAndSendEvent(event)

		if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
			# implement rising mono porta
			for heldnote in self.allNotes[::-1]:
				if heldnote.held and self.polyphony == self.voicesPerNote :
					self.processEvent(heldnote.msg)
					break

class Channel(FPGA_component):
	def __init__(self, voice, index, fpga_interface_inst):
		super().__init__(index, fpga_interface_inst)
		self.voice = voice
		self.event2action["control[7]"]   = [("cmd_voicegain", self.fn_voicegain)]
		self.event2action["control[10]"]  = [("cmd_voicegain", self.fn_voicegain)]
		self.fpga_interface_inst = fpga_interface_inst
		
	# control 7 = volume, 10 = pan
	def fn_voicegain (self)   : return  2**16*(control[7])*(self.index - (control[10])) # assume 2 channels
	
	def send(self, param):
		self.fpga_interface_inst.send(param, self.index, self.voice.index, self.computedState[param])

class Voice(FPGA_component):
		
	def __init__(self, index, fpga_interface_inst):
		super().__init__(index, fpga_interface_inst)
		
	
		self.index = index
		self.note = None
		self.patch  = None
		self.sounding = False    
		self.defaultIncrement = 0
		self.indexInCluster = 0
		self.OPERATORCOUNT  = 8
		self.operators = []
		for opindex in range(self.OPERATORCOUNT):
			self.operators += [Operator(self, opindex, fpga_interface_inst)]
		
		self.operators[0].fn_env  = self.operators[0].override_env_standard
		
		self.channels = []
		self.channels += [Channel(self, 0, fpga_interface_inst)]
		self.channels += [Channel(self, 1, fpga_interface_inst)]
		
		self.allChildren = self.channels + self.operators 
			
		self.event2action["control[1]"]  = [("cmd_vol_lfo_depth", self.fn_vol_lfo_depth )]
		self.event2action["control[2]"]  = [("cmd_algorithm"    , self.fn_algorithm )]
		self.event2action["control[3]"]  = [("cmd_am_algo"      , self.fn_am_algo   )]
		self.event2action["control[4]"]  = [("cmd_fbgain"       , self.fn_fbgain )]
		self.event2action["control[5]"]  = [("cmd_fbsrc"        , self.fn_fbsrc )]

	def fn_vol_lfo_depth (self)     : return 2**16 * self.control[1] #= "tremolo_env"  # breath control
	
	# match DX7
	def fn_algorithm (self)         : return self.patch.control[2] # TODO
	def fn_am_algo (self)           : return self.patch.control[3]
	def fn_fbgain (self)            : return 2**16 * self.patch.control[4]
	def fn_fbsrc (self)             : return self.patch.control[5]

	def send(self, param):
		self.fpga_interface_inst.send(param, 0, self.index, self.computedState[param])

def noteToFreq(note):
	a = 440.0 #frequency of A (coomon value is 440Hz)
	return (a / 32) * (2 ** ((note - 9) / 12))


class Note:
	def __init__(self, index):
		self.index  = index
		self.voices = []
		self.velocity = 0
		self.held  = False
		self.polytouch = 0
		self.msg  = None
		self.defaultIncrement = 2**32 * (noteToFreq(index) / 96000.0)

# OPERATOR DESCRIPTIONS
class Operator(FPGA_component):
	def __init__(self, voice, index, fpga_interface_inst):
		self.voice = voice
		super().__init__(index, fpga_interface_inst)
		self.base  = OPBASE[self.index]
		# provide a set of actions to be run when event happens
		self.event2action["note_on"]                           = [("cmd_env",       self.override_env_standard), ("cmd_increment", self.fn_increment)]
		self.event2action["note_off"]                          = [("cmd_env",       self.override_env_standard)]
		self.event2action["pitchwheel"]                        = [("cmd_increment", self.fn_increment)]
		self.event2action["aftertouch"]                        = [("cmd_increment", self.fn_increment)]
		self.event2action["polytouch"]                         = []
		self.event2action[self.getCtrlNum("env"            )]  = [("cmd_env"            , self.fn_env           )]
		self.event2action[self.getCtrlNum("env_porta"      )]  = [("cmd_env_porta"      , self.fn_env_porta     )]
		self.event2action[self.getCtrlNum("envexp"         )]  = [("cmd_envexp"         , self.fn_envexp        )]
		self.event2action[self.getCtrlNum("increment"      )]  = [("cmd_increment"      , self.fn_increment     )]
		self.event2action[self.getCtrlNum("increment_porta")]  = [("cmd_increment_porta", self.fn_increment_porta)]
		self.event2action[self.getCtrlNum("incexp"         )]  = [("cmd_incexp"         , self.fn_incexp        )]
		
		
	
	def getCtrlNum(self, paramName):
		return "control[" + str(int(self.base + OPOFFSET[paramName])) + "]"
		
	# TODO : WRITE FPGA CODE FOR SOUNDING vs NONSOUNDING OSC
	def fn_env_porta      (self) : return 2**15 * (1 - control[self.base + OPOFFSET["env_porta"]]) * (1 - control[65]) # 65 is portamento control
	def fn_env            (self) : return 2**16 * control[self.base + OPOFFSET["env"]]                      
	def override_env_standard   (self) : return self.voice.note.velocity*(2**16) * control[self.base + OPOFFSET["env"]] 
	def fn_increment      (self) : 
		pwadj = self.voice.patch.pitchwheel * self.voice.note.defaultIncrement
		indexOffset = (2 ** (self.voice.indexInCluster - (self.voice.patch.voicesPerNote-1)/2))
		return pwadj * indexOffset * (1 + self.voice.patch.aftertouch) * control[self.base + OPOFFSET["increment"]]
	#def fn_increment_porta(self) : return 2**22*(self.voice.patch.control[4]/128.0)  
	def fn_increment_porta(self) : return 2**21 * control[1+OPBASE[self.index]]
	def fn_incexp         (self) : return 2*control[self.base + OPOFFSET["incexp"]]  
	def fn_envexp         (self) : return 2*control[self.base + OPOFFSET["envexp"]]  

	def send(self, param):
		self.fpga_interface_inst.send(param, self.index, self.voice.index, self.computedState[param])

	def __unicode__(self):
		if self.index != None:
			return str(str(type(self))) + " #" + str(self.index) + " of Voice " + str(self.voice) 
		else:
			return str(type(self)) + " #" + "ALL"

			
class dt01(FPGA_component):

	POLYPHONYCOUNT = 32*4

	def __init__(self):
		self.fpga_interface_inst = fpga_interface()
		super().__init__(0, self.fpga_interface_inst)
		self.voiceno = 0# round robin voice allocation
		self.voices  = []
		
		for i in range(self.POLYPHONYCOUNT):
			newVoice = Voice(i, self.fpga_interface_inst)
			self.voices += [newVoice]

		self.allChildren = self.voices
		self.computeDicts(recursive = False)
	
		self.event2action["control[100]"] = [("cmd_env_clkdiv" , self.fn_env_clkdiv )]
		self.event2action["control[101]"] = [("cmd_flushspi"   , self.fn_flushspi   )]
		self.event2action["control[102]"] = [("cmd_passthrough", self.fn_passthrough)]
		self.event2action["control[103]"] = [("cmd_shift"      , self.fn_shift      )]
		
	def fn_env_clkdiv (self) : return control[100]
	def fn_flushspi   (self) : return control[101]
	def fn_passthrough(self) : return control[102]
	def fn_shift      (self) : return control[103]
	
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


class fpga_interface():
	
	cmdName2number = {}
	cmdName2number["cmd_vol_lfo_depth"]  = 69
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
	cmdName2number["cmd_env_clkdiv"       ] = 99
	cmdName2number["cmd_flushspi"         ] = 120
	cmdName2number["cmd_passthrough"      ] = 121
	cmdName2number["cmd_shift"            ] = 122
		
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
			logger.debug("sending " + paramName + " operator:" + str(mm_opno) + " voice:" + str(voiceno) + " payload:" + str(payload))
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
	fpga_interface_inst.send("cmd_increment_porta" , opno, voiceno, 2**30)
	fpga_interface_inst.send("cmd_increment"       , opno, voiceno, 2**22)
	fpga_interface_inst.send("cmd_algorithm"       , opno, voiceno, 1)

	opno = 1
	fpga_interface_inst.send("cmd_increment_porta", opno, voiceno, 2**30)
	fpga_interface_inst.send("cmd_increment"      , opno, voiceno, 2**22)
	fpga_interface_inst.send("cmd_algorithm"      , opno, voiceno, 2)
	
	fpga_interface_inst.send("cmd_flushspi", 0, 0, 0)
	fpga_interface_inst.send("cmd_shift"   , 0, 0, 0)
		