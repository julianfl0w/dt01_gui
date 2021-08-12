
import spidev
import struct
maxSpiSpeed = 20000000
spi = spidev.SpiDev()
spi.open(1, 0)
spi.max_speed_hz=maxSpiSpeed
from bitarray import bitarray
import threading
from note import Note
from voice import Voice

		
class dt01():

	POLYPHONYCOUNT = 512
	OPERATORCOUNT  = 8

	def __init__(self):
		self.voiceno = 0# round robin voice allocation
		self.voices  = []
		for i in range(self.POLYPHONYCOUNT):
			self.voices += [Voice(i, self)]

		self.cmdDict = dict()
		self.cmdDict["cmd_fmdepth"          ] = 68 
		self.cmdDict["cmd_fmmod_selector"   ] = 69 
		self.cmdDict["cmd_ammod_selector"   ] = 71 
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
		
		self.lock = threading.Lock()

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
		#self.lock.acquire()
		toreturn = self.voices[self.voiceno]
		toreturn.controlPatch = controlPatch
		self.voiceno += 1
		#self.lock.release()
		return toreturn
		
	def send(self, param, mm_opno,  voiceno,  payload):
		print(param.ljust(20) + " operator:" + str(mm_opno) + " voice:" + str(voiceno) + " payload:" + str(payload))
		tosend = self.format_command_int(self.cmdDict[param], mm_opno, voiceno, payload)
		#self.lock.acquire()
		spi.xfer2(tosend)
		#self.lock.release()
		
if __name__ == "__main__":
	dt01_inst = dt01()
	# run testbench
	opno = 0
	voiceno = 0
	dt01_inst.send("cmd_mastergain_left", opno, voiceno, 2**16)
	dt01_inst.send("cmd_mastergain_right", opno, voiceno, 2**16)
	dt01_inst.send("cmd_gain_porta", opno, voiceno, 2**16)
	dt01_inst.send("cmd_gain", opno, voiceno, 2**16)
	dt01_inst.send("cmd_increment_porta", opno, voiceno, 2**30)
	dt01_inst.send("cmd_increment", opno, voiceno, 123956524)
	dt01_inst.send("cmd_fmmod_selector", opno, voiceno, 1)
	dt01_inst.send("cmd_fmdepth", opno, voiceno, 2**15)

	opno = 1
	dt01_inst.send("cmd_increment_porta", opno, voiceno, 2**30)
	dt01_inst.send("cmd_increment", opno, voiceno, 123956524)
	
	dt01_inst.send("cmd_flushspi", 0, 0, 0)
	dt01_inst.send("cmd_shift", 0, 0, 0)
		