import os, json, sys
indir  = "dx7_patches"
outdir = "dtfm_patches"
from pathlib import Path
Path(outdir).mkdir(parents=True, exist_ok=True)
for category in os.listdir(indir):
	inCatDir = os.path.join(indir, category)
	outCatDir = os.path.join(outdir, category)
	Path(outCatDir).mkdir(parents=True, exist_ok=True)
	for filename in os.listdir(inCatDir):
		if filename.endswith(".json"):
			print("converting " + filename)
			infilename = os.path.join(inCatDir, filename)
			outfilename = os.path.join(outCatDir, filename)
			with open(infilename, 'r') as f:
				patchTxt  = f.read()
				#print(patchTxt)
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
				
			with open(outfilename, 'w+') as f:
				f.write(json.dumps(patchDict, indent=4))