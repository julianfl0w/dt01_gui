import struct
import sys
import numpy as np 
from dt01 import dt01
import time
import rtmidi
from rtmidi.midiutil import *
import mido
import math
import hjson as json
import socket
import os
from note  import *
from voice import *
import traceback
 
import logging
logger = logging.getLogger('DT01')

MIDINOTES      = 128
CONTROLCOUNT   = 128

class Patch:

	def __init__(self, midiInputInst, dt01_inst):
		# each patch has its own controls so they can be independantly initialized
		self.control     = np.zeros((CONTROLCOUNT), dtype=int)
		
		self.voicesPerNote = 1
		self.polyphony = 32
		self.dt01_inst  = dt01_inst
		self.midiInputInst = midiInputInst
		self.voices = []
		self.currVoiceIndex = 0
		self.currVoice = 0
		self.pitchwheel  = 1
		self.aftertouch = 0
		
		#initialize some controls
		self.control[1]  = 128
		self.control[2]  = 128
		self.control[3]  = 64
		self.control[4] = 128
		
		self.allNotes = []
		for i in range(MIDINOTES):
			self.allNotes+= [Note(i)]
			
		self.voices = self.dt01_inst.getVoices(self, self.polyphony)
		
		for voice in self.voices:
			logger.debug("claimed: " + str(voice.index))
			voice.updateAll()
			voice.note  = self.allNotes[0]
			voice.patch = self
			voice.updateAll()
				
		self.toRelease   = []
	
		logger.debug("init ")
		
		#with open(os.path.join(sys.path[0], "global.json")) as f:
		#	globaldict = json.loads(f.read())
		#
		#for key, value in globaldict.items():
		#	 dt01_inst.send(key , 0, 0, value)
	
		# initialize all voices
		for voice in self.voices:
			voice.operators[0].algorithm = 1
			voice.updateAll()
	
	
	def processEvent(self, msg):
	
		logger.debug("processing " + msg.type)
		voices = self.voices
			
		msgtype = msg.type
		
		if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
			note = self.allNotes[msg.note] 
			note.velocity = 0 
			for voice in note.voices:
				voice.note_off()
			note.voices = []
			note.held = False
			
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
				self.currVoice.note_on()
				
				
		elif msg.type == 'pitchwheel':
			logger.debug("PW: " + str(msg.pitch))
			amountchange = msg.pitch / 8192.0
			self.pitchwheel = pow(2, amountchange)
			for voice in self.voices:
				for operator in voice.operators:
					operator.setIncrement()
				
		elif msg.type == 'control_change':
			self.control[msg.control] = msg.value
			if msg.control == 1:
				for voice in self.voices:
					for operator in voice.operators:
						operator.setFMDepth()
			if msg.control == 2:
				for voice in self.voices:
					for operator in voice.operators:
						operator.setGain()
			if msg.control == 4:
				for operator in voice.operators:
					operator.setIncrementPorta()
			
			
		elif msg.type == 'polytouch':
			self.allNotes[msg.index].polyAftertouch = msg.value
			
		elif msg.type == 'aftertouch':
			self.aftertouch = msg.value
			for voice in self.voices:
				for operator in voice.operators:
					operator.setIncrement()
			
		elif msg.type == 'note_off':
			self.routine_noteoff(msg)
			
		class Operator0(Operator):	
			def setFMDepth(self)       : self.send("cmd_fmdepth"        ,  payload = int(2**14 * (self.voice.patch.control[1]/128.0)))
			def __init__(self, voice, index, dt01_inst):
				super().__init__(voice, index, dt01_inst)
		class Operator1(Operator):	
			def __init__(self, voice, index, dt01_inst):
				super().__init__(voice, index, dt01_inst)
		class Operator2(Operator):	
			def __init__(self, voice, index, dt01_inst):
				super().__init__(voice, index, dt01_inst)
		class Operator3(Operator):	
			def __init__(self, voice, index, dt01_inst):
				super().__init__(voice, index, dt01_inst)
		class Operator4(Operator):	
			def __init__(self, voice, index, dt01_inst):
				super().__init__(voice, index, dt01_inst)
		class Operator5(Operator):	
			def __init__(self, voice, index, dt01_inst):
				super().__init__(voice, index, dt01_inst)
		class Operator6(Operator):	
			def __init__(self, voice, index, dt01_inst):
				super().__init__(voice, index, dt01_inst)
		class Operator7(Operator):	
			def __init__(self, voice, index, dt01_inst):
				super().__init__(voice, index, dt01_inst)

