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


# begin operator parameters
controlName[14] = "op0_env"            
controlName[15] = "op0_env_porta"      
controlName[16] = "op0_envexp"         
controlName[17] = "op0_increment"      
controlName[18] = "op0_increment_porta"
controlName[19] = "op0_incexp"         

controlName[20] = "op1_env"            
controlName[21] = "op1_env_porta"      
controlName[22] = "op1_envexp"         
controlName[23] = "op1_increment"      
controlName[24] = "op1_increment_porta"
controlName[25] = "op1_incexp"         

controlName[30] = "op2_env"            
controlName[31] = "op2_env_porta"      
controlName[32] = "op2_envexp"         
controlName[33] = "op2_increment"      
controlName[34] = "op2_increment_porta"
controlName[35] = "op2_incexp"         

controlName[40] = "op3_env"            
controlName[41] = "op3_env_porta"      
controlName[42] = "op3_envexp"         
controlName[43] = "op3_increment"      
controlName[44] = "op3_increment_porta"
controlName[45] = "op3_incexp"         

controlName[50] = "op4_env"            
controlName[51] = "op4_env_porta"      
controlName[52] = "op4_envexp"         
controlName[53] = "op4_increment"      
controlName[54] = "op4_increment_porta"
controlName[55] = "op4_incexp"         

controlName[70] = "op5_env"            
controlName[72] = "op5_env_porta"      
controlName[73] = "op5_envexp"         
controlName[75] = "op5_increment"      
controlName[76] = "op5_increment_porta"
controlName[77] = "op5_incexp"         

controlName[80] = "vibrato_env"            
controlName[81] = "vibrato_env_porta"      
controlName[82] = "vibrato_envexp"         
controlName[83] = "vibrato_increment"      
controlName[84] = "vibrato_increment_porta"
controlName[85] = "vibrato_incexp"         

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
		logger.debug("computing dicts " + str(self))
		self.allChildrenDict = collections.defaultdict(list)
		self.allChildren = []
		for membername, member in inspect.getmembers(self):
			# sometimes they may be elements of a list
			if isinstance(member,list):
				for v in member:
					if (isinstance(v, FPGA_component)):
						#logger.debug("child " + str(v))
						self.allChildrenDict[str(type(v))] += [v]
						self.allChildren += [v]
			
			# if its a function starting with fn
			if membername.startswith("fn_") and callable(member):
				#logger.debug("found function " + membername)
				for keyword, events in self.keyword2events.items():
					#logger.debug("kw " + keyword)
					#logger.debug("events " + str(events))
					if keyword in inspect.getsource(member):
						#logger.debug(keyword + ", yeah its in " + str(inspect.getsource(member)))
						for event in events:
							#logger.debug("adding " + membername + " to " + event)
							self.event2action[event] += [(membername.replace("fn_", "cmd_"), member)]
							
				# if the function contains no keywords, send it
				if not any([keyword in inspect.getsource(member) for keyword in self.keyword2events.keys()]):
					self.computeAndSend((membername.replace("fn_", "cmd_"),member))
		if recursive:
			for child in self.allChildren:
				child.computeDicts()
		
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
		
		#initialize some controls
		self.control[3]  = 64
		
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
		self.processEvent(mido.Message('control_change', control=  7, value = 64)) # volume
		self.processEvent(mido.Message('control_change', control= 10, value = 64)) # pan
	
	
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
			self.allNotes[msg.note].polytouch = msg.value
			note = self.allNotes[msg.note]
			voicesToUpdate = note.voices
			
		elif msg.type == 'aftertouch':
			self.aftertouch = msg.value
						
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
		self.fpga_interface_inst = fpga_interface_inst
		
	# control 7 = volume, 10 = pan
	def fn_voicegain (self)   : return  2**16*(control[7] / 128.0)*(self.index - (control[10] / 128.0))
	
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
		
			
	def fn_vol_lfo_depth (self)     : return 0x00000000
	
	# match DX7
	def fn_algorithm (self)         : 
		if control[
		return 0x00000000
	def fn_am_algo (self)           : return 0x00000000
	def fn_fbgain (self)            : return 0x00000000
	def fn_fbsrc (self)             : return 0x00000000

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
		

	def fn_env_porta      (self) : return 2**15                                                        
	def fn_env            (self) : return 0                      
	def override_env_standard   (self) : return self.voice.note.velocity*(2**16)/128.0                      
	def fn_increment      (self) : return self.voice.patch.pitchwheel * self.voice.note.defaultIncrement * (2 ** (self.voice.indexInCluster - (self.voice.patch.voicesPerNote-1)/2)) * (1 + self.voice.patch.aftertouch/128.0)
	#def fn_increment_porta(self) : return 2**22*(self.voice.patch.control[4]/128.0)  
	def fn_increment_porta(self) : return 2**21  	
	def fn_incexp         (self) : return 1                                                            
	def fn_envexp         (self) : return 1                                                            

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

		
		self.computeDicts(recursive = False)
	
	def fn_env_clkdiv (self) : return 5
	def fn_flushspi   (self) : return 0
	def fn_passthrough(self) : return 0
	def fn_shift      (self) : return 2
	
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
			#logger.debug("sending " + paramName + " operator:" + str(mm_opno) + " voice:" + str(voiceno) + " payload:" + str(payload))
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
		