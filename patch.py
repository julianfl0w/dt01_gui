import spidev
import struct
#maxSpiSpeed = 120000000
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
import pickle
import dt01
import logging
import collections
import math
logger = logging.getLogger('DT01')
	
MIDINOTES      = 128
CONTROLCOUNT   = 128

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
		
# patch holds all state, including note and control state
class Patch():
					
	def send(self, param, value):
		self.fpga_interface_inst.send(param, 0, 0, value)
	
	def processControl(self, paramName, value):
		self.processEvent(mido.Message('control_change', control = dt01.paramName2Num [paramName], value = value)) #
		
	def __init__(self, dt01_inst):
		logger.debug("patch init ")
		self.dt01_inst = dt01_inst
		self.fpga_interface_inst  = dt01_inst.fpga_interface_inst
		self.polyphony = 32
		self.active = True
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
			
		self.opno = 0
		self.voices = dt01_inst.getVoices()

		self.allChildren = self.voices
	
		for voice in self.voices:
			#logger.debug("claimed: " + str(voice.index))
			voice.note  = self.allNotes[0]
			voice.patch = self
				
		self.toRelease   = []
	
		self.control = [0]*CONTROLCOUNT
		
		# set default control values
		self.control[dt01.paramName2Num["vibrato_env"     ]] = 0   #
		self.control[dt01.paramName2Num["tremolo_env"     ]] = 0   #
		self.control[dt01.paramName2Num[ "fbgain"         ]] = 0  
		self.control[dt01.paramName2Num[ "fbsrc"          ]] = 0  
		self.control[dt01.paramName2Num[ "baseincrement"  ]] = 127     # 
		self.control[dt01.paramName2Num[ "expression"     ]] = 0   # common midi control
		
		self.control[dt01.paramName2Num["env"             ]] = 0 #
		self.control[dt01.paramName2Num["env_porta"       ]] = 64  #
		self.control[dt01.paramName2Num["envexp"          ]] = 1   #
		self.control[dt01.paramName2Num["increment"       ]] = 64  #
		self.control[dt01.paramName2Num["increment_porta" ]] = 0   #
		self.control[dt01.paramName2Num["incexp"          ]] = 1   #
		self.control[dt01.paramName2Num["fmsrc"           ]] = 7   #fm off
		self.control[dt01.paramName2Num["amsrc"           ]] = 0   #am off
		self.control[dt01.paramName2Num["static"          ]] = 0   #
		self.control[dt01.paramName2Num["sounding"        ]] = 0   #
		
		self.control[dt01.paramName2Num["sustain"         ]] = 0  # common midi control
		self.control[dt01.paramName2Num["portamento"      ]] = 0  # common midi control
		self.control[dt01.paramName2Num["filter_resonance"]] = 0  # common midi control
		self.control[dt01.paramName2Num["filter_cutoff"   ]] = 0  # common midi control
		
		self.control[dt01.paramName2Num["env_clkdiv"      ]] = 16  #   
		self.control[dt01.paramName2Num["flushspi"        ]] = 0   #   
		self.control[dt01.paramName2Num["passthrough"     ]] = 0   #   
		self.control[dt01.paramName2Num["shift"           ]] = 3   #   
		
		
		self.controlReal = [0]*CONTROLCOUNT

		# establish defaults
		self.paramName2Val = {}
		self.paramName2Real= {}
		
		self.paramName2Val ["operator"] = {}
		self.paramName2Real["operator"] = {}
		for paramName in dt01.controlNum2ParamName:
			self.paramName2Val [paramName] = self.control[dt01.paramName2Num[paramName]]
			self.paramName2Real[paramName] = self.control[dt01.paramName2Num[paramName]] / 127.0
			
			# and again for each operator
			self.paramName2Val ["operator"][paramName] = [self.paramName2Val [paramName]]*dt01.OPERATORCOUNT
			self.paramName2Real["operator"][paramName] = [self.paramName2Real[paramName]]*dt01.OPERATORCOUNT
				
		#			
		#self.processEvent(mido.Message('pitchwheel', pitch = 64))
		#self.processEvent(mido.Message('aftertouch', value = 0))
		#for note in self.allNotes:
		#	self.processEvent(mido.Message('polytouch', note = note.index, value = 0))
		#	
		##self.processEvent(mido.Message('control_change', control = 114, value = 0)) #
	
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
			for voice in note.voices:
				voice.spawntime = 0
			note.voices = []
			note.held = False
			
	def getCurrOpParam2Real(self, index, paramName):
		return self.paramName2Real["operator"][paramName][index]
			
	def processEvent(self, msg):
	
		logger.debug("Processing " + str(msg))
	
		if msg.type == "note_on" or msg.type == "note_off":
			note = self.allNotes[msg.note]
			
		if msg.type == "note_on":
			note.velocity = msg.velocity
			note.velocityReal = msg.velocity/127.0
			note.held = True
			note.msg = msg
			# spawn some voices!
			for voiceno in range(self.voicesPerNote):
				
				#self.currVoiceIndex = (self.currVoiceIndex + 1) % self.polyphony
				#logger.debug([s.spawntime for s in self.voices])
				oldestVoiceInPatch = sorted(self.voices, key=lambda x: x.spawntime)[0]
				oldestVoiceInPatch.spawntime = time.time()
				oldestVoiceInPatch.indexInCluser = voiceno
				oldestVoiceInPatch.note = note
				note.voices += [oldestVoiceInPatch]
				oldestVoiceInPatch.send("cmd_baseincrement", self.paramName2Real["baseincrement"] * self.pitchwheelReal * (1 + self.aftertouchReal) * note.defaultIncrement * 2**6)
		
		if msg.type == "note_on" or msg.type == "note_off":
			for voice in note.voices:
				self.fpga_interface_inst.gather(False)
				for operator in voice.operators:
					if operator.static:
						operator.send("cmd_env"            , (2**16) * self.getCurrOpParam2Real(operator.index, "env")               )
					else:
						operator.send("cmd_env"            , note.velocityReal * (2**16) * self.getCurrOpParam2Real(operator.index, "env"))
				
				self.fpga_interface_inst.release()
				
		if msg.type == 'pitchwheel':
			logger.debug("PW: " + str(msg.pitch))
			self.pitchwheel = msg.pitch
			amountchange = msg.pitch / 8192.0
			self.pitchwheelReal = pow(2, amountchange)
			logger.debug("PWREAL " + str(self.pitchwheelReal))
			for voice in self.allVoices:
				voice.send("cmd_baseincrement", self.paramName2Real["baseincrement"] * self.pitchwheelReal * (1 + self.aftertouchReal) * voice.note.defaultIncrement * 2**6)
		
				
		elif msg.type == 'control_change':
			
			self.control[msg.control]     = msg.value
			self.controlReal[msg.control] = msg.value/127.0
			
			logger.debug("control : " + str(msg.control) + " (" + dt01.controlNum2ParamName[msg.control] +  "): " + str(msg.value))

			self.fpga_interface_inst.gather()
			event = "control[" + str(msg.control) + "]"
			
			# patch stores control vals for each operator
			self.paramName2Val [dt01.controlNum2ParamName[msg.control]] = msg.value
			self.paramName2Real[dt01.controlNum2ParamName[msg.control]] = msg.value/127.0
			self.paramName2Val ["operator"][dt01.controlNum2ParamName[msg.control]][self.opno] = msg.value
			self.paramName2Real["operator"][dt01.controlNum2ParamName[msg.control]][self.opno] = msg.value/127.0


			# forward some controls
			# PUT THIS BACK
			
			#if msg.control == 0:
			#	self.processEvent(mido.Message('control_change', control= dt01.paramName2Num["opno"      ], value = 6 ))
			#	self.processEvent(mido.Message('control_change', control= dt01.paramName2Num["env"      ], value = msg.value ))
			#if msg.control == 1:
			#	self.processEvent(mido.Message('control_change', control= dt01.paramName2Num["opno"      ], value = 7 ))
			#	self.processEvent(mido.Message('control_change', control= dt01.paramName2Num["env"      ], value = msg.value ))
			
			# route control3 to control 7 because sometimes 3 is volume control
			if msg.control == 3:
				self.processEvent(mido.Message('control_change', control= 7, value = msg.value ))
				
			if msg.control == ["env_clkdiv"]:
				self.send("cmd_env_clkdiv" , self.paramName2Val["env_clkdiv"])
				
			if msg.control == dt01.paramName2Num["flushspi"]:
				self.send("cmd_flushspi", self.paramName2Val["flushspi"])
				
			if msg.control == dt01.paramName2Num["passthrough"]:
				self.send("cmd_passthrough", self.paramName2Val["passthrough"])
				
			if msg.control == dt01.paramName2Num["shift"]:
				self.send("cmd_shift" , self.paramName2Val["shift"])
				
				
			# selection
			if msg.control == dt01.paramName2Num["opno"]:
				self.opno = msg.value
				
			if msg.control == dt01.paramName2Num["tremolo_env"]:
				voice.operators[6].send("env"             , msg.value) #
				
			if msg.control == dt01.paramName2Num["vibrato_env"]:
				voice.operators[7].send("env"             , msg.value) #
			
			self.fpga_interface_inst.gather()
			for voice in self.voices:
			
				# OPERATOR CONCERNS
				# get active operator
				channel  = voice.channels[self.opno]
				operator = voice.operators[self.opno]
				
				if msg.control == dt01.paramName2Num["voicegain"] or msg.control == dt01.paramName2Num["pan"] : 
					baseVolume = 2**16*self.paramName2Real["voicegain"]
					if self.opno == 0:
						channel.send("cmd_channelgain", baseVolume*self.paramName2Real["pan"]) # assume 2 channels
					else:
						#logger.debug(self.controlReal[10])
						channel.send("cmd_channelgain", baseVolume*(1 - self.paramName2Real["pan"])) # assume 2 channels
	
				# FM Algo
				if msg.control == dt01.paramName2Num["fmsrc"]:
					operator.fmsrc = msg.value
					sendVal = 0
					for i in reversed(range(voice.OPERATORCOUNT)):
						sendVal = int(sendVal) << int(math.log2(voice.OPERATORCOUNT))
						sendVal += int(voice.operators[i].fmsrc)
						#logger.debug(bin(sendVal))
					voice.send("cmd_fm_algo", sendVal)
				
				#am algo
				if msg.control == dt01.paramName2Num["amsrc"]:
					sendVal = 0
					for i in reversed(range(voice.OPERATORCOUNT)):
						sendVal = int(sendVal) << int(math.log2(voice.OPERATORCOUNT))
						sendVal += int(voice.operators[i].amsrc)
						#logger.debug(bin(sendVal))
					voice.send("cmd_am_algo", sendVal)
					
				if msg.control == dt01.paramName2Num["fbgain"]:
					voice.send("cmd_fbgain"   , 2**16 * self.paramName2Real["fbgain"]  )
					
				if msg.control == dt01.paramName2Num["fbsrc"]:
					voice.send("cmd_fbsrc"    , self.paramName2Val["fbsrc"]   )
		
				if msg.control == dt01.paramName2Num["sounding"]: 
					operator.sounding = msg.value
					sendVal = 0
					for i in reversed(range(dt01.OPERATORCOUNT)):
						sendVal = int(sendVal) << 1
						sendVal += int(voice.operators[i].sounding)
						#logger.debug(bin(sendVal))
					voice.send("cmd_sounding", sendVal)
					
				if msg.control == dt01.paramName2Num["static"]: 
					operator.static = msg.value
					sendVal = 0
					for i in reversed(range(voice.OPERATORCOUNT)):
						sendVal = int(sendVal) << 1
						sendVal += int(voice.operators[i].static)
					voice.send("cmd_static", sendVal)
		
				if msg.control == dt01.paramName2Num["env"]: 
					if operator.index < 6:
						operator.send("cmd_env"            , voice.note.velocityReal * (2**16) * self.getCurrOpParam2Real(operator.index, "env"))
					else:
						operator.send("cmd_env"            , (2**16) * self.getCurrOpParam2Real(operator.index, "env"))
						
				if msg.control == dt01.paramName2Num["env_porta"]: 
					operator.send("cmd_env_porta"      , 2**10 * (1 - self.getCurrOpParam2Real(operator.index, "env_porta")) * (1 - self.paramName2Real["portamento"]) )
		# static oscillators do not have velocity-dependant env
					
				if msg.control == dt01.paramName2Num["increment"]: 
					if operator.index < 6:
						operator.send("cmd_increment"      , 2**10 * self.getCurrOpParam2Real(operator.index, "increment")) # * self.getCurrOpParam2Real(operator.index, "increment")
					else:
						operator.send("cmd_increment"      , 2**3 * self.getCurrOpParam2Real(operator.index, "increment")) # * self.getCurrOpParam2Real(operator.index, "increment")
					
				if msg.control == dt01.paramName2Num["increment_porta"]: 
					operator.send("cmd_increment_porta", 2**10 * (1 - self.paramName2Real["portamento"]) * (1 - self.getCurrOpParam2Real(operator.index, "increment_porta")))
					
				if msg.control == dt01.paramName2Num["incexp"]: 
					operator.send("cmd_incexp"         , self.paramName2Val["operator"]["incexp"][self.opno])  
					
				if msg.control == dt01.paramName2Num["envexp"]: 
					operator.send("cmd_envexp"         , self.paramName2Val["operator"]["envexp"][self.opno])
					
				if msg.control == dt01.paramName2Num["fmsrc"]: 
					self.fmsrc = self.paramName2Val["fmsrc"]
					
				if msg.control == dt01.paramName2Num["amsrc"]:
					self.amsrc  = self.paramName2Val["amsrc"]
					
				if msg.control == dt01.paramName2Num["static"]:
					self.static = self.paramName2Val["static"]
					
				if msg.control == dt01.paramName2Num["sounding"]:
					self.sounding = self.paramName2Val["sounding"]
					
			self.fpga_interface_inst.release()
				
			
		elif msg.type == 'polytouch':
			for voice in self.voices:
				self.allNotes[msg.note].polytouch = msg.value/127.0
				note = self.allNotes[msg.note]
				voicesToUpdate = note.voices
				
		elif msg.type == 'aftertouch':
			self.aftertouch = msg.value
			self.aftertouchReal = msg.value/127.0
			for voice in self.allVoices:
				voice.send("cmd_baseincrement", self.paramName2Real["baseincrement"] * self.pitchwheelReal * (1 + self.aftertouchReal) * voice.note.defaultIncrement * 2**6)
		
		# commands effecting all voices should send them all at once
		if msg.type == 'aftertouch' or msg.type == 'pitchwheel' or msg.type == 'control_change': 
			self.fpga_interface_inst.gather()
			self.fpga_interface_inst.release()
			
		if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
			# implement rising mono porta
			for heldnote in self.allNotes[::-1]:
				if heldnote.held and self.polyphony == self.voicesPerNote :
					self.processEvent(heldnote.msg)
					break


if __name__ == "__main__":

	logger = logging.getLogger('DT01')
	#formatter = logging.Formatter('{"debug": %(asctime)s {%(pathname)s:%(lineno)d} %(message)s}')
	formatter = logging.Formatter('{{%(pathname)s:%(lineno)d %(message)s}')
	ch = logging.StreamHandler()
	ch.setFormatter(formatter)
	logger.addHandler(ch)

	logger.setLevel(1)
	logger.debug("initializing from scratch")
	polyphony = 512
	dt01_inst = dt01.DT01(polyphony = polyphony)
	
	logger.debug("Initializing")
	dt01_inst.initialize()
	
	testPatch = Patch(dt01_inst)
	testPatch.processEvent(mido.Message('control_change', control = dt01.paramName2Num ["opno"], value = 0)) #
	testPatch.processEvent(mido.Message('control_change', control = dt01.paramName2Num ["sounding"], value = 1)) #
	testPatch.processEvent(mido.Message('control_change', control = dt01.paramName2Num ["env"], value = 127)) #
	testPatch.processEvent(mido.Message('note_on', channel=0, note=12, velocity=23, time=0))
	testPatch.processEvent(mido.Message('note_on', channel=0, note=16, velocity=23, time=0))
	testPatch.processEvent(mido.Message('note_on', channel=0, note=19, velocity=23, time=0))
	
	#	logger.debug(json.dumps(testPatch.paramName2Real))
	