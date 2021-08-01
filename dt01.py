
import spidev
import struct
maxSpiSpeed = 20000000
spi = spidev.SpiDev()
spi.open(1, 0)
spi.max_speed_hz=maxSpiSpeed
from bitarray import bitarray

class Voice:
	def __init__(self, index, dt01_inst):
		self.dt01_inst = dt01_inst
		self.index = index
		self.controlNote = None
		self.controlPatch = None
		self.sounding = True    
		self.fmMod = 0
		
	def __unicode__(self):
		return "#" + str(self.index)
		
	def __str__(self):
		return "#" + str(self.index)

	def send(self, mm_paramno, mm_opno, payload):
		self.dt01_inst.send(mm_paramno, mm_opno, self.index, payload)
	
	def getFmMod(self, opno, modno):
		mask  = 0x07 << 3*opno
		newval= (0x07 & modno) << 3*opno
		self.fmMod = (self.fmMod & ~mask) | newval	
		return self.fmMod
		
		
class dt01():

	POLYPHONYCOUNT = 512
	OPERATORCOUNT  = 8

	def __init__(self):
		self.voiceno = 0# round robin voice allocation
		self.voices  = []
		for i in range(self.POLYPHONYCOUNT):
			self.voices += [Voice(i, self)]

		self.cmdDict = dict()
		self.cmdDict["cmd_ENVELOPE_MIDnEND" ] = 1  
		self.cmdDict["cmd_ENVELOPE_ENV_SPEED"] = 3  
		self.cmdDict["cmd_PBEND_MIDnEND"    ] = 16 
		self.cmdDict["cmd_PBEND_ENV_SPEED"  ] = 18 
		self.cmdDict["cmd_HWIDTH_3TARGETS"  ] = 32 
		self.cmdDict["cmd_HWIDTH_ENV_SPEED" ] = 34 
		self.cmdDict["cmd_NFILTER_3TARGETS" ] = 48 
		self.cmdDict["cmd_NFILTER_ENV_SPEED"] = 50 
		self.cmdDict["cmd_GFILTER_3TARGETS" ] = 64 
		self.cmdDict["cmd_GFILTER_ENV_SPEED"] = 67 
		self.cmdDict["cmd_fmdepth"          ] = 68 
		self.cmdDict["cmd_fmmod_selector"   ] = 69 
		self.cmdDict["cmd_ammod_selector"   ] = 71 
		self.cmdDict["cmd_HARMONIC_WIDTH"   ] = 80 
		self.cmdDict["cmd_HARMONIC_WIDTH_INV"] = 81 
		self.cmdDict["cmd_HARMONIC_BASENOTE"] = 82 
		self.cmdDict["cmd_HARMONIC_ENABLE"  ] = 83 
		self.cmdDict["cmd_pitchshiftdepth"  ] = 87 
		self.cmdDict["cmd_centsinc"         ] = 88 
		self.cmdDict["cmd_gain"             ] = 90
		self.cmdDict["cmd_gain_porta"       ] = 91
		self.cmdDict["cmd_increment"        ] = 92
		self.cmdDict["cmd_increment_porta"  ] = 93
		self.cmdDict["cmd_mastergain_right" ] = 95
		self.cmdDict["cmd_mastergain_left"  ] = 96
		self.cmdDict["cmd_incexp"           ] = 97
		self.cmdDict["cmd_gainexp"] = 98
		self.cmdDict["cmd_env_clkdiv"] = 99
		self.cmdDict["cmd_flushspi"] = 120
		self.cmdDict["cmd_passthrough"] = 121
		self.cmdDict["cmd_shift"] = 122
		

	def format_command_real(self, mm_paramno, noteno,  payload):
		payload = payload*(2**16)
		payload = struct.pack(">I", int(payload))
		payload = [mm_paramno, 0, 0, noteno] + [int(i) for i in payload]
		#print([hex(p) for p in payload])
		return payload
		
	def format_command_int(self, mm_paramno, mm_opno,  noteno,  payload):
		payload_packed = struct.pack(">I", int(payload))
		payload_array = [mm_paramno, mm_opno, 0, noteno] + [int(i) for i in payload_packed]
		print([hex(p) for p in payload_array])
		return payload_array
		
	def format_command_3bezier_targets(self, mm_paramno, noteno,  bt0, bt1, bt2):
		payload = struct.pack(">I", (int(bt0*(2**28)) & 0x3FF00000) + (int(bt1*(2**18)) & 0x000FFC00) + (int(bt2*(2**8)) & 0x000003FF))
		payload = [mm_paramno, 0, 0, noteno] + [int(p) for p in payload]
		#print([hex(p) for p in payload])
		return payload
		
	def getVoice(self, controlPatch):
		toreturn = self.voices[self.voiceno]
		toreturn.controlPatch = controlPatch
		self.voiceno += 1
		return toreturn
		
	def send(self, mm_paramno, mm_opno,  noteno,  payload):
		#print(mm_paramno)
		if type(mm_paramno) == str:
			mm_paramno = self.cmdDict[mm_paramno]
		#print(mm_paramno)
		tosend = self.format_command_int(mm_paramno, mm_opno, noteno, payload)
		spi.xfer2(tosend)