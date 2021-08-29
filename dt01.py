import spidev
import struct
maxSpiSpeed = 20000000
spi = spidev.SpiDev()
spi.open(1, 0)
spi.max_speed_hz=maxSpiSpeed
from bitarray import bitarray
import logging
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
from ilock import ILock

logger = logging.getLogger('DT01')

class DT01_Voice:

	def __init__(self, index, dt01_inst):
		
		self.cmdDict = dict()
		self.cmdDict["cmd_algorithm"        ] = 69 
		self.cmdDict["cmd_mastergain_right" ] = 95 
		self.cmdDict["cmd_mastergain_left"  ] = 96 
		self.functionDict  = dict()
		self.functionDict["cmd_mastergain_right"] = self.fn_mastergain_right
		self.functionDict["cmd_mastergain_left" ] = self.fn_mastergain_left 
		self.functionDict["cmd_algorithm"       ] = self.fn_algorithm 
		
		self.dt01_inst = dt01_inst
		self.index = index
		self.note = None
		self.patch  = None
		self.sounding = False    
		self.defaultIncrement = 0
		self.indexInCluster = 0
		self.OPERATORCOUNT  = 8
		self.stateInFPGA = dict()
		self.operators = []
		self.operators += [DT01_Operator0(self, 0, dt01_inst)]
		self.operators += [DT01_Operator1(self, 1, dt01_inst)]
		self.operators += [DT01_Operator2(self, 2, dt01_inst)]
		self.operators += [DT01_Operator3(self, 3, dt01_inst)]
		self.operators += [DT01_Operator4(self, 4, dt01_inst)]
		self.operators += [DT01_Operator5(self, 5, dt01_inst)]
		self.operators += [DT01_Operator6(self, 6, dt01_inst)]
		self.operators += [DT01_Operator7(self, 7, dt01_inst)]
		self.computedState = dict()
		for key in self.functionDict.keys():
			self.compute(key)


	def computeAndSendAll(self):
		logger.debug("updating all")
		for param in self.functionDict.keys():
			self.computeAndSend(param)
		for operator in self.operators:
			operator.computeAndSendAll()

	def fn_mastergain_right(self)   : return  2**16 
	def fn_mastergain_left (self)   : return  2**16 
	def fn_algorithm (self)         : return 0x00000001

	def compute(self, param):
		self.computedState[param] = self.functionDict[param]()

	def note_on(self):
		logger.debug("applying to " + str(self))
		self.sounding = True
		for operator in self.operators:
			operator.note_on()

	def note_off(self):
		logger.debug("applying to " + str(self))
		self.sounding = False
		for operator in self.operators:
			operator.note_off()
			
	def pitchwheel(self):
		for operator in self.operators:
			operator.pitchwheel()
			
	def polytouch(self):
		for operator in self.operators:
			operator.polytouch()
			
	def aftertouch(self):
		for operator in self.operators:
			operator.aftertouch()
			
	def control_change(self):
		for operator in self.operators:
			operator.control_change()
		

	def __unicode__(self):
		return "#" + str(self.index)

	def __str__(self):
		return "#" + str(self.index)

	def computeAndSend(self, param):
		self.compute(param)
		# only write the thing if it changed
		if self.computedState[param] != self.stateInFPGA.get(param):
			self.stateInFPGA[param] = self.computedState[param]
			self.dt01_inst.send(param, 0, self.index, self.computedState[param])
		else:
			pass
			#logger.debug("Not sending")
			
			

# OPERATOR DESCRIPTIONS
class DT01_Operator:
	def __init__(self, voice, index, dt01_inst):
		self.dt01_inst = dt01_inst
		self.index = index
		self.voice = voice
		self.functionDict  = dict()
		self.computedState = dict()
		self.stateInFPGA   = dict()
		self.algorithm = 0
		self.initFns()
		
		self.cmdDict = dict()
		self.cmdDict["cmd_fmdepth"          ] = 68
		self.cmdDict["cmd_ammod_selector"   ] = 71
		self.cmdDict["cmd_gain"             ] = 90
		self.cmdDict["cmd_gain_porta"       ] = 91
		self.cmdDict["cmd_increment"        ] = 92
		self.cmdDict["cmd_increment_porta"  ] = 93
		self.cmdDict["cmd_incexp"           ] = 97
		self.cmdDict["cmd_gainexp"          ] = 98
		

	def initFns(self):
		self.functionDict["cmd_gain_porta"     ] = self.fn_gain_porta     
		self.functionDict["cmd_gain"           ] = self.fn_gain           
		self.functionDict["cmd_increment"      ] = self.fn_increment      
		self.functionDict["cmd_increment_porta"] = self.fn_increment_porta
		self.functionDict["cmd_fmdepth"        ] = self.fn_fmdepth        
		self.functionDict["cmd_incexp"         ] = self.fn_incexp         
		self.functionDict["cmd_gainexp"        ] = self.fn_gainexp        

	def fn_gain_porta     (self) : return 2**4                                                        
	def fn_gain           (self) : return self.voice.note.velocity*(2**16)/128.0                      
	def fn_increment      (self) : return self.voice.patch.pitchwheel * self.voice.note.defaultIncrement * (2 ** (self.voice.indexInCluster - (self.voice.patch.voicesPerNote-1)/2)) * (1 + self.voice.patch.aftertouch/128.0)
	def fn_increment_porta(self) : return 2**22*(self.voice.patch.control[4]/128.0)                          
	def fn_fmdepth        (self) : return 0                                                            
	def fn_incexp         (self) : return 1                                                            
	def fn_gainexp        (self) : return 1                                                            


	def computeAndSendAll(self):
		for param in self.functionDict.keys():
			self.computeAndSend(param)

	def compute(self, param):
		self.computedState[param] = self.functionDict[param]()

	def __unicode__(self):
		return "#" + str(self.index)

	def __str__(self):
		return "#" + str(self.index)

	def computeAndSend(self, param):
		self.compute(param)
		# only write the thing if it changed
		if self.computedState[param] != self.stateInFPGA.get(param):
			self.stateInFPGA[param] = self.computedState[param]
			self.dt01_inst.send(param, self.index, self.voice.index, self.computedState[param])
		else:
			pass
			#logger.debug("Not sending")

	def note_on(self):
		self.computeAndSend("cmd_gain"     )
		self.computeAndSend("cmd_increment")

	def note_off(self):
		self.computeAndSend("cmd_gain"     )
		
	def pitchwheel(self):
		self.computeAndSend("cmd_increment")
		
	def polytouch(self):
		self.computeAndSend("cmd_increment")
		
	def aftertouch(self):
		self.computeAndSend("cmd_increment")
		
	def control_change(self):
		pass
		

		
		
class DT01_Operator0(DT01_Operator):	
	def setFMDepth(self)       : self.send("cmd_fmdepth"        ,  payload = int(2**14 * (self.voice.patch.control[1]/128.0)))
	def control_change(self):
		self.computeAndSend("cmd_fmdepth")
	def __init__(self, voice, index, dt01_inst):
		super().__init__(voice, index, dt01_inst)
class DT01_Operator1(DT01_Operator):	
	def __init__(self, voice, index, dt01_inst):
		super().__init__(voice, index, dt01_inst)
class DT01_Operator2(DT01_Operator):	
	def __init__(self, voice, index, dt01_inst):
		super().__init__(voice, index, dt01_inst)
class DT01_Operator3(DT01_Operator):	
	def __init__(self, voice, index, dt01_inst):
		super().__init__(voice, index, dt01_inst)
class DT01_Operator4(DT01_Operator):	
	def __init__(self, voice, index, dt01_inst):
		super().__init__(voice, index, dt01_inst)
class DT01_Operator5(DT01_Operator):	
	def __init__(self, voice, index, dt01_inst):
		super().__init__(voice, index, dt01_inst)
class DT01_Operator6(DT01_Operator):	
	def __init__(self, voice, index, dt01_inst):
		super().__init__(voice, index, dt01_inst)
class DT01_Operator7(DT01_Operator):	
	def __init__(self, voice, index, dt01_inst):
		super().__init__(voice, index, dt01_inst)

		
			
class dt01():

	POLYPHONYCOUNT = 512

	def __init__(self):
		self.voiceno = 0# round robin voice allocation
		self.voices  = []
		expressionDict = dict()
		for i in range(self.POLYPHONYCOUNT):
			newVoice = DT01_Voice(i, self)
			self.voices += [newVoice]

		self.cmdDict = dict()
		self.cmdDict["cmd_fmdepth"          ] = 68 
		self.cmdDict["cmd_algorithm"        ] = 69 
		self.cmdDict["cmd_ammod_selector"   ] = 71  
		self.cmdDict["cmd_gain"             ] = 90
		self.cmdDict["cmd_gain_porta"       ] = 91
		self.cmdDict["cmd_increment"        ] = 92
		self.cmdDict["cmd_increment_porta"  ] = 93
		self.cmdDict["cmd_mastergain_right" ] = 95 
		self.cmdDict["cmd_mastergain_left"  ] = 96
		self.cmdDict["cmd_incexp"           ] = 97
		self.cmdDict["cmd_gainexp"          ] = 98
		self.cmdDict["cmd_env_clkdiv"       ] = 99
		self.cmdDict["cmd_flushspi"         ] = 120
		self.cmdDict["cmd_passthrough"      ] = 121
		self.cmdDict["cmd_shift"            ] = 122
		
		
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
		
	def format_command_word(self, mm_paramno, mm_opno,  voiceno, voicemode = 0):
		payload_array = [mm_paramno, 1 << mm_opno, (voicemode << 7) | (voiceno >> 8), voiceno]
		#print([hex(p) for p in payload_array])
		return payload_array
		
	def format_command_int(self, mm_paramno, mm_opno,  voiceno,  payload, voicemode = 0):
		payload_packed = struct.pack(">I", int(payload))
		payload_array = [mm_paramno, 1 << mm_opno, (voicemode << 7) | (voiceno >> 8), voiceno] + [int(i) for i in payload_packed] 
		#print([hex(p) for p in payload_array])
		return payload_array
		
	def format_command_3bezier_targets(self, mm_paramno, voiceno,  bt0, bt1, bt2):
		payload = struct.pack(">I", (int(bt0*(2**28)) & 0x3FF00000) + (int(bt1*(2**18)) & 0x000FFC00) + (int(bt2*(2**8)) & 0x000003FF))
		payload = [mm_paramno, 0, 0, voiceno] + [int(p) for p in payload]
		#print([hex(p) for p in payload])
		return payload
		
	def getVoices(self, controlPatch, voicesToGet = 32):
		toreturn = []
		with ILock('jlock'):
			for i in range(voicesToGet):
				toreturn += [self.voices[self.voiceno]]
				self.voices[self.voiceno].controlPatch = controlPatch
				self.voiceno += 1
		return toreturn
		
	def sendMultiple(self, param, opno, voiceno, payload, voicemode = 0):
		packstring = ">" + str(int(len(payload)/4)) + "I"
		payload = np.array(payload, dtype=np.int)
		payload_packed = struct.pack(packstring, *payload)
		tosend = self.format_command_int(self.cmdDict[param], opno, voiceno, 0)
		with ILock('jlock'):
			print("tslen: " + str(len(tosend[:4])))
			spi.xfer2(tosend[:4] + payload_packed)
			#logger.debug("sent")
	
	def send(self, param, mm_opno,  voiceno,  payload):
		tosend = self.format_command_int(self.cmdDict[param], mm_opno, voiceno, payload)
		with ILock('jlock'):
			logger.debug(param.ljust(20) + " operator:" + str(mm_opno) + " voice:" + str(voiceno) + " payload:" + str(payload))
			spi.xfer2(tosend)
			#logger.debug("sent")
		
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
	dt01_inst.send("cmd_gain_porta"      , opno, voiceno, 2**16)
	dt01_inst.send("cmd_gain"            , opno, voiceno, 2**16)
	dt01_inst.send("cmd_increment_porta" , opno, voiceno, 2**30)
	dt01_inst.send("cmd_increment"       , opno, voiceno, 2**22)
	dt01_inst.send("cmd_algorithm"       , opno, voiceno, 1)
	dt01_inst.send("cmd_fmdepth"         , opno, voiceno, 0)

	opno = 1
	dt01_inst.send("cmd_increment_porta", opno, voiceno, 2**30)
	dt01_inst.send("cmd_increment"      , opno, voiceno, 2**22)
	dt01_inst.send("cmd_fmdepth"        , opno, voiceno, 0)
	dt01_inst.send("cmd_algorithm"      , opno, voiceno, 2)
	
	dt01_inst.send("cmd_flushspi", 0, 0, 0)
	dt01_inst.send("cmd_shift"   , 0, 0, 0)
		