import spidev
import struct
maxSpiSpeed = 20000000
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
logger = logging.getLogger('DT01')

MIDINOTES      = 128
CONTROLCOUNT   = 128


logger = logging.getLogger('DT01')
import inspect
# master class for FPGA elements
class FPGA_component:

	# need to call super.init
	def __init__(self, index, fpga_interface_inst):
	
		self.cmdName2number = dict()
		self.computedState  = dict()
		self.stateInFPGA    = dict()
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
		self.event2action  = {}
		for keyword, events in self.keyword2events.items():
			for event in events:
				self.event2action[event] = []
		
		logger.debug("initialized " + str(self))
		
	def computeDicts(self, recursive = True):
		logger.debug("computing dicts " + str(self))
		self.allChildren = []
		self.sensitivity = {}
		for membername, member in inspect.getmembers(self):
			# sometimes they may be elements of a list
			try:
				if isinstance(member,list):
					for v in member:
						if (isinstance(v, FPGA_component)):
							#logger.debug("child " + str(v))
							self.allChildren += [v]
				
				# if its a function starting with fn
				if membername.startswith("fn_") and callable(member):
					#logger.debug("found function " + membername)
					for keyword, events in self.keyword2events.items():
						for event in events:
							if keyword in inspect.getsource(member):
								self.event2action[event] += [(membername.replace("fn_", "cmd_"), member)]
			except:
				pass
		
		if recursive:
			for child in self.allChildren:
				child.computeDicts()
		
	def computeAndSendEvent(event):
		for actionTuple in self.event2action[event]:
			self.send(actionTuple[0], actionTuple[1])
	
	def computeAndSendAll(self):
		logger.debug("updating all")
		
		# run ALL the Actions!
		for event, actionList in self.event2action.items():
			for actionTuple in actionList:
				logger.debug("action " + str(actionTuple))
				self.computeAndSend(actionTuple)
		
		#send to all children that are of type FPGA_component
		for child in self.allChildren:
			child.computeAndSendAll()
		
	def compute(self, param, fn):
		self.computedState[param] = fn()
		
	def computeAndSend(self, actionTuple):
		param, fn = actionTuple
		self.compute(param, fn)
		# only write the thing if it changed
		if self.computedState[param] != self.stateInFPGA.get(param):
			self.stateInFPGA[param] = self.computedState[param]
			logger.debug(param)
			self.send(param)
		else:
			pass
			#logger.debug("Not sending")
			
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
		self.control     = np.ones((CONTROLCOUNT), dtype=int) * 128
		
		self.voicesPerNote = 1
		self.polyphony  = 4
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
	
	
	
	def processEvent(self, msg):
	
		logger.debug("processing " + msg.type)
		voices = self.voices
			
		msgtype = msg.type
		voicesToUpdate = self.voices
		event = msg.type
		
		if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
			note = self.allNotes[msg.note] 
			note.velocity = 0 
			note.voices = []
			note.held = False
			
			voicesToUpdate = note.voices
			
			# implement rising mono porta
			for heldnote in self.allNotes[::-1]:
				if heldnote.held and self.polyphony == self.voicesPerNote :
					self.processEvent(heldnote.msg)
					break
				
				
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
			event = "control[" + msg.control + "]"
			
		elif msg.type == 'polytouch':
			self.allNotes[msg.note].polytouch = msg.value
			note = self.allNotes[msg.note]
			voicesToUpdate = note.voices
			
		elif msg.type == 'aftertouch':
			self.aftertouch = msg.value
						
		for voice in voicesToUpdate:
			voice.computeAndSendEvent(event)


class Channel(FPGA_component):
	def __init__(self, voice, index, fpga_interface_inst):
		super().__init__(index, fpga_interface_inst)
		self.voice = voice
		self.cmdName2number["cmd_voicegain"]      = 75
		self.fpga_interface_inst = fpga_interface_inst
		
		
	def fn_voicegain (self)   : return  2**16 
	
	def send(self, param):
		self.fpga_interface_inst.send(self.cmdName2number[param], self.index, self.voice.index, self.computedState[param])

class Voice(FPGA_component):
		
	def __init__(self, index, fpga_interface_inst):
		super().__init__(index, fpga_interface_inst)
		
		self.cmdName2number["cmd_algorithm"]  = 70
		self.cmdName2number["cmd_am_algo"  ]  = 71
		self.cmdName2number["cmd_fbgain"   ]  = 73
		self.cmdName2number["cmd_fbsrc"    ]  = 74
	
		self.index = index
		self.note = None
		self.patch  = None
		self.sounding = False    
		self.defaultIncrement = 0
		self.indexInCluster = 0
		self.OPERATORCOUNT  = 8
		self.operators = []
		self.operators += [Operator0(self, 0, fpga_interface_inst)]
		self.operators += [Operator1(self, 1, fpga_interface_inst)]
		self.operators += [Operator2(self, 2, fpga_interface_inst)]
		self.operators += [Operator3(self, 3, fpga_interface_inst)]
		self.operators += [Operator4(self, 4, fpga_interface_inst)]
		self.operators += [Operator5(self, 5, fpga_interface_inst)]
		self.operators += [Operator6(self, 6, fpga_interface_inst)]
		self.operators += [Operator7(self, 7, fpga_interface_inst)]
		
		self.channels = []
		self.channels += [Channel(self, 0, fpga_interface_inst)]
		self.channels += [Channel(self, 1, fpga_interface_inst)]
		
			
	def fn_algorithm (self)         : return 0x00000001
	def fn_am_algo (self)           : return 0x00000000
	def fn_fbgain (self)            : return 0x00000000
	def fn_fbsrc (self)             : return 0x00000000

	def send(self, param):
		self.fpga_interface_inst.send(self.cmdName2number[param], 0, self.index, self.computedState[param])

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
		super().__init__(index, fpga_interface_inst)
		
		self.fpga_interface_inst = fpga_interface_inst
		self.voice = voice
		self.algorithm = 0
		
		self.cmdName2number["cmd_env"            ] = 75 
		self.cmdName2number["cmd_env_porta"      ] = 76 
		self.cmdName2number["cmd_envexp"         ] = 77 
		self.cmdName2number["cmd_increment"      ] = 78 
		self.cmdName2number["cmd_increment_porta"] = 79 
		self.cmdName2number["cmd_incexp"         ] = 80 
				

	def fn_env_porta      (self) : return 2**4                                                        
	def fn_env            (self) : return 0                      
	def fn_increment      (self) : return self.voice.patch.pitchwheel * self.voice.note.defaultIncrement * (2 ** (self.voice.indexInCluster - (self.voice.patch.voicesPerNote-1)/2)) * (1 + self.voice.patch.aftertouch/128.0)
	def fn_increment_porta(self) : return 2**22*(self.voice.patch.control[4]/128.0)                          
	def fn_incexp         (self) : return 1                                                            
	def fn_envexp         (self) : return 1                                                            

	def send(self, param):
		self.fpga_interface_inst.send(self.cmdName2number[param], self.index, self.voice.index, self.computedState[param])

		
		
class Operator0(Operator):	
	def fn_fmdepth       (self) : return 2**14*(self.voice.note.polytouch)
	def fn_env           (self) : return self.voice.note.velocity*(2**16)/128.0          
	def __init__(self, voice, index, fpga_interface_inst):
		super().__init__(voice, index, fpga_interface_inst)
class Operator1(Operator):	
	def __init__(self, voice, index, fpga_interface_inst):
		super().__init__(voice, index, fpga_interface_inst)
class Operator2(Operator):	
	def __init__(self, voice, index, fpga_interface_inst):
		super().__init__(voice, index, fpga_interface_inst)
class Operator3(Operator):	
	def __init__(self, voice, index, fpga_interface_inst):
		super().__init__(voice, index, fpga_interface_inst)
class Operator4(Operator):	
	def __init__(self, voice, index, fpga_interface_inst):
		super().__init__(voice, index, fpga_interface_inst)
class Operator5(Operator):	
	def __init__(self, voice, index, fpga_interface_inst):
		super().__init__(voice, index, fpga_interface_inst)
class Operator6(Operator):	
	def __init__(self, voice, index, fpga_interface_inst):
		super().__init__(voice, index, fpga_interface_inst)
class Operator7(Operator):	
	def __init__(self, voice, index, fpga_interface_inst):
		super().__init__(voice, index, fpga_interface_inst)

		
			
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

		self.cmdName2number["cmd_env_clkdiv"       ] = 99
		self.cmdName2number["cmd_flushspi"         ] = 120
		self.cmdName2number["cmd_passthrough"      ] = 121
		self.cmdName2number["cmd_shift"            ] = 122
		
		self.computeDicts(recursive = False)
	
	def fn_env_clkdiv () : return 5
	def fn_flushspi   () : return 0
	def fn_passthrough() : return 0
	def fn_shift      () : return 5
	
	def getVoices(self, controlPatch, voicesToGet = 32):
		toreturn = []
		with ILock('jlock'):
			for i in range(voicesToGet):
				toreturn += [self.voices[self.voiceno]]
				self.voices[self.voiceno].controlPatch = controlPatch
				self.voiceno += 1
		return toreturn
		
	def send(self, param):
		self.fpga_interface_inst.send(self.cmdName2number[param], 0, 0, self.computedState[param])


class fpga_interface():
	def format_command_real(self, mm_paramno, voiceno,  payload):
		payload = payload*(2**16)
		payload = struct.pack(">I", int(payload))
		payload = [mm_paramno, 0, 0, voiceno] + [int(i) for i in payload]
		#print([hex(p) for p in payload])
		return payload
		
	def format_command_word(self, mm_paramno, mm_opno,  voiceno, voicemode = 0):
		payload_array = [mm_paramno, 1 << mm_opno, (voicemode << 7) | (voiceno >> 8), voiceno]
		#print([hex(p) for p in payload_array])
		return payload_array
		
	def format_command_int(self, mm_paramno, mm_opno,  voiceno,  payload, voicemode = 0):
		payload_packed = struct.pack(">I", int(payload))
		payload_array = [mm_paramno, 1 << mm_opno, (voicemode << 7) | (voiceno >> 8), voiceno] + [int(i) for i in payload_packed] 
		#print([hex(p) for p in payload_array])
		return payload_array
		
	def format_command_3bezier_targets(self, mm_paramno, voiceno,  bt0, bt1, bt2):
		payload = struct.pack(">I", (int(bt0*(2**28)) & 0x3FF00000) + (int(bt1*(2**18)) & 0x000FFC00) + (int(bt2*(2**8)) & 0x000003FF))
		payload = [mm_paramno, 0, 0, voiceno] + [int(p) for p in payload]
		#print([hex(p) for p in payload])
		return payload
		
	def sendMultiple(self, param, opno, voiceno, payload, voicemode = 0):
		packstring = ">" + str(int(len(payload)/4)) + "I"
		payload = np.array(payload, dtype=np.int)
		payload_packed = struct.pack(packstring, *payload)
		tosend = self.format_command_int(self.cmdName2number[param], opno, voiceno, 0)
		with ILock('jlock'):
			print("tslen: " + str(len(tosend[:4])))
			spi.xfer2(tosend[:4] + payload_packed)
			#logger.debug("sent")
	
	def send(self, paramno = 0, mm_opno = 0,  voiceno = 0,  payload = 0):
		tosend = self.format_command_int(paramno, mm_opno, voiceno, payload)
		with ILock('jlock'):
			logger.debug(str(paramno) + " operator:" + str(mm_opno) + " voice:" + str(voiceno) + " payload:" + str(payload))
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
		