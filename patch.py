import struct
from bitarray import bitarray
import logging
import RPi.GPIO as GPIO
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
import multiprocessing
import RPi.GPIO as GPIO
import zmq
import algos
logger = logging.getLogger('DT01')

import socket


	
MIDINOTES      = 128
CONTROLCOUNT   = 128

def noteToFreq(note):
	a = 440.0 #frequency of A (coomon value is 440Hz)
	return (a / 32) * (2 ** ((note - 9) / 12.0))

class Note:
	def __init__(self, index):
		self.index  = index
		self.voices = []
		self.velocity = 0
		self.velocityReal = 0
		self.held  = False
		self.polytouch = 0
		self.msg  = None
		self.defaultIncrement = 2**32 * (noteToFreq(index) / 96000.0)
		
# patch holds all state, including note and control state
class Patch():
					
	def formatAndSend(self, param, value):
		dt01.formatAndSend(param, 0, 0, value)
	
	def processControl(self, paramName, value):
		self.midi2commands(mido.Message('control_change', control = dt01.controlNum2Num [paramName], value = value)) #
		
	def __init__(self, dt01_inst, patchFilename):
		logger.debug("patch init ")
		self.dt01_inst = dt01_inst
		self.polyphony = 64
		self.active = True
		self.voicesPerNote = 1
		self.voices = []
		self.currvoiceno = 0
		self.currVoice = 0
		self.pitchwheel  = 8192
		self.pitchwheelReal  = 1
		self.aftertouch = 0
		self.aftertouchReal = 0
		self.sustain = False
		self.toRelease = [False]*MIDINOTES
		self.allNotes = []
		self.opZeros = np.array([0]* dt01.OPERATORCOUNT, dtype=np.int)

		for i in range(MIDINOTES):
			self.allNotes+= [Note(i)]
			
		self.activeOperator = 0
		self.voices = dt01_inst.getVoices()
		self.lowestVoiceIndex = min([v.index for v in self.voices])
		self.voiceCount = len(self.voices)

		self.allChildren = self.voices
	
		for voice in self.voices:
			#logger.debug("claimed: " + str(voice.index))
			voice.note  = self.allNotes[0]
			voice.patch = self
				
		# more defaults : should be programmable by patch
		self.phaseCount = 4
		
		self.envelopeLevelReal  = np.zeros((dt01.OPERATORCOUNT, self.phaseCount))
		self.envelopeLevelFixed = np.zeros((dt01.OPERATORCOUNT, self.phaseCount), dtype=np.int)
		self.envStepSizeReal    = np.zeros((dt01.OPERATORCOUNT, self.phaseCount))
		self.envStepSizeFixed   = np.zeros((dt01.OPERATORCOUNT, self.phaseCount), dtype=np.int)
		#
		## env_period (samples) = Fs * envelopeTimeSeconds
		#self.envelopeTimeSeconds  = np.ones((dt01.OPERATORCOUNT, self.phaseCount)) * 0.01
		##self.envelopeTimeSeconds[0] = np.array([2**24, 0, 0, 2**7])
		#self.envelopeTimeSeconds[0,3] = 3
		#
		#self.envTimeSamples = self.envelopeTimeSeconds * dt01.SamplesPerSecond
		#logger.debug("self.envTimeSamples:" + str(self.envTimeSamples))
		#self.envStepSizeReal   = np.abs(self.envelopeLevelFixed - np.roll(self.envelopeLevelFixed, 1)) / self.envTimeSamples
		#self.envStepSizeFixed  = np.array(self.envStepSizeReal, dtype=np.int)
		
		self.envelopePhase = np.zeros((len(self.voices), dt01.OPERATORCOUNT), dtype=np.int)
		
	def loadJson(self, filename):
		with open(filename, 'r') as f:
			patchDict = json.loads(f.read)
		self.patchDict = patchDict
		logger.debug("loading " + patchDict["Name"])
		
		fmAlgo, fbSrc, sounding = algos.getAlgo(patchDict["Algorithm"])
		
		soundPayload = int(0)
		for operator in enumerate(sounding):
			soundPayload += (1 << operator)
			
		## FM, (AM), and Feedback Algos
		dt01.formatAndSend(dt01.cmd_fm_algo , self.lowestVoiceIndex, 0, [Voice.getFMAlgo(fmAlgo)]*self.voiceCount, voicemode=True)         
		dt01.formatAndSend(dt01.cmd_sounding, self.lowestVoiceIndex, 0, [soundPayload]*self.voiceCount, voicemode=True)         
		dt01.formatAndSend(dt01.cmd_fbgain  , self.lowestVoiceIndex, 0, [2**16*patchDict["Feedback"] / 127.0]*self.voiceCount, voicemode=True)
		
		## LFOs
		LFODict = patchDict["LFO"]
		dt01.formatAndSend(dt01.cmd_increment_rate  , self.lowestVoiceIndex, 6, [2**18]*self.voiceCount, voicemode=True)
		dt01.formatAndSend(dt01.cmd_increment       , self.lowestVoiceIndex, 6, [2**20*LFODict["Speed"] / 127.0]*self.voiceCount, voicemode=True)
		dt01.formatAndSend(dt01.cmd_env_rate        , self.lowestVoiceIndex, 6, [2**18*LFODict["Delay"]]*self.voiceCount, voicemode=True)
		dt01.formatAndSend(dt01.cmd_env             , self.lowestVoiceIndex, 6, [2**20*LFODict["AM Depth"] / 127.0]*self.voiceCount, voicemode=True)
		dt01.formatAndSend(dt01.cmd_increment_rate  , self.lowestVoiceIndex, 7, [2**18]*self.voiceCount, voicemode=True)
		dt01.formatAndSend(dt01.cmd_increment       , self.lowestVoiceIndex, 7, [2**20*LFODict["Speed"] / 127.0]*self.voiceCount, voicemode=True)
		dt01.formatAndSend(dt01.cmd_env_rate        , self.lowestVoiceIndex, 7, [2**18*LFODict["Delay"]]*self.voiceCount, voicemode=True)
		dt01.formatAndSend(dt01.cmd_env             , self.lowestVoiceIndex, 7, [2**20*LFODict["Pitch Mod Depth"] / 127.0]*self.voiceCount, voicemode=True)
		
		# ignoring pitch envelope generator for now
		
		for operator in range(6):
			opDict = patchDict["Operator" + str(operator+1)]
			if opDict["Oscillator Mode"] == "Frequency (Ratio)":
				for voice in self.voices:
					voice.operators[operator].incrementScale = opDict["Frequency"] * (1 + opDict["Detune"] / 127.0)
			else:
				for voice in self.voices:
					voice.operators[operator].baseIncrement  = (2**32)*opDict["Frequency"] / dt01.SamplesPerSecond
					voice.operators[operator].incrementScale = 1
					
			envDict = opDict["Envelope Generator"]
			setenvelopeLevelReal(operator, 0, envDict["Level 1"]/127.0)
			setenvelopeLevelReal(operator, 1, envDict["Level 2"]/127.0)
			setenvelopeLevelReal(operator, 2, envDict["Level 3"]/127.0)
			setenvelopeLevelReal(operator, 3, envDict["Level 4"]/127.0)
			setenvelopeTimeSeconds(operator, 0, 4*envDict["Rate 1"]/127.0)
			setenvelopeTimeSeconds(operator, 1, 4*envDict["Rate 2"]/127.0)
			setenvelopeTimeSeconds(operator, 2, 4*envDict["Rate 3"]/127.0)
			setenvelopeTimeSeconds(operator, 3, 4*envDict["Rate 4"]/127.0)
			
			# ignoring level scaling
			# and rate scaling
			
		return 0
	
	def setenvelopeLevelReal(opno, phase, value):
		self.envelopeLevelReal[opno,phase]  = value
		self.envelopeLevelFixed[opno,phase] = value*2**31
		self.envStepSizeSamples   = np.abs(envelopeLevelFixed[opno,phase] - envelopeLevelFixed[opno,phase+1])
		self.envStepSizeReal    = envStepSizeSamples / self.envTimeSamples
		
	def setenvelopeTimeSeconds(opno, phase, value):
		self.envelopeTimeSeconds[opno,phase] = value
		self.envTimeSamples = self.envelopeTimeSeconds * dt01.SamplesPerSecond
		logger.debug("self.envTimeSamples:" + str(self.envTimeSamples))
		

	def setPhaseAllOps(self, voiceno, phase):
		dt01.formatAndSend(dt01.cmd_env_rate, voiceno, 0, self.opZeros, voicemode=False)                               
		dt01.formatAndSend(dt01.cmd_env,      voiceno, 0, self.envelopeLevelFixed[:,phase], voicemode=False)
		dt01.formatAndSend(dt01.cmd_env_rate, voiceno, 0, self.envStepSizeFixed[:,phase], voicemode=False)                           
		self.envelopePhase[voiceno, :] = phase
		
		return 0
	
	def processIRQueue(self, voiceno, opno):
		if opno>5:
			return
			
		phase = self.envelopePhase[voiceno, opno]
			
		logger.debug("\n\nproc IRQUEUE! voice:" + str(voiceno) + " op:"+ str(opno) + " phase:" + str(phase))

		if phase >= self.phaseCount - 1:
			logger.debug("STOP PHASE")
		else:
			dt01.formatAndSend(dt01.cmd_env_rate, voiceno, opno, 0, voicemode=False)                               
			dt01.formatAndSend(dt01.cmd_env,      voiceno, opno, self.envelopeLevelFixed[opno,phase], voicemode=False)
			logger.debug("sending rate " + str(self.envStepSizeFixed[opno,phase]))
			dt01.formatAndSend(dt01.cmd_env_rate, voiceno, opno, self.envStepSizeFixed[opno,phase], voicemode=False)                           
	
	
	def midi2commands(self, msg):
	
		logger.debug("\n\nProcessing " + str(msg))
			
		if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
			if self.sustain:
				self.toRelease[msg.note] = True
				return
				
			note = self.allNotes[msg.note] 
			note.velocity = 0 
			note.velocityReal = 0 
			voicesToUpdate = note.voices.copy()
			for voice in note.voices:
				#voice.spawntime = 0
				self.setPhaseAllOps(voice.index, 3)
			note.voices = []
			note.held = False
		
		# if note on, spawn voices
		if msg.type == "note_on":
			note = self.allNotes[msg.note]
			note.velocity     = msg.velocity
			note.velocityReal = (msg.velocity/127.0)**2
			note.held = True
			note.msg = msg
			# spawn some voices!
			for voiceNoInCluster in range(self.voicesPerNote):
				
				#self.currvoiceno = (self.currvoiceno + 1) % self.polyphony
				#logger.debug([s.spawntime for s in self.voices])
				voice = sorted(self.voices, key=lambda x: x.spawntime)[0]
				voice.spawntime = time.time()
				voice.indexInCluser = voiceNoInCluster
				voice.note = note
				note.voices += [voice]
				logger.debug("modifier " + str(self.pitchwheelReal * (1 + self.aftertouchReal)))
				voice.setAllIncrements(self.pitchwheelReal * (1 + self.aftertouchReal))
				
				self.setPhaseAllOps(voice.index, 0)
						
				dt01.formatAndSend(dt01.cmd_channelgain, voice.index, 0, [2**16*note.velocityReal]*2, voicemode = False)
				
		if msg.type == 'pitchwheel':
			logger.debug("PW: " + str(msg.pitch))
			self.pitchwheel = msg.pitch
			ARTIPHON = 1
			if ARTIPHON:
				self.pitchwheel *= 2
			amountchange = self.pitchwheel / 8192.0
			self.pitchwheelReal = pow(2, amountchange)
			logger.debug("PWREAL " + str(self.pitchwheelReal))
			
			for voice in self.voices:
				voice.setAllIncrements(self.pitchwheelReal * (1 + self.aftertouchReal))
				
		elif msg.type == 'control_change':
						
			logger.debug("control : " + str(msg.control) + " (" + dt01.controlNum2Name[msg.control] +  "): " + str(msg.value))

			event = "control[" + str(msg.control) + "]"
			
			# selection
			if msg.control == dt01.ctrl_opno:
				self.activeOperator = min(msg.value, 7)
				#logger.debug(self.activeOperator)
				
			logger.debug("Setting op " + str(self.activeOperator) + " control: " + str(msg.control) + " value: " + str(msg.value/127.0))
			
			# forward some controls
			# PUT THIS BACK
			
			#if msg.control == 0:
			#	self.midi2commands(mido.Message('control_change', control= dt01.ctrl_opno      ], value = 6 ))
			#	self.midi2commands(mido.Message('control_change', control= dt01.ctrl_env      ], value = msg.value ))
			#if msg.control == 1:
			#	self.midi2commands(mido.Message('control_change', control= dt01.ctrl_opno      ], value = 7 ))
			#	self.midi2commands(mido.Message('control_change', control= dt01.ctrl_env      ], value = msg.value ))
			
			# route control3 to control 7 because sometimes 3 is volume control
			if msg.control == 3:
				self.midi2commands(mido.Message('control_change', control= 7, value = msg.value ))
				
			if msg.control == dt01.ctrl_flushspi:
				self.formatAndSend(dt01.cmd_flushspi, self.controlNum2Val[dt01.ctrl_flushspi])
				
			if msg.control == dt01.ctrl_passthrough:
				self.formatAndSend(dt01.cmd_passthrough, self.controlNum2Val[dt01.ctrl_passthrough])
				
			if msg.control == dt01.ctrl_shift:
				self.formatAndSend(dt01.cmd_shift , self.controlNum2Val[dt01.ctrl_shift])
				
				
			if msg.control == dt01.ctrl_tremolo_env:
				self.midi2commands(mido.Message('control_change', control = dt01.ctrl_opno, value = 6)) #
				self.midi2commands(mido.Message('control_change', control = dt01.ctrl_env, value = msg.value)) #
				#dt01.formatAndSend(dt01.cmd_env , 0,self.activeOperator, [self.opControlNum2Real[self.activeOperator, dt01.ctrl_env]*2**28] * self.polyphony)
				
				
			if msg.control == dt01.ctrl_vibrato_env:
				self.midi2commands(mido.Message('control_change', control = dt01.ctrl_opno, value = 7)) #
				self.midi2commands(mido.Message('control_change', control = dt01.ctrl_env, value = msg.value)) #
		
			if msg.control == dt01.ctrl_env: 
				# sounding operators begin on note_on
				logger.debug("\n\n-------CTRL_ENV---------\n\n")
				dt01.formatAndSend(dt01.cmd_env , 0,self.activeOperator, [self.opControlNum2Real[self.activeOperator, dt01.ctrl_env]*2**28] * self.polyphony)
				
			for voice in self.voices:
			
				# OPERATOR CONCERNS
				# get active operator
				if self.activeOperator < 2:
					channel  = voice.channels[self.activeOperator]
				activeOperator = voice.operators[self.activeOperator]
				
				if msg.control == dt01.ctrl_voicegain or msg.control == dt01.ctrl_pan : 
					baseVolume = 2**16*self.controlNum2Real["ctrl_voicegain"]
					if self.activeOperator == 0:
						channel.formatAndSend(dt01.cmd_channelgain, baseVolume*self.controlNum2Real["ctrl_pan"]) # assume 2 channels]
					else:
						channel.formatAndSend(dt01.cmd_channelgain, baseVolume*(1 - self.controlNum2Real["ctrl_pan"])) # assume 2 channels]
	
				
				#am algo
				if msg.control == dt01.ctrl_amsrc:  
					voice.setAMSrc(self.activeOperator.index, msg.value)
					
				if msg.control == dt01.ctrl_fbgain: 
					voice.setFBGainReal(msg.value / 127.0)
					
				if msg.control == dt01.ctrl_fbsrc:
					voice.setFBSource(dt01.cmd_fbsrc)
		
				if msg.control == dt01.ctrl_sounding: 
					voice.setSounding(self, activeOperator, msg.value & 0x01)
					
				if msg.control == dt01.ctrl_env: 
					pass
					# sounding operators begin on note_on
					#self.setEnv(activeOperator)
					#dt01.formatAndSend(dt01.cmd_env, activeOperator.index, activeOperator.voice.index, self.computedState[dt01.cmd_env,activeOperator.voice.index,activeOperator.index])
				
						
				if msg.control == dt01.ctrl_env_rate: 
					activeOperator.formatAndSend(dt01.cmd_env_rate      , 2**10 * (1 - self.opControlNum2Real[activeOperator.index,dt01.ctrl_env_rate]) * (1 - self.controlNum2Real[dt01.ctrl_ratemento]) )
		# static oscillators do not have velocity-dependant env
					
				if msg.control == dt01.ctrl_increment:
					voice.setAllIncrements(self.pitchwheelReal * (1 + self.aftertouchReal))
					
				if msg.control == dt01.ctrl_increment_rate: 
					activeOperator.formatAndSend(dt01.cmd_increment_rate, 2**8 * (1 - self.controlNum2Real[dt01.ctrl_ratemento]) * (1 - self.controlNum2Real[activeOperator.index,dt01.ctrl_increment_rate]))
					
				if msg.control == dt01.ctrl_sustain: 
					self.sustain  = msg.value
					if not self.sustain:
						for note, release in enumerate(self.toRelease):
							if release:
								self.midi2commands(mido.Message('note_off', note = note, velocity = 0))
						self.toRelease = [False]*MIDINOTES
					
				
			
		elif msg.type == 'polytouch':
			self.polytouch = msg.value
			self.polytouchReal = msg.value/127.0
				
		elif msg.type == 'aftertouch':
			self.aftertouch = msg.value
			self.aftertouchReal = msg.value/127.0
			
			#for voice in self.voices:
			#	voice.setAllIncrements(self.pitchwheelReal * (1 + self.aftertouchReal))
			for operator in range(6):
				dt01.formatAndSend(dt01.cmd_increment, self.lowestVoiceIndex, operator, [self.pitchwheelReal * (1 + self.aftertouchReal)*voice.operators[operator].getIncrement() for voice in self.voices])
									
			
		if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
			# implement rising mono rate
			for heldnote in self.allNotes[::-1]:
				if heldnote.held and self.polyphony == self.voicesPerNote :
					self.midi2commands(heldnote.msg)
					break
		
		return True


def startup(patchFilename = "PatchTranslate/rhodes1_12/F__Rhodes_.json"):
	
	PID = os.getpid()
	
	logger = logging.getLogger('DT01')
	#formatter = logging.Formatter('{"debug": %(asctime)s {%(pathname)s:%(lineno)d} %(message)s}')
	formatter = logging.Formatter('{{%(pathname)s:%(lineno)d %(message)s}')
	ch = logging.StreamHandler()
	ch.setFormatter(formatter)
	logger.addHandler(ch)

	logger.setLevel(0)
	if len(sys.argv) > 1:
		logger.setLevel(1)
		
	logger.debug("Instantiating DT01")
	polyphony = 512
	
	logger.debug("initializing from scratch")
	dt01_inst = dt01.DT01(polyphony = polyphony)
		
	GLOBAL_DEFAULT_PATCH = Patch(dt01_inst, patchFilename)
	
	api=rtmidi.API_UNSPECIFIED
	allMidiDevicesAndPatches = []
	midiin = rtmidi.MidiIn(get_api_from_environment(api))
	
	midi_ports_last = []
	
	dt01.initIRQueue()
		
	# Socket to talk to server
	context = zmq.Context()
	socket = context.socket(zmq.SUB)

	socket.connect ("tcp://localhost:%s" % "5000")
	socket.setsockopt_string(zmq.SUBSCRIBE, "")

	logger.debug("Entering main loop. Press Control-C to exit.")
	loopstart = time.time()
	lastCheck = 0
	try:
		maxLoop = 0
		# Just wait for keyboard interrupt,
		# everything else is handled via the input callback.
		while True:
			# check for new devices
			if time.time()-lastCheck > 1:
				lastCheck = time.time()
				midi_ports  = midiin.get_ports()
				for i, midi_portname in enumerate(midi_ports):
					if midi_portname not in midi_ports_last:
						logger.debug("adding " + midi_portname)
						try:
							mididev, midi_portno = open_midiinput(midi_portname)
						except (EOFError, KeyboardInterrupt):
							sys.exit()
			
						# no longer doing callbacks
						#logger.debug("Attaching MIDI input callback handler.")
						##allMidiDevicesAndPatchesice_inst = allMidiDevicesAndPatchesice(i, GLOBAL_DEFAULT_PATCH, str(midi_portname))
						#allMidiDevicesAndPatchesice_inst = allMidiDevicesAndPatchesice(i, GLOBAL_DEFAULT_PATCH, str(midi_portname))
						#midiin.set_callback(allMidiDevicesAndPatchesice_inst)
						#logger.debug("Handler: " + str(midiin))
						midiDevAndPatches = (mididev, [GLOBAL_DEFAULT_PATCH])
						allMidiDevicesAndPatches += [midiDevAndPatches]
				midi_ports_last = midi_ports
				
		
			#c = sys.stdin.read(1)
			#if c == 'd':
			#	dt01_inst.dumpState()
			for dev, patches in allMidiDevicesAndPatches:
				msg = dev.get_message()
				if msg != None:
					msg, dtime = msg
					msg = mido.Message.from_bytes(msg)
					logger.debug(msg)
					for patch in patches:
						patch.midi2commands(msg)
				
					logger.warning(time.time() - loopstart)
			loopstart = time.time()
			
			# process the IRQUEUE
			if(GPIO.input(37)):
				voiceno, opno = dt01.getIRQueue()
				GLOBAL_DEFAULT_PATCH.processIRQueue(voiceno, opno)
				
			
	except KeyboardInterrupt:
		logger.debug('')
	finally:
		logger.debug("Exit.")
		midiin.close_port()
		del midiin

if __name__ == "__main__":
	startup("PatchTranslate/rhodes1_12/F__Rhodes_.json")