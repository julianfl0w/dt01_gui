
class Operator:
	def __init__(self, voice, index, dt01_inst):
		self.dt01_inst = dt01_inst
		self.index = index
		self.voice = voice
		self.stateDict = dict()
		self.fmmod_selector = 0
	
	def setGainPorta(self)     : self.send("cmd_gain_porta"     , 2**4                                                        )
	def setGain(self)          : self.send("cmd_gain"           , self.voice.note.velocity*(2**16)/128.0                      )
	def setIncrement(self)     : self.send("cmd_increment"      , self.voice.patch.pitchwheel * self.voice.note.defaultIncrement * (2 ** (self.voice.indexInCluster - (self.voice.patch.voicesPerNote-1)/2)) * (1 + self.voice.patch.aftertouch/128.0))
	def setIncrementPorta(self): self.send("cmd_increment_porta", 2**22*(self.voice.patch.control[4]/128.0)                          )
	def setFMDepth(self)       : self.send("cmd_fmdepth"        , 0                                                            ) 
	def setFMMod_selector(self): self.send("cmd_fmmod_selector" , self.voice.getFmMod())
	def setIncExp(self)        : self.send("cmd_incexp"         , 1                                                            )
	def setGainexp(self)       : self.send("cmd_gainexp"        , 1                                                            )
	
	def setAll(self):
		self.setGainPorta()     
		self.setGain()          
		self.setIncrement()     
		self.setIncrementPorta()
		self.setFMDepth()       
		self.setFMMod_selector()
		self.setIncExp()        
		self.setGainexp()       
		
	
	def __unicode__(self):
		return "#" + str(self.index)
		
	def __str__(self):
		return "#" + str(self.index)

	def send(self, param, payload):
		# only write the thing if it changed
		#if payload != self.stateDict.get(param):
		if  True:
			self.stateDict[param] = payload
			self.dt01_inst.send(param, self.index, self.voice.index, payload)
	

class Voice:
	class Operator0(Operator):	
		def setFMDepth(self)       : self.send("cmd_fmdepth"        ,  payload = int(2**14 * (self.voice.patch.control[1]/128.0)))
		def __init__(self, voice, index, dt01_inst):
			super().__init__(voice, index, dt01_inst)
			self.fmmod_selector = 1
	class Operator1(Operator):	
		def __init__(self, voice, index, dt01_inst):
			super().__init__(voice, index, dt01_inst)
	class Operator2(Operator):	
		def __init__(self, voice, index, dt01_inst):
			super().__init__(voice, index, dt01_inst)
	class Operator3(Operator):	
		def __init__(self, voice, index, dt01_inst):
			super().__init__(voice, index, dt01_inst)
	class Operator4(Operator):	
		def __init__(self, voice, index, dt01_inst):
			super().__init__(voice, index, dt01_inst)
	class Operator5(Operator):	
		def __init__(self, voice, index, dt01_inst):
			super().__init__(voice, index, dt01_inst)
	class Operator6(Operator):	
		def __init__(self, voice, index, dt01_inst):
			super().__init__(voice, index, dt01_inst)
	class Operator7(Operator):	
		def __init__(self, voice, index, dt01_inst):
			super().__init__(voice, index, dt01_inst)


	def __init__(self, index, dt01_inst):
		self.dt01_inst = dt01_inst
		self.index = index
		self.note = None
		self.expressionDict = dict()
		self.patch  = None
		self.sounding = False    
		self.defaultIncrement = 0
		self.indexInCluster = 0
		self.OPERATORCOUNT  = 2
		self.stateDict = dict()
		self.operators = []
		self.operators += [self.Operator0(self, 0, dt01_inst)]
		self.operators += [self.Operator1(self, 1, dt01_inst)]
		self.operators += [self.Operator2(self, 2, dt01_inst)]
		self.operators += [self.Operator3(self, 3, dt01_inst)]
		self.operators += [self.Operator4(self, 4, dt01_inst)]
		self.operators += [self.Operator5(self, 5, dt01_inst)]
		self.operators += [self.Operator6(self, 6, dt01_inst)]
		self.operators += [self.Operator7(self, 7, dt01_inst)]
			
	def setMastergainRight(self)  : self.send("cmd_mastergain_right", 2**16)
	def setMastergainLeft(self)   : self.send("cmd_mastergain_left" , 2**16)
	def setAll(self):
		self.setMastergainRight() 
		self.setMastergainLeft()  
		for operator in self.operators:
			operator.setAll()
			
		#elif command == "cmd_increment"         :
		#	payload = 2**22
		#	if operator == 0:
		#		payload = 
		#	else:
		#		payload = self.pitchwheel * voice.note.defaultIncrement * (2**int((self.control[3] -64) / 16)) * (1 + self.aftertouch/128.0) * (2 ** (voice.indexInCluster - (self.voicesPerNote-1)/2))
		
			
		
	def __unicode__(self):
		return "#" + str(self.index)
		
	def __str__(self):
		return "#" + str(self.index)

	def send(self, param, payload):
		#if payload != self.stateDict.get(param):
		if  True:
			self.stateDict[param] = payload
			self.dt01_inst.send(param, 0, self.index, payload)
	
	def getFmMod(self):
		fmMod = 0
		for op in self.operators:
			mask  = 0x07 << 3*op.index
			newval= (0x07 & op.fmmod_selector) << 3*op.index
			fmMod = (fmMod & ~mask) | newval	
		#self.send("cmd_fmmod", 0, fmMod):
		return fmMod