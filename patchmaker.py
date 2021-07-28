
cmd_fmdepth            = 68 
cmd_fmmod_selector     = 69 
cmd_ammod_selector     = 71 
cmd_pitchshiftdepth    = 87 
cmd_gain               = 90 
cmd_gain_porta         = 91 
cmd_increment          = 92 
cmd_increment_porta    = 93 
cmd_mastergain_right   = 95 
cmd_mastergain_left    = 96 
cmd_flushspi           = 120
cmd_passthrough        = 121
cmd_shift              = 122

HWIDTH = 1 

import struct
import sys
import numpy as np 

def format_command_real(mm_paramno = 0, noteno = 0,  payload = 0):
	payload = payload*(2**16)
	payload = struct.pack(">I", int(payload))
	payload = [mm_paramno, 0, 0, noteno] + [int(i) for i in payload]
	#print([hex(p) for p in payload])
	return payload
	
def format_command_int(mm_paramno = 0, mm_opno = 0,  noteno = 0,  payload = 0):
	payload = struct.pack(">I", int(payload))
	payload = [mm_paramno, mm_opno, 0, noteno] + [int(i) for i in payload]
	print([hex(p) for p in payload])
	return payload
	
def format_command_3bezier_targets(mm_paramno = 0, noteno = 0,  bt0 = 0, bt1 = 0, bt2 = 0):
	payload = struct.pack(">I", (int(bt0*(2**28)) & 0x3FF00000) + (int(bt1*(2**18)) & 0x000FFC00) + (int(bt2*(2**8)) & 0x000003FF))
	payload = [mm_paramno, 0, 0, noteno] + [int(p) for p in payload]
	#print([hex(p) for p in payload])
	return payload
	
import spidev
spi = spidev.SpiDev()

spi.open(1, 0)

speed = 20000000
spi.max_speed_hz=speed


import time
import rtmidi
from rtmidi.midiutil import *
import mido
import math

def noteToFreq(note):
	a = 440.0 #frequency of A (coomon value is 440Hz)
	return (a / 32) * (2 ** ((note - 9) / 12))

MIDINOTES      = 128
POLYPHONYCOUNT = 512
OPERATORCOUNT  = 8
CONTROLCOUNT   = 128

noteno = 0

class MidiInputHandler(object):
	def __init__(self, port):
		self.port = port
		self._wallclock  = time.time() 
		self.increment   = np.zeros((POLYPHONYCOUNT, OPERATORCOUNT))
		self.heldNotes   = -np.ones((MIDINOTES), dtype=int)
		self.controlVals = np.zeros((CONTROLCOUNT), dtype=int)
		self.pitchWheel  = 0.5
		self.afterTouch  = 0.0
		self.toRelease   = []
		self.mastergain_right_spawn = 2**16
		self.mastergain_left_spawn  = 2**16
		self.o1ratio = 1
		self.hold = 0
	
	def updateOperator(self):
		
	def updateVoice(self):
	
	def updateHeldNotes(self):
		
	
	def routine_noteoff(self, message):
		if self.hold > 64:
			self.toRelease += [message]
			return
	
		self.gainporta = 100
		self.voicegain = 0
		noteToSilence = int(self.heldNotes[message.note])
		print(noteToSilence)
		spi.xfer2( format_command_int(cmd_gain_porta	 , 0, noteToSilence, self.gainporta			))
		spi.xfer2( format_command_int(cmd_gain			 , 0, noteToSilence, self.voicegain				   ))
		spi.xfer2( format_command_int(cmd_increment_porta, 0, noteToSilence, 500 ))
		
		# delete this note
		print("deletomg")
		self.heldNotes[message.note] = -1
		
		if not any(self.heldNotes + 1) or POLYPHONYCOUNT > 1: 
			return
		message.note     = np.max(np.where(self.heldNotes))
		message.velocity = self.velocitylast
		
		self.routine_noteon(message)
		
		

	def routine_noteon(self, message):
		global noteno
		self.voicegain = int(2**16 * math.pow(message.velocity/128.0, 1/4.0))
		self.gainporta = 1
		self.velocitylast  = message.velocity
		thisinc = int(2**32  * noteToFreq(message.note) / 96000)
		self.increment[noteno][0] = thisinc
		self.incporta  = 2**16
			
		spi.xfer2( format_command_int(cmd_gain_porta	 , 0, noteno, self.gainporta))
		spi.xfer2( format_command_int(cmd_gain			 , 0, noteno, self.voicegain))
		spi.xfer2( format_command_int(cmd_increment_porta, 0, noteno, self.incporta))
		spi.xfer2( format_command_int(cmd_increment		 , 0, noteno, thisinc * self.pitchWheel))
		spi.xfer2( format_command_int(cmd_fmmod_selector , 0, noteno, 1))
		spi.xfer2( format_command_int(cmd_fmdepth        , 0, noteno, self.fmdepth_spawn))
		
		
		spi.xfer2( format_command_int(cmd_increment_porta, 1, noteno, self.incporta))
		spi.xfer2( format_command_int(cmd_increment		 , 1, noteno, thisinc * self.pitchWheel * self.o1ratio))
		spi.xfer2( format_command_int(cmd_fmmod_selector , 1, noteno, 2))
		
		spi.xfer2( format_command_int(cmd_mastergain_left,  0, noteno, self.mastergain_left_spawn ))
		spi.xfer2( format_command_int(cmd_mastergain_right, 0, noteno, self.mastergain_right_spawn))
		
		self.heldNotes[message.note] = int(noteno)
		noteno= (noteno+ 1) % POLYPHONYCOUNT
	
	def __call__(self, event, data=None):
		message, deltatime = event
		print(message)
		self._wallclock += deltatime
		#print("[%s] @%0.6f %r" % (self.port, self._wallclock, message))
		#print(message)
		message = mido.Message.from_bytes(message)
		#print(message.type)
		if message.type == 'note_on':
			if message.velocity == 0:
				self.routine_noteoff(message)
			else:
				self.routine_noteon(message)
				
		elif message.type == 'note_off':
			self.routine_noteoff(message)
			
		elif message.type == 'pitchwheel':
			print("PW: " + str(message.pitch))
			amountchange = message.pitch / 8192.0
			amountchange = pow(2, amountchange)
			
			self.pitchWheel = amountchange
			for i in self.heldNotes:
				if i != -1:
					spi.xfer2( format_command_int(cmd_increment, 0, int(i), self.increment[int(i)][0]*amountchange))
				
		
		elif message.type == 'aftertouch':
			amountchange = message.value / 128.0
			amountchange = pow(1.5, amountchange)
			
			self.pitchWheel = amountchange
			for i in self.heldNotes:
				if i != -1:
					spi.xfer2( format_command_int(cmd_increment, 0, int(i), self.increment[int(i)][0]*amountchange))
				
		
		elif message.is_cc():
			print('Control change message received: ' + str(message.control))
			if message.control == 1:
				print(message.value)
				for i, noteno in enumerate(self.heldNotes):
					if noteno >= 0:
						self.fmdepth_spawn = int(2**14*(message.value/128.0))
						cmd = format_command_int(cmd_fmdepth, 0, int(noteno), int(self.fmdepth_spawn))
						spi.xfer2(cmd)
			elif message.control == 12:
				for voice in range(POLYPHONYCOUNT):
					spi.xfer2( format_command_int(cmd_gain, 0, voice, 0 ))
					
			#	spi.xfer2( format_command_int(cmd_shift, 0, 0, message.value))
			elif message.control == 13:
				self.mastergain_right_spawn = 2**16*(message.value/128.0)
			elif message.control == 14:
				self.mastergain_left_spawn = 2**16*(message.value/128.0)
			elif message.control == 15:
				print(message.value)
				for i, noteno in enumerate(self.heldNotes):
					if noteno >= 0:
						self.o1ratio = (8 / (message.value))
						freq = self.increment[int(noteno)][0]*self.pitchWheel*self.o1ratio
						spi.xfer2( format_command_int(cmd_increment, 1, int(noteno), freq))
				
			elif message.control == 64: # sustain pedal
				self.hold = message.value
				if self.hold < 64:
					for release in self.toRelease:
						self.routine_noteoff(release)
					self.toRelease = []
			

		#spi.xfer2( format_command_int(cmd_increment_adj	, noteno, 0))
		#spi.xfer2( format_command_int(cmd_mod_selector	 , noteno, 0))
		
		
port = sys.argv[1] if len(sys.argv) > 1 else None
api=rtmidi.API_UNSPECIFIED
midiin = rtmidi.MidiIn(get_api_from_environment(api))
ports  = midiin.get_ports()
print(ports)
for port in ports:
	try:
		midiin, port_name = open_midiinput(port)
	except (EOFError, KeyboardInterrupt):
		sys.exit()


	print("Attaching MIDI input callback handler.")
	midiin.set_callback(MidiInputHandler(port_name))

spi.xfer2( format_command_int(cmd_mastergain_right, 0, 0, 2**16))
spi.xfer2( format_command_int(cmd_mastergain_left , 0, 0, 2**16))

spi.xfer2( format_command_int(cmd_flushspi , 0, 0, 1))
spi.xfer2( format_command_int(cmd_passthrough, 0, 0, 0))
spi.xfer2( format_command_int(cmd_shift, 0, 0, 4))

print("Entering main loop. Press Control-C to exit.")
try:
	# Just wait for keyboard interrupt,
	# everything else is handled via the input callback.
	while True:
		time.sleep(1)
		
except KeyboardInterrupt:
	print('')
finally:
	print("Exit.")
	midiin.close_port()
	del midiin
