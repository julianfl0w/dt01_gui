
class Operator:
	def __init__(self, voice, index, dt01_inst):
		self.dt01_inst = dt01_inst
		self.index = index
		self.voice = voice
		self.stateDict = dict()
		
	def __unicode__(self):
		return "#" + str(self.index)
		
	def __str__(self):
		return "#" + str(self.index)

	def send(self, param, payload):
		stateDict[param] = payload
		self.dt01_inst.send(param, self.index, self.voice.index, payload)
	

class Voice:
	def __init__(self, index, dt01_inst):
		self.dt01_inst = dt01_inst
		self.index = index
		self.controlNote = None
		self.controlPatch = None
		self.sounding = False    
		self.defaultIncrement = 0
		self.indexInCluster = 0
		self.OPERATORCOUNT  = 8
		self.operators = []
		for opno in range(self.OPERATORCOUNT):
			self.operators += [Operator(self, opno, dt01_inst)]
		
	def __unicode__(self):
		return "#" + str(self.index)
		
	def __str__(self):
		return "#" + str(self.index)

	def send(self, param, mm_opno, payload):
		self.dt01_inst.send(param, mm_opno, self.index, payload)
	
	def sendFmMod(self):
		fmMod = 0
		for op in self.operators:
			mask  = 0x07 << 3*op.index
			newval= (0x07 & modno) << 3*op.index
			self.fmMod = (self.fmMod & ~mask) | newval	
			return self.fmMod
		