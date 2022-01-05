import os, json, sys
for filename in os.listdir(sys.argv[1]):
	if filename.endswith(".json"):
		print("converting " + filename)
		fullfilename = os.path.join(sys.argv[1], filename)
		with open(fullfilename, 'r') as f:
			patchTxt  = f.read()
			print(patchTxt)
			patchDict = json.loads(patchTxt)
		for operator in range(6):
			opDict = patchDict["Operator" + str(operator + 1)]
			opDict["Time (seconds)"] = []
			opDict["Level (unit interval)"] = []
			envDict = opDict["Envelope Generator"]
			for phase in range(4):
				opDict["Time (seconds)"]        += [envDict["Rate "  + str(phase + 1)] / 100.0]
				opDict["Level (unit interval)"] += [envDict["Level " + str(phase + 1)] / 100.0]
			del opDict["Envelope Generator"]
			patchDict["Operator" + str(operator + 1)] = opDict
			
		with open(fullfilename, 'w+') as f:
			f.write(json.dumps(patchDict, indent=4))