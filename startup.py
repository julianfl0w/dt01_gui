import struct
import sys
import numpy as np 
import dt01
from patch import *
import time
import rtmidi
from rtmidi.midiutil import *
from rtmidi.midiutil import open_midiinput
import mido
import math
import hjson as json
import socket
import os
import logging
import threading
import faulthandler
import traceback
import re

# Import the package and create an audio effects chain function.
from pysndfx import AudioEffectsChain
fx = (
    AudioEffectsChain()
    #.highshelf()
    .reverb()
    #.phaser()
    #.delay()
    #.lowshelf()
)
audio = np.random.rand(256*8)

faulthandler.enable()
 

if __name__ == "__main__":
	
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
	filename = "dt01_" + str(int(polyphony)) + ".pkl"

	#if os.path.exists(filename):
	#	logger.debug("reading from file")
	#	dt01_inst = dt01.DT01_fromFile(filename)
	#	logger.debug("finished reading")
	#else:
	logger.debug("initializing from scratch")
	dt01_inst = dt01.DT01(polyphony = polyphony)
	logger.debug("saving to file")
	dt01_inst.toFile(filename)
	
	logger.debug("Initializing")
	dt01_inst.initialize()
	
	
	GLOBAL_DEFAULT_PATCH = Patch(dt01_inst)
	#dt01_inst.addPatch(GLOBAL_DEFAULT_PATCH)
	
	api=rtmidi.API_UNSPECIFIED
	allMidiDevicesAndPatches = []
	midiin = rtmidi.MidiIn(get_api_from_environment(api))
	
	midi_ports_last = []
	
	dt01.initIRQueue()
	
	logger.debug("Entering main loop. Press Control-C to exit.")
	lastCheck = 0
	try:
		maxLoop = 0
		# Just wait for keyboard interrupt,
		# everything else is handled via the input callback.
		while True:
			loopstart = time.time()
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
				
					#logger.warning(time.time() - loopstart)
				
			# process the IRQUEUE
			if(GPIO.input(37)):
				voiceno, opno = dt01.getIRQueue()
				GLOBAL_DEFAULT_PATCH.processIRQueue(voiceno, opno)
				
			thisLoop = time.time() - loopstart
			maxLoop = max([thisLoop, maxLoop])
			
			#fxstart = time.time()
			#y = fx(audio)
			#fxtime = time.time() - fxstart
			#logger.warning("fxtime: " + str(fxtime))

			
	except KeyboardInterrupt:
		logger.debug('')
	finally:
		logger.debug("Exit.")
		midiin.close_port()
		del midiin