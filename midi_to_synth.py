cmd_ENVELOPE_MIDnEND   = 1
cmd_ENVELOPE_ENV_SPEED = 3

cmd_PBEND_MIDnEND	  = 16
cmd_PBEND_ENV_SPEED	= 18

cmd_HWIDTH_3TARGETS	= 32
cmd_HWIDTH_ENV_SPEED   = 34

cmd_NFILTER_3TARGETS   = 48
cmd_NFILTER_ENV_SPEED  = 50
			 
cmd_GFILTER_3TARGETS   = 64
cmd_GFILTER_ENV_SPEED  = 67

cmd_HARMONIC_WIDTH	 = 80
cmd_HARMONIC_WIDTH_INV = 81
cmd_HARMONIC_BASENOTE  = 82
cmd_HARMONIC_ENABLE	= 83
cmd_fmfactor		   = 85
cmd_fmdepth			= 86
cmd_pitchshiftdepth	= 87
cmd_centsinc		   = 88
cmd_master_gain		= 89
cmd_gain			   = 90
cmd_gain_porta		 = 91
cmd_increment		  = 92
cmd_increment_porta	= 93
cmd_increment_adj   = 94
cmd_mod_atten	   = 95
cmd_mod_selector	= 96
cmd_flushspi    = 120
cmd_passthrough = 121

HWIDTH = 1 

import struct
import sys

def format_command_real(mm_paramno = 0, mm_noteno = 0,  payload = 0):
	payload = payload*(2**16)
	payload = struct.pack(">I", int(payload))
	payload = [mm_paramno, 0, 0, mm_noteno] + [int(i) for i in payload]
	print([hex(p) for p in payload])
	return payload
	
def format_command_int(mm_paramno = 0, mm_noteno = 0,  payload = 0):
	payload = struct.pack(">I", int(payload))
	payload = [mm_paramno, 0, 0, mm_noteno] + [int(i) for i in payload]
	print([hex(p) for p in payload])
	return payload
	
def format_command_int_op(mm_paramno = 0, mm_opno = 0,  mm_noteno = 0,  payload = 0):
	payload = struct.pack(">I", int(payload))
	payload = [mm_paramno, mm_opno, 0, mm_noteno] + [int(i) for i in payload]
	print([hex(p) for p in payload])
	return payload
	
def format_command_3bezier_targets(mm_paramno = 0, mm_noteno = 0,  bt0 = 0, bt1 = 0, bt2 = 0):
	payload = struct.pack(">I", (int(bt0*(2**28)) & 0x3FF00000) + (int(bt1*(2**18)) & 0x000FFC00) + (int(bt2*(2**8)) & 0x000003FF))
	payload = [mm_paramno, 0, 0, mm_noteno] + [int(p) for p in payload]
	print([hex(p) for p in payload])
	return payload
	
import spidev
spi = spidev.SpiDev()

spi.open(1, 0)

speed = 2000000
spi.max_speed_hz=speed


import time
import rtmidi
from rtmidi.midiutil import open_midiinput
import mido
import math

def noteToFreq(note):
	a = 440.0 #frequency of A (coomon value is 440Hz)
	return (a / 32) * (2 ** ((note - 9) / 12))


class MidiInputHandler(object):
	def __init__(self, port):
		self.port = port
		self._wallclock = time.time()
		self.increment = 0
		self.heldNotes = dict()
	
	def routine_noteoff(self, message):
		self.gainporta = 1
		self.voicegain = 0
		mm_noteno = 0
		spi.xfer2( format_command_int(cmd_gain_porta	 , mm_noteno, self.gainporta			))
		spi.xfer2( format_command_int(cmd_gain			 , mm_noteno, self.voicegain				   ))
		spi.xfer2( format_command_int(cmd_increment_porta, mm_noteno, 500 ))
		spi.xfer2( format_command_int(cmd_increment		 , mm_noteno, self.increment))
		
		# delete this note
		del self.heldNotes[str(message.note)]
		
		if len(self.heldNotes.keys()) == 0: 
			return
		message.note     = max([int(i) for i in self.heldNotes.keys()])
		message.velocity = self.velocitylast
		
		self.routine_noteon(message)
		
		

	def routine_noteon(self, message):
		self.voicegain = int(2**16 * math.sqrt(message.velocity/128.0))
		self.gainporta = 20
		self.velocitylast  = message.velocity
		#self.increment = int(2**32 * noteToFreq(message.note) / 96000)
		self.increment = int(2**29 * noteToFreq(message.note) / 96000)
		mm_noteno = 0
			
		spi.xfer2( format_command_int(cmd_gain_porta	 , mm_noteno, self.gainporta))
		spi.xfer2( format_command_int(cmd_gain			 , mm_noteno, self.voicegain))
		spi.xfer2( format_command_int(cmd_increment_porta, mm_noteno, 500 ))
		spi.xfer2( format_command_int(cmd_increment		, mm_noteno, self.increment))
		spi.xfer2( format_command_int(cmd_mod_atten		, mm_noteno, 2**15))
		
		self.heldNotes[str(message.note)] = mm_noteno
	
	def __call__(self, event, data=None):
		message, deltatime = event
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

		#spi.xfer2( format_command_int(cmd_increment_adj	, mm_noteno, 0))
		#spi.xfer2( format_command_int(cmd_mod_selector	 , mm_noteno, 0))
		
		
port = sys.argv[1] if len(sys.argv) > 1 else None
try:
	midiin, port_name = open_midiinput(port)
except (EOFError, KeyboardInterrupt):
	sys.exit()


print("Attaching MIDI input callback handler.")
midiin.set_callback(MidiInputHandler(port_name))

spi.xfer2( format_command_int(cmd_master_gain, 1, 1))
spi.xfer2( format_command_int(cmd_master_gain, 0, 1))

spi.xfer2( format_command_int(cmd_flushspi, 0, 1))
spi.xfer2( format_command_int(cmd_passthrough, 0, 0))

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
