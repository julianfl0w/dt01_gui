import struct
import sys
import numpy as np 
from dt01 import *
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
from patch import *
import traceback
import re

faulthandler.enable()
 
logger = logging.getLogger('DT01')
formatter = logging.Formatter('{"debug": %(asctime)s {%(pathname)s:%(lineno)d} %(message)s}')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(1)

		
def noteToFreq(note):
	a = 440.0 #frequency of A (coomon value is 440Hz)
	return (a / 32) * (2 ** ((note - 9) / 12))


class Note:
	def __init__(self, index):
		self.index  = index
		self.voices = []
		self.velocity = 0
		self.held  = False
		self.polyAftertouch = 0
		self.msg  = None
		self.defaultIncrement = 2**32 * (noteToFreq(index) / 96000.0)

class MidiDevice(object):
		
	def __init__(self, i, patch, midi_portname, dt01_inst):
		print(midi_portname)
		midi_portname_file = re.sub(r'\W+', '', midi_portname) + ".txt"
		faulthandler.dump_traceback(file=open(midi_portname_file, "w+"), all_threads=False)
		logger.debug("__init__")
		self.lock = threading.Lock()
		TCP_IP = '127.0.0.1'
		TCP_midi_portname = 5000 + int(i)
		BUFFER_SIZE = 50  # Normally 1024, but we want fast response

		#self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		#self.s.bind((TCP_IP, TCP_midi_portname))
		#self.s.setblocking(False)
	
		self.dt01_inst = dt01_inst
		self.midi_portname  = midi_portname
		self._wallclock  = time.time() 
		
		self.hold = 0 
		
		self.patches = [patch]
		
		
		
	def __call__(self, event, data=None):
		logger.debug("__CALL__")
		#return 0
		#self.lock.acquire()
		starttime = time.time() 
		msg, deltatime = event
		logger.debug(msg)
		self._wallclock += deltatime
		#logger.debug("[%s] @%0.6f %r" % (self.midi_portname, self._wallclock, msg))
		#logger.debug(msg)
		msg = mido.Message.from_bytes(msg)
		logger.debug("processing " + msg.type)
		
		
		logger.debug("\n\n\n---------------")
		logger.debug(msg.type)
		for patch in self.patches:
			patch.processEvent(msg)
			#try: 
			#	patch.processEvent(msg)
			#except Exception as e:
			#	logger.debug(type(e))
			#	
		# remove active voices afterwards
			
		logger.debug(time.time() - starttime)
		#self.lock.release()


if __name__ == "__main__":
	
		
	api=rtmidi.API_UNSPECIFIED
	midiDev = []
	midiin = rtmidi.MidiIn(get_api_from_environment(api))
	midi_ports  = midiin.get_ports()
	dt01_inst = dt01()
	GLOBAL_DEFAULT_PATCH = Patch(self, dt01_inst)
	
	logger.debug(midi_ports)
	#for i, midi_portname in enumerate(midi_ports):
	for i, midi_portname in enumerate(midi_ports[1:]):
		try:
			midiin, midi_portno = open_midiinput(midi_portname)
		except (EOFError, KeyboardInterrupt):
			sys.exit()


		logger.debug("Attaching MIDI input callback handler.")
		MidiDevice_inst = MidiDevice(i, GLOBAL_DEFAULT_PATCH, str(midi_portname), dt01_inst)
		midiin.set_callback(MidiDevice_inst)
		logger.debug("Handler: " + str(midiin))
		#midiDev += [MidiDevice_inst]


	logger.debug("Entering main loop. Press Control-C to exit.")
	try:
		# Just wait for keyboard interrupt,
		# everything else is handled via the input callback.
		while True:
			#for dev in midiDev:
			#	try:
			#		data = dev.s.recv(50)
			#		if len(data):
			#			dev.loadPatch(data)
			#	except Exception as e:
			#		#logger.debug(Exception)
			#		pass
			pass
				
			
	except KeyboardInterrupt:
		logger.debug('')
	finally:
		logger.debug("Exit.")
		midiin.close_port()
		del midiin