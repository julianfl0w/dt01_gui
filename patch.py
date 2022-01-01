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
		self.lowestVoice = sorted(self.voices, key=lambda x: x.index)[0]
		self.lowestVoiceIndex = self.lowestVoice.index
		self.voiceCount = len(self.voices)

		self.allChildren = self.voices
	
		for voice in self.voices:
			#logger.debug("claimed: " + str(voice.index))
			voice.note  = self.allNotes[0]
			voice.patch = self
				
		# more defaults : should be programmable by patch
		self.phaseCount = 4
		
		self.envelopeLevelAbsolute = np.zeros((dt01.OPERATORCOUNT, self.phaseCount), dtype=np.int)
		self.envRatePerSample      = np.zeros((dt01.OPERATORCOUNT, self.phaseCount), dtype=np.int)
		self.envTimeSeconds        = np.zeros((dt01.OPERATORCOUNT, self.phaseCount), dtype=np.float)
		self.envTimeSamples        = np.zeros((dt01.OPERATORCOUNT, self.phaseCount), dtype=np.int)
		self.envStepAbsolute       = np.zeros((dt01.OPERATORCOUNT, self.phaseCount), dtype=np.int)
		self.envelopePhase         = np.zeros((len(self.voices), dt01.OPERATORCOUNT), dtype=np.int)
		self.loadJson(patchFilename)
		
		#
		## env_period (samples) = Fs * envTimeSeconds
		#self.envTimeSeconds  = np.ones((dt01.OPERATORCOUNT, self.phaseCount)) * 0.01
		#
		#self.envTimeSamples = self.envTimeSeconds * dt01.SamplesPerSecond
		#logger.debug("self.envTimeSamples:" + str(self.envTimeSamples))
		#self.envRateReal   = np.abs(self.envelopeLevelAbsolute - np.roll(self.envelopeLevelAbsolute, 1)) / self.envTimeSamples
		#self.envRatePerSample  = np.array(self.envRateReal, dtype=np.int)
		
		
	def loadJson(self, filename):
	
		with open(filename, 'r') as f:
			patchDict = json.loads(f.read())
		self.patchDict = patchDict
		logger.debug("loading " + patchDict["Name"])
		initDict = {}
		
		initDict["fm_algo" ], initDict["fbsrc"   ], initDict["sounding"] = algos.getAlgo(patchDict["Algorithm"])
		
		initDict["fbsrc"   ] = initDict["fbsrc"   ]-1
		
		initDict["am_algo" ] = 0x00000000
		initDict["fbgain"  ] = 2**16*patchDict["Feedback"] / 127.0         
		initDict["fbsrc"  ] = 2**16*patchDict["Feedback"] / 127.0        
		
		LFODict = patchDict["LFO"]
		initDict["channelgain"] = [2**16/8, 2**16/8]         
		initDict["env"]       = [0    , 0    , 0    , 0    , 0    , 0    , 2**29*LFODict["AM Depth"] / 127.0    ,2**30*LFODict["Pitch Mod Depth"] / 127.0]
		initDict["env_rate" ] = [2**27, 2**27, 2**27, 2**27, 2**27, 2**27, 2**26*LFODict["Delay"] / 127.0, 2**26*LFODict["Delay"] / 127.0]
		
		initDict["increment"      ] = [0    , 0    , 0    , 0    , 0    , 0    , 2**20*pow(LFODict["Speed"] / 127.0, 2), 2**18*LFODict["Speed"] / 127.0]
		initDict["increment_rate" ] = [2**29, 2**29, 2**29, 2**29, 2**29, 2**29, 2**28, 2**28]
		
		initDict["flushspi"    ] = 0
		initDict["passthrough" ] = 0
		initDict["shift"       ] = max(2 - len(initDict["sounding"]), 0)
		
		sounding0indexed = [s-1 for s in initDict["sounding"]]
		for voice in self.voices:
			for operator in voice.operators:
				if operator.index in sounding0indexed: 
					operator.sounding = 1
				else:
					operator.sounding = 0
				
		
		
		# ignoring pitch envelope generator for now
		
		for operator in range(6):
			opDict = patchDict["Operator" + str(operator+1)]
			if opDict["Oscillator Mode"] == "Frequency (Ratio)":
				for voice in self.voices:
					voice.operators[operator].incrementScale = opDict["Frequency"] * (1 + (opDict["Detune"] / 7.0) / 70)
			else:
				for voice in self.voices:
					voice.operators[operator].baseIncrement  = (2**32)*opDict["Frequency"] / dt01.SamplesPerSecond
					voice.operators[operator].incrementScale = 1
					
			envDict = opDict["Envelope Generator"]
			outputLevelReal = (opDict["Output Level"]/127.0)
			maxSeconds = 10 # gets multiplied again by 4 if its a release (as opposed to attack)
			gamma = 4
			self.setEnvTimeSecondsAndLevelReal(sounding0indexed, operator, 0, maxSeconds*pow(1-(envDict["Rate 1"]/127.0), gamma), outputLevelReal * (envDict["Level 1"]/127.0))
			self.setEnvTimeSecondsAndLevelReal(sounding0indexed, operator, 1, maxSeconds*pow(1-(envDict["Rate 2"]/127.0), gamma), outputLevelReal * (envDict["Level 2"]/127.0))
			self.setEnvTimeSecondsAndLevelReal(sounding0indexed, operator, 2, maxSeconds*pow(1-(envDict["Rate 3"]/127.0), gamma), outputLevelReal * (envDict["Level 3"]/127.0))
			self.setEnvTimeSecondsAndLevelReal(sounding0indexed, operator, 3, maxSeconds*pow(1-(envDict["Rate 4"]/127.0), gamma), outputLevelReal * (envDict["Level 4"]/127.0))
		
		logger.debug("envRatePerSample:\n" + str(self.envRatePerSample))
		logger.debug("envelopeLevelAbsolute:\n" + str(self.envelopeLevelAbsolute))
		logger.debug("envStepAbsolute:\n" + str(self.envStepAbsolute))
			
		# format sounding
		soundPayload = int(0)
		for operator in sounding0indexed: 
			soundPayload += (1 << (operator))
		initDict["sounding"] = soundPayload
		
		# format fm algo
		fm_algo_payload = int(0)
		for i, src in enumerate(initDict["fm_algo" ]):
			fm_algo_payload = fm_algo_payload + ((src-1) << (i*4))
		initDict["fm_algo" ] = fm_algo_payload
		
		# format am algo
		# am_algo_payload = int(0)
		# for i, src in enumerate(initDict["am_algo" ]):
		# 	am_algo_payload += src << (i*4)
		# initDict["am_algo" ] = am_algo_payload
		
		self.dt01_inst.initialize(initDict, voices = self.voices)
		
		return 0
	
	# SHOULD FOLLOW LEVEL SETTING
	def setEnvTimeSecondsAndLevelReal(self, sounding, opno, phase, timeSeconds, levelReal):
		# sounding vs nonsounding difference?
		if opno in sounding:
			self.envelopeLevelAbsolute[opno,phase] = levelReal*(2**31)
		else:
			self.envelopeLevelAbsolute[opno,phase] = levelReal*(2**31)
			
		# Falling env is 4x slower than rising
		if self.envelopeLevelAbsolute[opno,phase] > self.envelopeLevelAbsolute[opno,(phase+self.phaseCount-1) % self.phaseCount]:
			timeSeconds *= 4
			
		#clip
		self.envTimeSeconds[opno,phase]   = max(0.005, timeSeconds)
			
		self.envTimeSamples[opno,phase]   = self.envTimeSeconds[opno,phase] * dt01.SamplesPerSecond
		self.envStepAbsolute[opno,phase]  = np.abs(self.envelopeLevelAbsolute[opno,phase] - self.envelopeLevelAbsolute[opno,(phase+self.phaseCount-1) % self.phaseCount])
		# if new level is too close to old level, set to the smallest increase that makes time
		lastPhase = (phase + self.phaseCount -1) % self.phaseCount
		if abs(self.envelopeLevelAbsolute[opno,phase] - self.envelopeLevelAbsolute[opno,lastPhase]) < self.envTimeSamples[opno,phase]:
			self.envelopeLevelAbsolute[opno,phase] = self.envelopeLevelAbsolute[opno,lastPhase] + self.envTimeSamples[opno,phase]
			self.envStepAbsolute[opno,phase]  = np.abs(self.envelopeLevelAbsolute[opno,phase] - self.envelopeLevelAbsolute[opno,(phase+self.phaseCount-1) % self.phaseCount])
			self.envRatePerSample[opno,phase] = 1
		else:
			self.envRatePerSample[opno,phase] = self.envStepAbsolute[opno,phase] / self.envTimeSamples[opno,phase] # scale the envelope rate to the difference between this step and the next
		
	def setPhaseAllOps(self, voiceno, phase):
		dt01.formatAndSend(dt01.cmd_env_rate, voiceno, 0, self.opZeros[:6], voicemode=False)                               
		dt01.formatAndSend(dt01.cmd_env,      voiceno, 0, self.envelopeLevelAbsolute[:6,phase], voicemode=False)
		dt01.formatAndSend(dt01.cmd_env_rate, voiceno, 0, self.envRatePerSample[:6,phase], voicemode=False)                           
		self.envelopePhase[voiceno, :] = phase
		
		return 0
		
	def silenceAllOps(self, voiceno):
		dt01.formatAndSend(dt01.cmd_env_rate, voiceno, 0, self.opZeros[:6], voicemode=False)                               
		dt01.formatAndSend(dt01.cmd_env,      voiceno, 0, self.envelopeLevelAbsolute[:6,3], voicemode=False)
		dt01.formatAndSend(dt01.cmd_env_rate, voiceno, 0, self.envStepAbsolute[:6,3], voicemode=False)                           
		self.envelopePhase[voiceno, :] = 3
		
		return 0
	
	def processIRQueue(self, voiceno, opnos):
		
		for opno in opnos:
			phase = (self.envelopePhase[voiceno, opno] + 1) % self.phaseCount
				
			#logger.debug("\n\nproc IRQUEUE! voice:" + str(voiceno) + " op:"+ str(opno) + " phase:" + str(phase))

			if phase == 0:
				pass
				logger.debug("STOP PHASE")
			else:
				dt01.formatAndSend(dt01.cmd_env_rate, voiceno, opno, 0, voicemode=False)                               
				dt01.formatAndSend(dt01.cmd_env,      voiceno, opno, self.envelopeLevelAbsolute[opno,phase], voicemode=False)
				#logger.debug("sending rate " + str(self.envRatePerSample[opno,phase]))
				#logger.debug("envRatePerSample:\n" + str(self.envRatePerSample))
				dt01.formatAndSend(dt01.cmd_env_rate, voiceno, opno, self.envRatePerSample[opno,phase], voicemode=False)                           
	
			self.envelopePhase[voiceno, opno] = phase
		
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
				self.silenceAllOps(voice.index)
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
				dt01.formatAndSend(dt01.cmd_env_rate , self.lowestVoiceIndex, 6, [0] * self.polyphony)
				dt01.formatAndSend(dt01.cmd_env , self.lowestVoiceIndex, 6, [(msg.value/127.0)*2**29] * self.polyphony)
				dt01.formatAndSend(dt01.cmd_env_rate , self.lowestVoiceIndex, 6, [(msg.value/127.0)*2**29] * self.polyphony)
				
				
			for voice in self.voices:
			
				# OPERATOR CONCERNS
				# get active operator
				if self.activeOperator < 2:
					channel  = voice.channels[self.activeOperator]
				activeOperator = voice.operators[self.activeOperator]
				
				if msg.control == dt01.ctrl_voicegain or msg.control == dt01.ctrl_pan : 
					baseVolume = 2**16*(msg.value/127.0)
					if self.activeOperator == 0:
						channel.formatAndSend(dt01.cmd_channelgain, baseVolume*(msg.value/127.0)) # assume 2 channels]
					else:
						channel.formatAndSend(dt01.cmd_channelgain, baseVolume*(1 - (msg.value/127.0))) # assume 2 channels]
	
				
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
					activeOperator.formatAndSend(dt01.cmd_env_rate      , 2**10 * (1 - (msg.value/127.0)) * (1 - (msg.value/127.0)) )
		# static oscillators do not have velocity-dependant env
					
				if msg.control == dt01.ctrl_increment:
					voice.setAllIncrements(self.pitchwheelReal * (1 + self.aftertouchReal))
					
				if msg.control == dt01.ctrl_increment_rate: 
					activeOperator.formatAndSend(dt01.cmd_increment_rate, 2**8 * (1 - (msg.value/127.0)) * (1 - (msg.value/127.0)))
					
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
				dt01.formatAndSend(dt01.cmd_increment, self.lowestVoiceIndex, operator, [min(self.pitchwheelReal * (1 + self.aftertouchReal)*voice.operators[operator].getIncrement(),2**30) for voice in self.voices])
									
			
		if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
			# implement rising mono rate
			for heldnote in self.allNotes[::-1]:
				if heldnote.held and self.polyphony == self.voicesPerNote :
					self.midi2commands(heldnote.msg)
					break
		
		return True


def startup(patchFilename = "dx7_patches/aaa/J__Rhodes_.json"):
	
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

	socket.connect ("tcp://localhost:%s" % "5555")
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
				voiceno, opnos = dt01.getIRQueue()
				GLOBAL_DEFAULT_PATCH.processIRQueue(voiceno, opnos)
				
			#check for patch change 
			try:
				string = socket.recv_string(flags=zmq.NOBLOCK)
				logger.debug(string)
				GLOBAL_DEFAULT_PATCH.loadJson(string)
			except zmq.Again as e:
				pass
				
	except KeyboardInterrupt:
		logger.debug('')
	finally:
		logger.debug("Exit.")
		midiin.close_port()
		del midiin
if __name__ == "__main__":
	startup("/home/pi/dt01_gui/dx7_patches/aaa/J__Rhodes_.json")
