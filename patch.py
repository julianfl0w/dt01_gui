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
import traceback
 
import logging
logger = logging.getLogger('DT01')

MIDINOTES      = 128
CONTROLCOUNT   = 128

class Voice(DT01_Voice):

	def __init__(self, index, dt01_inst):
		super().__init__(voice, index, dt01_inst)

	def fn_mastergain_right(self)   : return  2**16 
	def fn_mastergain_left (self)   : return  2**16 
	def fn_algorithm (self)         : return 0x00000001

	def __unicode__(self):
		return "#" + str(self.index)

	def __str__(self):
		return "#" + str(self.index)

# heirarchy:
# patch controls
# voice controls
# operator
		
class Operator0(DT01_Operator):	
	def setFMDepth(self)       : self.send("cmd_fmdepth"        ,  payload = int(2**14 * (self.voice.patch.control[1]/128.0)))
	def __init__(self, voice, index, dt01_inst):
		super().__init__(voice, index, dt01_inst)
class Operator1(DT01_Operator):	
	def __init__(self, voice, index, dt01_inst):
		super().__init__(voice, index, dt01_inst)
class Operator2(DT01_Operator):	
	def __init__(self, voice, index, dt01_inst):
		super().__init__(voice, index, dt01_inst)
class Operator3(DT01_Operator):	
	def __init__(self, voice, index, dt01_inst):
		super().__init__(voice, index, dt01_inst)
class Operator4(DT01_Operator):	
	def __init__(self, voice, index, dt01_inst):
		super().__init__(voice, index, dt01_inst)
class Operator5(DT01_Operator):	
	def __init__(self, voice, index, dt01_inst):
		super().__init__(voice, index, dt01_inst)
class Operator6(DT01_Operator):	
	def __init__(self, voice, index, dt01_inst):
		super().__init__(voice, index, dt01_inst)
class Operator7(DT01_Operator):	
	def __init__(self, voice, index, dt01_inst):
		super().__init__(voice, index, dt01_inst)

		
# patch holds all state, including note and control state
class Patch:

	def __init__(self, dt01_inst):
		# each patch has its own controls so they can be independantly initialized
		self.control     = np.ones((CONTROLCOUNT), dtype=int) * 128
		
		self.voicesPerNote = 1
		self.polyphony = 32
		self.dt01_inst  = dt01_inst
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
			
		self.voices = self.dt01_inst.getVoices(self, self.polyphony)
		
		for voice in self.voices:
			logger.debug("claimed: " + str(voice.index))
			voice.computeAndSendAll()
			voice.note  = self.allNotes[0]
			voice.patch = self
			voice.computeAndSendAll()
				
		self.toRelease   = []
	
		logger.debug("init ")
		
		# initialize all voices
		for voice in self.voices:
			voice.computeAndSendAll()
	
	
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
				voice.pitchwheel()
				
		elif msg.type == 'control_change':
			self.control[msg.control] = msg.value
			for voice in self.voices:
				voice.control_change()
			
		elif msg.type == 'polytouch':
			self.allNotes[msg.index].polytouch = msg.value
			note = self.allNotes[msg.note]
			for voice in note.voices:
				voice.polytouch()
			
		elif msg.type == 'aftertouch':
			self.aftertouch = msg.value
			for voice in self.voices:
				voice.aftertouch()
			
		elif msg.type == 'note_off':
			note = self.allNotes[msg.note]
			note.velocity = 0
			note.held = False
			for voice in note.voices:
				voice.note_off()
			
			

