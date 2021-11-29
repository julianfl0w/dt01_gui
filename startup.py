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
import spi_interface

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
	initCommands = dt01_inst.getInitCommands()
	for payload in initCommands:
		spi_interface.send(payload)
	
	
	GLOBAL_DEFAULT_PATCH = Patch(dt01_inst)
	#dt01_inst.addPatch(GLOBAL_DEFAULT_PATCH)
	
	api=rtmidi.API_UNSPECIFIED
	allMidiDevicesAndPatches = []
	midiin = rtmidi.MidiIn(get_api_from_environment(api))
	
	midi_ports_last = []
	
	# IRQUEUE Considerations
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(37 , GPIO.IN)
	# flush queue
	while(GPIO.input(37)):
		spi_interface.send(dt01.formatCommand(dt01.cmd_readirqueue, 0, 0, 0))
		res = spi_interface.send(dt01.formatCommand(0, 0, 0, 0))
	
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
						commands = patch.midi2commands(msg)
						logger.debug(commands)
						for payload in commands:
							spi_interface.send(payload)
				
					#logger.warning(time.time() - loopstart)
				
			# process the IRQUEUE
			if(GPIO.input(37)):
				spi_interface.send(dt01.formatCommand(dt01.cmd_readirqueue, 0, 0, 0))
				res = spi_interface.send(dt01.formatCommand(0, 0, 0, 0))
				logger.debug("res: " + str(res))
				opno = int(math.log2((res[1]<<7) + (res[2]>>1)))
				voiceno = int(((res[2] & 0x01)<<8) + res[3])
				logger.debug("IRQUEUE! voice:" + str(voiceno) + " op:"+ str(opno))
				currPhase = GLOBAL_DEFAULT_PATCH.envelopePhase[voiceno, opno]
					
				logger.debug("IRQUEUE! voice:" + str(voiceno) + " op:"+ str(opno) + " phase:" + str(currPhase))
				if np.sum(res) == 0:
					continue
				if currPhase >= GLOBAL_DEFAULT_PATCH.phaseCount - 1:
					logger.debug("STOP PHASE")
					continue
				logger.debug(GLOBAL_DEFAULT_PATCH.envelopePhase[0,:])
				#logger.debug("self.envelopeExp "   + str(self.envelopeExp  [opno][currPhase]))
				#logger.debug("self.envelopeLevel " + str(self.envelopeLevel[opno][currPhase]*baseEnv))
				#logger.debug("self.envelopeRate "  + str(self.envelopeRate [opno][currPhase]))
				
				logger.debug(res)
				
				commands = []
				commands += [dt01.formatCommand(dt01.cmd_env_rate, opno, voiceno, 0)                                  ]
				commands += [dt01.formatCommand(dt01.cmd_envexp,   opno, voiceno, GLOBAL_DEFAULT_PATCH.envelopeExp  [opno][currPhase])]
				commands += [dt01.formatCommand(dt01.cmd_env,      opno, voiceno, GLOBAL_DEFAULT_PATCH.envelopeLevel[opno][currPhase])]
				commands += [dt01.formatCommand(dt01.cmd_env_rate, opno, voiceno, GLOBAL_DEFAULT_PATCH.envelopeRate [opno][currPhase])]
				for payload in commands:
					logger.debug(dt01.controlNum2Name[payload[0]] + " " + str(payload[4:8]))
					spi_interface.send(payload)
				GLOBAL_DEFAULT_PATCH.envelopePhase[voiceno, opno] = (GLOBAL_DEFAULT_PATCH.envelopePhase[voiceno, opno] + 1) % GLOBAL_DEFAULT_PATCH.phaseCount
			
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