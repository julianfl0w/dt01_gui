import json
import sys
import os 

def splitJson(filename):
	with open(filename, 'r') as f:
		a = f.read()
	b = json.loads(a)
	outdir = filename.replace(".json", "")
	os.makedirs(outdir, exist_ok = True)
	for patch in b:
		with open(os.path.join(outdir, patch["Name"].replace(" ","_").replace(".","_") + ".json"), "w+") as f:
			f.write(json.dumps(patch, indent=4))
	
splitJson(sys.argv[1])
