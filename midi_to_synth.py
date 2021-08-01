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

 
logger = logging.getLogger('DT01')
formatter = logging.Formatter('{"debug": %(asctime)s %(message)s}')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

class initClass:
	def __init__(self):
		self.type = "init"

def noteToFreq(note):
	a = 440.0 #frequency of A (coomon value is 440Hz)
	return (a / 32) * (2 ** ((note - 9) / 12))

MIDINOTES      = 128
CONTROLCOUNT   = 128

class Note:
	def __init__(self, msg):
		self.index  = msg.note
		self.controlledVoices = []
		self.velocity = msg.velocity
		self.polyAftertouch = 0
		self.defaultIncrement = 2**32 * (noteToFreq(msg.note) / 96000.0)

class Patch:
	def __init__(self, patchFilename, midiInputInst, dt01_inst):
		with open(patchFilename) as f:
			self.paramdict = json.loads(f.read())
	
		self.polyphony = self.paramdict["metaDict"]["polyphony"]
		self.dt01_inst  = dt01_inst
		self.midiInputInst = midiInputInst
		self.voices = []
		self.soundingVoices = []
		self.idleVoices = []
		self.currVoice = 0
		for voicetoclaim in range(self.polyphony):
			claimedVoice = self.midiInputInst.dt01_inst.getVoice(self)
			logger.debug("claimed: " + str(claimedVoice.index))
			self.voices += [claimedVoice]
			self.idleVoices += [claimedVoice]
			
			commandDict = self.paramdict["voiceDict"]
			logger.debug(commandDict)
			for command, payload in commandDict.items():
				logger.debug(str(0) + " : " + command + " : " + str(payload) + " : " + str(eval(str(payload))))
				claimedVoice.send(dt01_inst.cmdDict[command], 0, int(eval(str(payload))))
					
		self.toRelease   = []
	
		
		logger.debug("init ")
		for opname, operator in self.paramdict["opParamDict"].items():
			logger.debug("op"+ opname + "\n---------------")
			opno = int(opname)
			commandDict = operator["init"]
			logger.debug(commandDict)
			for command, payload in commandDict.items():
				logger.debug(str(0) + " : " + command + " : " + str(payload) + " : " + str(eval(str(payload))))
				for voice in self.voices:
					logger.debug("voice #" + str(voice))
					voice.send(dt01_inst.cmdDict[command], opno, int(eval(str(payload))))
	
	
	def routine_noteoff(self, note):
		toremove = []
		for voice in note.controlledVoices:
			self.idleVoices += [voice]
			self.soundingVoices.remove(voice)

	def routine_noteon(self, note):
		if len(self.idleVoices):
			 thisVoice = self.idleVoices.pop()
			 logger.debug("applying to " + str(thisVoice))
			 self.soundingVoices += [thisVoice]
		else:
			thisVoice = self.soundingVoices[-1]
			
		thisVoice.controlNote = note
		note.controlledVoices += [thisVoice]
	
	def processEvent(self, msg):
		logger.debug("processing " + msg.type)
		for opname, operator in self.paramdict["opParamDict"].items():
			logger.debug("op"+ opname + "\n---------------")
			if msg.type not in operator.keys():
				logger.debug(operator.keys())
				logger.debug("WTF")
				return
			opno = int(opname)
			conditionDict = operator[msg.type]
			logger.debug(conditionDict)
			if conditionDict is not None:
				for condition, commandDict in conditionDict.items():
					logger.debug(commandDict)
					for command, payload in commandDict.items():
						for voice in self.soundingVoices: # only makes sense to modify active voices
						#for voice in self.voices: # only makes sense to modify active voices
							#logger.debug("MSG: " + str(msg.note))
							logger.debug("voice #" + str(voice))
							logger.debug(condition)
							if eval(condition):
								#logger.debug(condition)
								logger.debug(str(voice.index) + " : " + command + " : " + str(payload) + " : " + str(eval(str(payload))))
								#logger.debug(int(opname))
								#logger.debug(voice.index)
								#logger.debug(str(payload))
								#logger.debug(eval(str(payload)))
								
								voice.send(dt01_inst.cmdDict[command], opno, int(eval(str(payload))))
		
		
class MidiInputHandler:
		
	def __init__(self, midi_portname, dt01_inst):

		self.lock = threading.Lock()
		TCP_IP = '127.0.0.1'
		TCP_midi_portname = 5000 + int(midi_portname)
		BUFFER_SIZE = 50  # Normally 1024, but we want fast response

		self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.s.bind((TCP_IP, TCP_midi_portname))
		self.s.setblocking(False)
	
		self.dt01_inst = dt01_inst
		self.aftertouch = 0
		self.midi_portname  = midi_portname
		self._wallclock  = time.time() 
		self.control     = np.zeros((CONTROLCOUNT), dtype=int)
		self.pitchwheel  = 1
		self.physicallyHeldNotes   = []
		
		self.hold = 0
		
		patchFilename = os.path.join(sys.path[0], "patches/Classic/default.json")
		self.patches = [Patch(patchFilename, self, dt01_inst)]
		
		
	def routine_noteoff(self, msg):
	
		for note in self.physicallyHeldNotes:
			if note.index == msg.note:
				thisNote = note
				break
				
		self.physicallyHeldNotes.remove(thisNote)
		for patch in self.patches:
			patch.routine_noteoff(thisNote)

	def routine_noteon(self, msg):
		newNote = Note(msg)
		self.physicallyHeldNotes += [newNote]
		for patch in self.patches:
			patch.routine_noteon(newNote)
		
	def __call__(self, event, data=None):
		self.lock.acquire()
		starttime = time.time()
		msg, deltatime = event
		logger.debug(msg)
		self._wallclock += deltatime
		#logger.debug("[%s] @%0.6f %r" % (self.midi_portname, self._wallclock, msg))
		#logger.debug(msg)
		msg = mido.Message.from_bytes(msg)
		#logger.debug(msg.type)
		
		# first, update state of device
		if msg.type == 'note_on':
			if msg.velocity == 0:
				self.routine_noteoff(msg)
			else:
				self.routine_noteon(msg)
				
		elif msg.type == 'pitchwheel':
			logger.debug("PW: " + str(msg.pitch))
			amountchange = msg.pitch / 8192.0
			self.pitchwheel = pow(2, amountchange)
			
		elif msg.type == 'control_change':
			self.control[msg.control] = msg.value
			#logger.debug("msg.control" + str(msg.control))
			#logger.debug("msg.value" + str(msg.value))
			
		elif msg.type == 'polytouch':
			for note in self.physicallyHeldNotes:
				if note.index == msg.note:
					note.polyAftertouch = msg.value
			
		elif msg.type == 'aftertouch':
			self.aftertouch = msg.value
		
		logger.debug("\n\n\n---------------")
		logger.debug(msg.type)
		for patch in self.patches:
			patch.processEvent(msg)
		# remove active voices afterwards
			
		if msg.type == 'note_off':
			self.routine_noteoff(msg)
			
		logger.debug(self.physicallyHeldNotes)
		logger.debug("SELFCONTROL " + str(self.control[1]))
		print(time.time() - starttime)
		self.lock.release()
	

if __name__ == "__main__":

		
	midi_portname = sys.argv[1] if len(sys.argv) > 1 else None
	api=rtmidi.API_UNSPECIFIED
	midiDev = []
	midiin = rtmidi.MidiIn(get_api_from_environment(api))
	midi_ports  = midiin.get_ports()
	dt01_inst = dt01()
	
	dt01_inst.send( dt01_inst.cmdDict["cmd_flushspi"] , 0, 0, 1)
	dt01_inst.send( dt01_inst.cmdDict["cmd_passthrough"], 0, 0, 0)
	dt01_inst.send( dt01_inst.cmdDict["cmd_shift"], 0, 0, 4)
	dt01_inst.send( dt01_inst.cmdDict["cmd_env_clkdiv"], 0, 0, 5)
	
	logger.debug(midi_ports)
	#for i, midi_portname in enumerate(midi_ports):
	for i, midi_portname in enumerate(midi_ports[1:]):
		try:
			midiin, midi_portno = open_midiinput(midi_portname)
		except (EOFError, KeyboardInterrupt):
			sys.exit()


		logger.debug("Attaching MIDI input callback handler.")
		MidiInputHandler_inst = MidiInputHandler(i, dt01_inst)
		midiin.set_callback(MidiInputHandler_inst)
		midiDev += [MidiInputHandler_inst]


	logger.debug("Entering main loop. Press Control-C to exit.")
	try:
		# Just wait for keyboard interrupt,
		# everything else is handled via the input callback.
		while True:
			for dev in midiDev:
				try:
					data = dev.s.recv(50)
					if len(data):
						dev.loadPatch(data)
				except BlockingIOError as e:
					pass
			
	except KeyboardInterrupt:
		logger.debug('')
	finally:
		logger.debug("Exit.")
		midiin.close_port()
		del midiin