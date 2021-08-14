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
import logging
import threading
import faulthandler
from note import *
from voice import *
import traceback

faulthandler.enable()
 
logger = logging.getLogger('DT01')

MIDINOTES      = 128
CONTROLCOUNT   = 128

class Patch:

	def __init__(self, midiInputInst, dt01_inst):
		# each patch has its own controls so they can be independantly initialized
		self.control     = np.zeros((CONTROLCOUNT), dtype=int)
		
		self.voicesPerNote = 1
		self.polyphony = 1
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
		for voicetoclaim in range(self.polyphony):
			claimedVoice = self.midiInputInst.dt01_inst.getVoice(self)
			claimedVoice.patch = self
			logger.debug("claimed: " + str(claimedVoice.index))
			claimedVoice.note = self.allNotes[0]
			self.voices += [claimedVoice]
			claimedVoice.setAll()
			
		self.toRelease   = []
	
		logger.debug("init ")
		
		
		#with open(os.path.join(sys.path[0], "global.json")) as f:
		#	globaldict = json.loads(f.read())
		#
		#for key, value in globaldict.items():
		#	 dt01_inst.send(key , 0, 0, value)
		dt01_inst.send("cmd_shift",    0, 0, 2)
		dt01_inst.send("cmd_flushspi", 0, 0, 0)
		dt01_inst.send("cmd_env_clkdiv", 0, 0, 2)
	
		# initialize all voices
		for voice in self.voices:
			voice.operators[0].fmmod_selector = 1
			voice.setAll()
				
	def processEvent(self, msg):
	
		logger.debug("processing " + msg.type)
		voices = self.voices
			
		msgtype = msg.type
		
		if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
			note = self.allNotes[msg.note] 
			note.velocity = 0
			for voice in note.controlledVoices:
				voice.operators[0].setGain()
				voice.operators[1].setGain()
				
			note.controlledVoices = []
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
				logger.debug("applying to " + str(self.currVoice))
				self.currVoice.note = note
				self.currVoice.sounding = True
				self.currVoice.indexInCluser = voiceno
				note.controlledVoices += [self.currVoice]
				
				self.currVoice.operators[0].setGain()
				self.currVoice.operators[0].setIncrement()
				self.currVoice.operators[1].setGain()
				self.currVoice.operators[1].setIncrement()
					
				
				
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
