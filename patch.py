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
		
		self.allNotes = []
		for i in range(MIDINOTES):
			self.allNotes+= [Note(i)]
		for voicetoclaim in range(self.polyphony):
			claimedVoice = self.midiInputInst.dt01_inst.getVoice(self)
			logger.debug("claimed: " + str(claimedVoice.index))
			claimedVoice.controlNote = self.allNotes[0]
			self.voices += [claimedVoice]
			
		self.toRelease   = []
	
		logger.debug("init ")
		
		#initialize some controls
		self.control[1]  = 128
		self.control[2]  = 128
		self.control[3]  = 64
		self.control[4] = 128
		
		# initialize all voices
		for voice in self.voices:
			for operator in range(2):
				# fuck it, call em all
				for command in self.dt01_inst.cmdDict.keys():
					try: 
						self.sendParam(None, voice, command, operator)
					except:
						print("missed one: " + command)
				#voice.send("cmd_mastergain_right", 0, int(2**16))
				#voice.send("cmd_mastergain_left" , 0, int(2**16))
				#self.sendParam(None, voice, "cmd_increment_porta", 0)
				#self.sendParam(None, voice, "cmd_increment_porta", 1)
				#self.sendParam(None, voice, "cmd_gain_porta", 0)
				#self.sendParam(None, voice, "cmd_gain_porta", 1)
	
	def sendParam(self, msg, voice, command, operator):
		payload = 2**16
		if command == "cmd_fmdepth"           :
			if operator == 0:
				#payload = int(2**14 * (self.control[1]/128.0))
				payload = 0
			else:
				payload = 0
		elif command == "cmd_fmmod_selector"    :
			if operator == 0:
				payload = voice.getFmMod(operator, 1) # operator 1 is the FM mod for this operator
			else:
				payload = 0
				
		elif command == "cmd_ammod_selector"    :
			payload = 0
		elif command == "cmd_gain"              :
			if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
				payload = 0
			else:
				payload = int(2**16 * (self.control[2]/128.0))
		elif command == "cmd_gain_porta"        :
			payload = 2**28
		elif command == "cmd_increment"         :
			payload = 2**26
			#if operator == 0:
			#	payload = self.pitchwheel * voice.controlNote.defaultIncrement * (2 ** (voice.indexInCluster - (self.voicesPerNote-1)/2)) * (1 + self.aftertouch/128.0)
			#else:
			#	payload = self.pitchwheel * voice.controlNote.defaultIncrement * (2**int((self.control[3] -64) / 16)) * (1 + self.aftertouch/128.0) * (2 ** (voice.indexInCluster - (self.voicesPerNote-1)/2))
		
		elif command == "cmd_increment_porta"   :
			#payload = 2**28*(self.control[4]/128.0)
			payload = 2**28
		elif command == "cmd_mastergain_right"  :
			payload = 2**16
		elif command == "cmd_mastergain_left"   :
			payload = 2**16
		elif command == "cmd_incexp"            :
			payload = 1
		elif command == "cmd_gainexp"           :
			payload = 1
		elif command == "cmd_env_clkdiv"        :
			#payload = 8
			payload = 0
		elif command == "cmd_flushspi"          :
			payload = 0
		elif command == "cmd_passthrough"       :
			payload = 0
		elif command == "cmd_shift"             :
			payload = 5
			
		voice.send(command, operator, payload)
	
	def processEvent(self, msg):
	
		logger.debug("processing " + msg.type)
		voices = self.voices
			
		msgtype = msg.type
		
		if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
			note = self.allNotes[msg.note] 
			note.velocity = 0
			for voice in note.controlledVoices:
				voice.controlNote = None
				self.sendParam(msg, voice, "cmd_gain", 0)
				self.sendParam(msg, voice, "cmd_gain", 1)

			note.controlledVoices = []
			note.held = False
			
			# implement rising mono porta
			for note in self.allNotes[::-1]:
				if note.held and self.polyphony == self.voicesPerNote :
					self.processEvent(note.msg)
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
				self.currVoice.controlNote = note
				self.currVoice.sounding = True
				self.currVoice.indexInCluser = voiceno
				note.controlledVoices += [self.currVoice]
				
				self.sendParam(msg, self.currVoice, "cmd_gain",      0)
				self.sendParam(msg, self.currVoice, "cmd_increment", 0)
				self.sendParam(msg, self.currVoice, "cmd_gain",      1)
				self.sendParam(msg, self.currVoice, "cmd_increment", 1)
					
				
				
		elif msg.type == 'pitchwheel':
			logger.debug("PW: " + str(msg.pitch))
			amountchange = msg.pitch / 8192.0
			self.pitchwheel = pow(2, amountchange)
			for voice in self.voices:
				self.sendParam(msg, voice, "cmd_increment", 0)
				self.sendParam(msg, voice, "cmd_increment", 1)
			
		elif msg.type == 'control_change':
			self.control[msg.control] = msg.value
			#if msg.control == 1:
			#	for voice in self.voices:
			#		self.sendParam(msg, voice, "cmd_fmdepth", 0)
			#if msg.control == 2:
			#	for voice in self.voices:
			#		self.sendParam(msg, voice, "cmd_gain", 0)
			
			
		elif msg.type == 'polytouch':
			self.allNotes[msg.index].polyAftertouch = msg.value
			
		elif msg.type == 'aftertouch':
			self.aftertouch = msg.value
			for voice in self.voices:
				self.sendParam(msg, voice, "cmd_increment", 0)
				self.sendParam(msg, voice, "cmd_increment", 1)
			
		elif msg.type == 'note_off':
			self.routine_noteoff(msg)
