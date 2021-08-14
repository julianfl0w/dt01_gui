
import spidev
import struct
maxSpiSpeed = 22000000
spi = spidev.SpiDev()
spi.open(1, 0)
spi.max_speed_hz=maxSpiSpeed
from bitarray import bitarray
import threading
from note import Note
from voice import Voice
import logging

logger = logging.getLogger('DT01')
		
class dt01():

	POLYPHONYCOUNT = 512

	def __init__(self):
		self.lock = threading.Lock()
		self.voiceno = 0# round robin voice allocation
		self.voices  = []
		expressionDict = dict()
		for i in range(self.POLYPHONYCOUNT):
			newVoice = Voice(i, self)
			self.voices += [newVoice]

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
		
		
		self.send("cmd_env_clkdiv"   , 0, 0, 2)
		self.send("cmd_flushspi"     , 0, 0, 0)
		self.send("cmd_passthrough"  , 0, 0, 0)
		self.send("cmd_shift"        , 0, 0, 2)
		

	def format_command_real(self, mm_paramno, voiceno,  payload):
		payload = payload*(2**16)
		payload = struct.pack(">I", int(payload))
		payload = [mm_paramno, 0, 0, voiceno] + [int(i) for i in payload]
		#print([hex(p) for p in payload])
		return payload
		
	def format_command_int(self, mm_paramno, mm_opno,  voiceno,  payload):
		payload_packed = struct.pack(">I", int(payload))
		payload_array = [mm_paramno, mm_opno, 0, voiceno] + [int(i) for i in payload_packed]
		#print([hex(p) for p in payload_array])
		return payload_array
		
	def format_command_3bezier_targets(self, mm_paramno, voiceno,  bt0, bt1, bt2):
		payload = struct.pack(">I", (int(bt0*(2**28)) & 0x3FF00000) + (int(bt1*(2**18)) & 0x000FFC00) + (int(bt2*(2**8)) & 0x000003FF))
		payload = [mm_paramno, 0, 0, voiceno] + [int(p) for p in payload]
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
		tosend = self.format_command_int(self.cmdDict[param], mm_opno, voiceno, payload)
		self.lock.acquire()
		logger.debug(param.ljust(20) + " operator:" + str(mm_opno) + " voice:" + str(voiceno) + " payload:" + str(payload))
		spi.xfer2(tosend)
		#logger.debug("sent")
		self.lock.release()
		
if __name__ == "__main__":
	dt01_inst = dt01()
	
	#for voiceno in range(dt01_inst.POLYPHONYCOUNT):
	#	for opno in range(dt01_inst.OPERATORCOUNT):
	#		for command in dt01_inst.cmdDict.keys():
	#			dt01_inst.send(command, opno, voiceno, 0)
				
	# run testbench
	dt01_inst.send("cmd_env_clkdiv", 0, 0, 0)
	
	opno = 0
	voiceno = 0
	dt01_inst.send("cmd_mastergain_right", opno, voiceno, 2**16)
	dt01_inst.send("cmd_gain_porta", opno, voiceno, 2**16)
	dt01_inst.send("cmd_gain", opno, voiceno, 2**16)
	dt01_inst.send("cmd_increment_porta", opno, voiceno, 2**30)
	dt01_inst.send("cmd_increment", opno, voiceno, 2**22)
	dt01_inst.send("cmd_fmmod_selector", opno, voiceno, 1)
	dt01_inst.send("cmd_fmdepth", opno, voiceno, 0)

	opno = 1
	dt01_inst.send("cmd_increment_porta", opno, voiceno, 2**30)
	dt01_inst.send("cmd_increment", opno, voiceno, 2**22)
	dt01_inst.send("cmd_fmdepth", opno, voiceno, 0)
	dt01_inst.send("cmd_fmmod_selector", opno, voiceno, 2)
	
	dt01_inst.send("cmd_flushspi", 0, 0, 0)
	dt01_inst.send("cmd_shift", 0, 0, 0)
		