
def noteToFreq(note):
	a = 440.0 #frequency of A (coomon value is 440Hz)
	return (a / 32) * (2 ** ((note - 9) / 12))


class Note:
	def __init__(self, index):
		self.index  = index
		self.controlledVoices = []
		self.velocity = 0
		self.held  = False
		self.polyAftertouch = 0
		self.msg  = None
		self.defaultIncrement = 2**32 * (noteToFreq(index) / 96000.0)
