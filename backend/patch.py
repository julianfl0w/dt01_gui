import os
os.system("export XAUTHORITY=/home/pi/.Xauthority")
os.system("export DISPLAY=:0")

import struct
from bitarray import bitarray
import logging
import RPi.GPIO as GPIO
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
import traceback
import pickle
import dtfm

useKeyboard = False
if useKeyboard:
	import keyboard
	#import mouse
	#import pyautogui

import logging
import collections
import math
import multiprocessing
import RPi.GPIO as GPIO
import zmq
import algos
import queue
logger = logging.getLogger('dtfm')
#formatter = logging.Formatter('{"debug": %(asctime)s {%(pathname)s:%(lineno)d} %(message)s}')
formatter = logging.Formatter('{{%(pathname)s:%(lineno)d %(message)s}')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

import faulthandler; faulthandler.enable()

	
MIDINOTES      = 128
CONTROLCOUNT   = 128
maxIntArray    = np.array([2**30]*8, dtype=np.int32)
newInc         = maxIntArray.copy()

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
		self.releaseTime = 0
		
pentaSingle = [1/1, 32.0/27, 4.0/3, 3.0/2, 16.0/9]
penta = []
for i in range(10):
	for ps in pentaSingle:
		penta += [ps*(2**i)]

class Cluster():
	def __init__(self, voices, patch):
		self.voices = voices
		self.vIndexes = [v.index for v in voices]
		self.patch  = patch
		for v in voices:
			v.cluster = self
		self.spawntime = time.time()
		voiceNoInCluster = np.arange(len(self.voices))
		
		#¢ or c = 1200 × log2 (f2 / f1)
		# c = 1200 × log2 (fratio)
		# c / 1200 = log2 (fratio)
		# 2 ^ ( c / 1200) = fratio
		self.voiceposUnit = (voiceNoInCluster / len(voices)) * 2 - 1
		self.centsDetune = 20
		self.clusterDetune = pow(2, self.centsDetune*self.voiceposUnit/1200)
		np.set_printoptions(threshold=sys.maxsize)
	
	def startEnvs(self):
		logger.debug("startEnvs cluster " + str(self.index))
		self.formatAndSend(dtfm.cmd_env_rate, self.opZeros,  voicemode=False)                               
		self.formatAndSend(dtfm.cmd_env,      self.env0,     voicemode=False)
		self.formatAndSend(dtfm.cmd_env_rate, self.envRate0, voicemode=False) 
		for voice in self.voices:
			for op in voice.operators:
				op.phase = 0
		
		return 0
	
	def spawn(self, note):
		#logger.debug("clusterDetune "  + str(self.clusterDetune))
		#logger.debug("incrementScale " + str(self.patch.incrementScale))
		#logger.debug("freqScales " + str(self.freqScales[:]))
		np.multiply(note.defaultIncrement, self.freqScales, out = self.strikeIncrement, casting='unsafe')
		logger.debug(self.strikeIncrement)
		for voice in self.voices:
			voice.note = note
		note.cluster = self
			
		#logger.debug("modifier " + str(self.patch.getPitchMod()))
		self.setAllIncrements()
		self.startEnvs()
		dtfm.formatAndSend(dtfm.cmd_channelgain, self.vIndexes[0], 0, [2**16*note.velocityReal]*len(self.voices), voicemode = True)
		dtfm.formatAndSend(dtfm.cmd_channelgain, self.vIndexes[0], 1, [2**16*note.velocityReal]*len(self.voices), voicemode = True)
				
	
	def setAllIncrements(self):
		logger.debug("setting all increments")
		np.multiply(self.strikeIncrement, self.patch.getPitchMod(), out = self.strikeIncrementPM, casting='unsafe' )
		
		val = np.minimum(self.patch.baseIncrement + self.strikeIncrementPM, 2**30).astype(np.int32)
		val = val.flatten()
		logger.debug("val " + str( val))
		self.voices[0].formatAndSend(dtfm.cmd_increment, val[:], voicemode = False)
	
	def silenceAllOps(self):
		rates  = []
		for voice in self.voices:
			for op in voice.operators:
				rates  += [self.patch.envRatePerSample[op.index, self.patch.phaseCount[op.index] - 1]]
				op.phase = self.patch.phaseCount[op.index] - 1
		#logger.debug(rates)
		self.formatAndSend(dtfm.cmd_env_rate, self.opZeros, voicemode=False)
		self.formatAndSend(dtfm.cmd_env,      self.opZeros, voicemode=False)
		self.formatAndSend(dtfm.cmd_env_rate, rates, voicemode=False)        
		
	def update(self):
		self.opZeros = np.zeros((8 * len(self.voices)), dtype=np.int32)
		self.env0     = np.repeat(self.patch.envThisLevel    [:,0].reshape((1, dtfm.OPERATORCOUNT)), len(self.voices), axis=0).astype(np.int32).flatten()    
		self.envRate0 = np.repeat(self.patch.envRatePerSample[:,0].reshape((1, dtfm.OPERATORCOUNT)), len(self.voices), axis=0).astype(np.int32).flatten()
		self.freqScales = (np.rot90(self.clusterDetune.reshape(1,len(self.voices)), 3) * self.patch.incrementScale).astype(np.float32)
		self.strikeIncrement   = np.full_like(self.freqScales, 1, dtype = np.int32)
		self.strikeIncrementPM = np.full_like(self.freqScales, 1, dtype = np.int32)
		
		np.set_printoptions(threshold=sys.maxsize)
		#logger.debug(str(self.env0 ))
	
	def formatAndSend(self, param, value, voicemode):
		dtfm.formatAndSend(param, self.vIndexes[0], 0, value, voicemode)
		
# patch holds all state, including note and control state
class Patch():
					
	def formatAndSend(self, param, value):
		dtfm.formatAndSend(param, 0, 0, value)
	
	def processControl(self, paramName, value):
		self.midi2commands(mido.Message('control_change', control = dtfm.controlNum2Num [paramName], value = value)) #
		
	def __init__(self, dtfm_inst, patchFilename):
		logger.debug("patch init ")
		self.dtfm_inst = dtfm_inst
		self.polyphony = 128
		self.active = True
		self.voicesPerCluster = 5
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
		
		for i in range(MIDINOTES):
			self.allNotes+= [Note(i)]
			
		self.activeOperator = 0
		self.voices = dtfm_inst.getVoices()
		self.clusterCount = int(len(self.voices) / self.voicesPerCluster)
		
		remainingVoices = self.voices.copy()
		self.clusters = []
		for i in range(self.clusterCount):
			newCluster = Cluster(remainingVoices[:self.voicesPerCluster], self)
			newCluster.index = i
			self.clusters += [newCluster]
			remainingVoices = remainingVoices[self.voicesPerCluster:]
		
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
		
		self.loadJson(patchFilename)
	
	def getInitDict(self, patchDict):
		initDict = {}
		
		initDict["fm_algo" ], initDict["fbsrc"   ], initDict["sounding"] = algos.getAlgo(patchDict["Algorithm"])
		sounding0indexed = [s-1 for s in initDict["sounding"]]
		initDict["fbsrc"   ] = initDict["fbsrc"   ]-1
		initDict["fbgain"  ] = 2**16*patchDict["Feedback"] / 127.0         
		
		LFODict = patchDict["LFO"]
		initDict["channelgain"] = [2**16/8, 2**16/8]         
		initDict["env"]       = [0    , 0    , 0    , 0    , 0    , 0    , 2**29*LFODict["AM Depth"] / 127.0    ,2**30*LFODict["Pitch Mod Depth"] / 127.0]
		initDict["env_rate" ] = [2**27, 2**27, 2**27, 2**27, 2**27, 2**27, 2**26*LFODict["Delay"] / 127.0, 2**26*LFODict["Delay"] / 127.0]
		
		initDict["increment"      ] = [0    , 0    , 0    , 0    , 0    , 0    , 2**20*pow(LFODict["Speed"] / 127.0, 2), 2**18*LFODict["Speed"] / 127.0]
		initDict["increment_rate" ] = [2**22] * 8 
		
		initDict["flushspi"    ] = 0
		initDict["passthrough" ] = 0
		initDict["shift"       ] = max(2 - len(initDict["sounding"]), 0)
		
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
		
		initDict["am_algo" ] = 0x00000000
		# format am algo
		# am_algo_payload = int(0)
		# for i, src in enumerate(initDict["am_algo" ]):
		# 	am_algo_payload += src << (i*4)
		# initDict["am_algo" ] = am_algo_payload
		
		return initDict, sounding0indexed
	
	def setAllIncrements(self):
		# no way to avoid casting it seems
		#logger.debug(self.baseIncrement   )
		#logger.debug(self.incrementScale  )
		#logger.debug(self.strikeIncrement)
		#logger.debug(modifier)
		self.tosend = np.add(self.baseIncrement, self.getPitchMod() * self.strikeIncrement).astype(np.int32)
		for op in self.lowestVoice.operators[:6]:
			op.formatAndSend(dtfm.cmd_increment, self.tosend[:, op.index], voicemode = True)
	
	def loadJson(self, filename):
	
		with open(filename, 'r') as f:
			patchDict = json.loads(f.read())
		self.patchDict = patchDict
		logger.debug("loading " + patchDict["Name"])
		initDict, sounding0indexed = self.getInitDict(patchDict)
		
		# ignoring pitch envelope generator for now
		self.phaseCount       = np.zeros((dtfm.OPERATORCOUNT), dtype=np.int32)
		self.envRatePerSample = np.zeros((dtfm.OPERATORCOUNT, 100), dtype=np.int32)
		self.envThisLevel     = np.zeros((dtfm.OPERATORCOUNT, 100), dtype=np.int32)
		self.incrementScale   = np.zeros((dtfm.OPERATORCOUNT))
		self.baseIncrement    = np.zeros((dtfm.OPERATORCOUNT))
		self.strikeIncrement  = np.zeros((self.polyphony, dtfm.OPERATORCOUNT), dtype=np.int32)
		self.sounding         = np.zeros((dtfm.OPERATORCOUNT), dtype=np.int32)
			
		logger.debug("Kosherizing env vals")
		# setup env vals
		soundingops = 6
		for opno in range(soundingops):
			logger.debug("Operator" + str(opno+1))
			opDict = patchDict["Operator" + str(opno+1)]
			eps, ela = dtfm.getRateAndLevel(opDict, (opDict["Output Level"]))
			self.phaseCount[opno] = len(ela)
			self.envRatePerSample[opno,:self.phaseCount[opno]] = np.abs(eps)
			self.envThisLevel    [opno,:self.phaseCount[opno]] = ela
			
			# setup the frequencies
			if opDict["Oscillator Mode"] == "Frequency (Ratio)":
				self.baseIncrement [opno] = 0
				#self.incrementScale[opno] = opDict["Frequency"] * (1 + (opDict["Detune"] / 7.0) / 80)
				self.incrementScale[opno] = opDict["Frequency"] * (1 + (opDict["Detune"] / 7.0) / 30)

			else:
				self.baseIncrement [opno] = (2**32)*opDict["Frequency"] / dtfm.SamplesPerSecond
				self.incrementScale[opno] = 0
			
			self.sounding[opno] = 1 if opno in sounding0indexed else 0
		logger.debug("Done kosherizing")

		self.dtfm_inst.initialize(initDict, voices = self.voices)
		for cluster in self.clusters:
			cluster.update()
		return 0
		
	def processIRQueue(self, voiceno, opnos):
		
		for opno in opnos:
			if opno < 6:
				op = self.dtfm_inst.voices[voiceno].operators[opno]
				phase = (op.phase + 1) % self.phaseCount[opno]

				#logger.debug("\n\nproc IRQUEUE! voice:" + str(voiceno) + " op:"+ str(opno) + " phase:" + str(phase))

				if phase == 0:
					#logger.debug("STOP PHASE")
					pass
				elif phase == self.phaseCount[opno] - 1:
					#logger.debug("FALL PHASE, CAN ONLY BE RESTARTED BY NOTE-ON")
					pass
				else:
					op.phase = phase
					op.formatAndSend(dtfm.cmd_env_rate, 0)                               
					op.formatAndSend(dtfm.cmd_env,      self.envThisLevel[opno, phase])
					op.formatAndSend(dtfm.cmd_env_rate, self.envRatePerSample[opno, phase])                           
					#logger.debug("sending rate " + str(self.envRatePerSample[opno,phase]))
					#logger.debug("envRatePerSample:\n" + str(self.envRatePerSample))
					
	def getPitchMod(self):
		quantized = penta[int(self.aftertouchReal * 10)]
		
		return self.pitchwheelReal * quantized
		#return self.pitchwheelReal * (1 + self.aftertouchReal)
		
	def midi2commands(self, msg):
		loopstart = time.time()
	
		logger.debug("\n\nProcessing " + str(msg))
			
		if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
			if self.sustain:
				self.toRelease[msg.note] = True
				return
				
			note = self.allNotes[msg.note] 
			note.velocity = 0 
			note.velocityReal = 0 
			if note.cluster is not None:
				note.cluster.silenceAllOps()
			note.cluster = None
			note.held = False
			note.releaseTime = time.time()
		
		# if note on, spawn voices
		if msg.type == "note_on":
			note = self.allNotes[msg.note]
			note.velocity     = msg.velocity
			note.velocityReal = (msg.velocity/127.0)**2
			note.held = True
			note.msg = msg
			
			# spawn some voices!
			cluster = sorted(self.clusters, key=lambda x: x.spawntime)[0]
			cluster.spawntime = time.time()
			cluster.spawn(note)

		if msg.type == 'pitchwheel':
			logger.debug("PW: " + str(msg.pitch))
			self.pitchwheel = msg.pitch
			ARTIPHON = 1
			if ARTIPHON:
				self.pitchwheel *= 2
			amountchange = self.pitchwheel / 8192.0
			self.pitchwheelReal = pow(2, amountchange)
			logger.debug("PWREAL " + str(self.pitchwheelReal))
			self.setAllIncrements()
			
		elif msg.type == 'control_change':
						
			logger.debug("control : " + str(msg.control) + " (" + dtfm.controlNum2Name[msg.control] +  "): " + str(msg.value))

			event = "control[" + str(msg.control) + "]"
			
			# forward some controls
			
			# route control3 to control 7 because sometimes 3 is volume control
			if msg.control == 3:
				self.midi2commands(mido.Message('control_change', control= 7, value = msg.value ))
				
			if msg.control == dtfm.ctrl_vibrato_env:
				dtfm.formatAndSend(dtfm.cmd_env_rate , self.lowestVoiceIndex, 7, [0] * self.polyphony)
				dtfm.formatAndSend(dtfm.cmd_env , self.lowestVoiceIndex, 7, [(msg.value/127.0)*2**29] * self.polyphony)
				dtfm.formatAndSend(dtfm.cmd_env_rate , self.lowestVoiceIndex, 7, [(msg.value/127.0)*2**29] * self.polyphony)
				
			if msg.control == dtfm.ctrl_tremolo_env:
				dtfm.formatAndSend(dtfm.cmd_env_rate , self.lowestVoiceIndex, 6, [0] * self.polyphony)
				dtfm.formatAndSend(dtfm.cmd_env , self.lowestVoiceIndex, 6, [(msg.value/127.0)*2**29] * self.polyphony)
				dtfm.formatAndSend(dtfm.cmd_env_rate , self.lowestVoiceIndex, 6, [(msg.value/127.0)*2**29] * self.polyphony)
				
			if msg.control == dtfm.ctrl_silence:
				for op in range(6):
					dtfm.formatAndSend(dtfm.cmd_env , self.lowestVoiceIndex,      op, [0] * self.polyphony)
					dtfm.formatAndSend(dtfm.cmd_env_rate , self.lowestVoiceIndex, op, [0] * self.polyphony)
				
				
			# OPERATOR CONCERNS
			if msg.control == dtfm.ctrl_sustain: 
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
			
			self.setAllIncrements()
			#for voice in self.voices:
			#	if time.time() - voice.note.releaseTime > max(voice.envTimeSeconds[3,:]):
			#		voice.setAllIncrements(self.pitchwheelReal * (1 + self.aftertouchReal))
					
			
		if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
			# implement rising mono rate
			for heldnote in self.allNotes[::-1]:
				if heldnote.held and self.polyphony == self.voicesPerCluster :
					self.midi2commands(heldnote.msg)
					break
		
		logger.warning(time.time() - loopstart)
		return True

useMouse = False
class PatchManager():

	def checkForPatchChange(self):
		#check for patch change 
		try:
			string = self.patchSocket.recv_string(flags=zmq.NOBLOCK)
			logger.debug(string)
			self.GLOBAL_DEFAULT_PATCH.loadJson(string)
		except zmq.Again as e:
			pass
	
	def checkForNewDevices(self):
		midi_ports  = self.midiin.get_ports()
		for i, midi_portname in enumerate(midi_ports):
			if midi_portname not in self.midi_ports_last:
				logger.debug("adding " + midi_portname)
				try:
					mididev, midi_portno = open_midiinput(midi_portname)
				except (EOFError, KeyboardInterrupt):
					sys.exit()
	
				midiDevAndPatches = (mididev, [self.GLOBAL_DEFAULT_PATCH])
				self.allMidiDevicesAndPatches += [midiDevAndPatches]
		self.midi_ports_last = midi_ports

	def checkKeyboard(self):
		if not keyQueue.empty():
			keyDict = keyQueue.get()
			key = keyDict["name"]
			if key in qwerty2midi.keys():
				if keyDict["event_type"] == "down":
					msg = mido.Message('note_on',  note = qwerty2midi[key], velocity = 120)
				else:
					msg = mido.Message('note_off', note = qwerty2midi[key], velocity = 0)
					
				for dev, patches in self.allMidiDevicesAndPatches:
					for patch in patches:
						patch.midi2commands(msg)



	def checkMidi(self):
		
		for dev, patches in self.allMidiDevicesAndPatches:
			msg  = dev.get_message()
			msgs = []
			while msg is not None:
				msgs += [msg]
				msg  = dev.get_message()
				
			processedPW = False
			processedAT = False
			for msg in reversed(msgs): # most recent first
				
				msg, dtime = msg
				msg = mido.Message.from_bytes(msg)
				if msg.type == 'pitchwheel':
					if processedPW:
						continue
					else:
						processedPW = True
						
				if msg.type == 'aftertouch':
					if processedAT:
						continue
					else:
						processedAT = True
						
				logger.debug(msg)
				for patch in patches:
					patch.midi2commands(msg)
				
	
	def eventLoop(self):
	
		# loop related variables
		lastDevCheck    = 0
		lastPatchCheck    = 0
		mousePosLast = 0
		maxLoop = 0
		self.midi_ports_last = []
		self.allMidiDevicesAndPatches = []
		
		
		while(1):
			
			
			# check for new devices once a second
			if time.time()-lastDevCheck > 1:
				lastDevCheck = time.time()
				self.checkForNewDevices()
		
			#c = sys.stdin.read(1)
			#if c == 'd':
			#	dtfm_inst.dumpState()
			self.checkMidi()
			
			if useKeyboard:
				self.checkKeyboard()
				
			
			# process the IRQUEUE
			while(GPIO.input(37)):
				voiceno, opnos = dtfm.getIRQueue()
				self.GLOBAL_DEFAULT_PATCH.processIRQueue(voiceno, opnos)
				
			if time.time()-lastPatchCheck > 0.02:
				lastPatchCheck = time.time()
				self.checkForPatchChange()
			
			if useMouse:
				print("CHECKING MOUSE")
				mouseX, mouseY = mouse.get_position()
				#mouseX /= pyautogui.size()[0]
				#mouseY /= pyautogui.size()[1]
				mouseX /= 480
				mouseY /= 360
				if (mouseX, mouseY) != mousePosLast:
					mousePosLast = (mouseX, mouseY)
					self.GLOBAL_DEFAULT_PATCH.midi2commands(mido.Message('control_change', control= dtfm.ctrl_tremolo_env, value = int(mouseX*127)))
					self.GLOBAL_DEFAULT_PATCH.midi2commands(mido.Message('control_change', control= dtfm.ctrl_vibrato_env, value = int(mouseY*127)))
					#logger.debug((mouseX, mouseY))
						

			
	def startup(self, patchFilename):
		
		PID = os.getpid()
		if useKeyboard:
			logger.debug("setting up keyboard")
			keyQueue = queue.Queue()
			keyState = {}
			def print_event_json(event):
				keyDict = json.loads(event.to_json(ensure_ascii=sys.stdout.encoding != 'utf-8'))
				# protect against repeat delay, for simplicity
				# "xset r off" not working
				if keyState.get(keyDict["name"]) != keyDict["event_type"]:
					keyState[keyDict["name"]] = keyDict["event_type"]
					#keyQueue.put(json.dumps(keyDict))
					keyQueue.put(keyDict)
				#sys.stdout.flush()
			keyboard.hook(print_event_json)

		logger.setLevel(0)
		if len(sys.argv) > 1:
			logger.setLevel(1)
			
		logger.debug("Instantiating dtfm")
		self.polyphony = 512
		
		logger.debug("initializing from scratch")
		self.dtfm_inst = dtfm.dtfm(polyphony = self.polyphony)
			
		self.GLOBAL_DEFAULT_PATCH = Patch(self.dtfm_inst, patchFilename)
		
		api=rtmidi.API_UNSPECIFIED
		self.midiin = rtmidi.MidiIn(get_api_from_environment(api))
		
		dtfm.initIRQueue()
			
		# Socket to talk to server
		context = zmq.Context()
		self.patchSocket = context.socket(zmq.SUB)
		self.patchSocket.connect ("tcp://localhost:%s" % "5555")
		self.patchSocket.setsockopt_string(zmq.SUBSCRIBE, "")
		
		self.qwerty2midi = {'a':48, 's':50, 'd':52, \
			'f':53, 'g':55, 'h':57, 'j':59, 'k':60, 'l':62, \
			'w':49, 'e':51, 't':54, 'y':56, 'u':58, 'o':61, \
			'p':63, ';':65, "\'":67}

		logger.debug("Entering main loop. Press Control-C to exit.")
		try:
			# Just wait for keyboard interrupt,
			# everything else is handled via the input callback.
			self.eventLoop()
					
		except KeyboardInterrupt:
			logger.debug('')
		finally:
			logger.debug("Exit.")
			self.midiin.close_port()
			del self.midiin
if __name__ == "__main__":
	P = PatchManager()
	P.startup('/home/pi/dtfm/patches/aaa/Dlby Rude .json')
