class Voice:
	def __init__(self, index, dt01_inst):
		self.dt01_inst = dt01_inst
		self.index = index
		self.controlNote = None
		self.controlPatch = None
		self.sounding = False    
		self.fmMod = 0
		self.defaultIncrement = 0
		self.indexInCluster = 0
		
	def __unicode__(self):
		return "#" + str(self.index)
		
	def __str__(self):
		return "#" + str(self.index)

	def send(self, param, mm_opno, payload):
		self.dt01_inst.send(param, mm_opno, self.index, payload)
	
	def getFmMod(self, opno, modno):
		mask  = 0x07 << 3*opno
		newval= (0x07 & modno) << 3*opno
		self.fmMod = (self.fmMod & ~mask) | newval	
		return self.fmMod
		