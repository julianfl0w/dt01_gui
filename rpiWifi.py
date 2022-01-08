# imports
import platform
import os
import sys
import platform
import subprocess
import json

def runCommand(cmd):
	return subprocess.check_output([cmd], shell=True).decode(encoding='UTF-8')

def RPIConnectToWifi(ESSID, passwd):
	# DO NOT CHANGE FORMATTING OF THIS STRING!
	wpa_sup = """ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
  update_config=1
  country=US
  
"""
	# Connect using standard RPI tools
	network_part = runCommand("wpa_passphrase " + ESSID + " " + passwd)
	network_part = "\n".join([network_part.split("\n")[i] for i in [0,1,3,4]])
	print("connecting to " + ESSID)
	with open("temp.txt", "w+") as f:
		f.write(wpa_sup + network_part)
	command = "sudo cp temp.txt /etc/wpa_supplicant/wpa_supplicant.conf"
	print(command)
	os.system(command)
	os.system("wpa_cli -i wlan0 reconfigure &")

def RPIGetAvailableNetworks():

	SSID_txt = runCommand("sudo iwlist wlan0 scan")
	print(SSID_txt)
	allHosts = []
	ssidDict = None
	ssidLines = SSID_txt.split("\n")
	for i, line in enumerate(ssidLines):

		# add dict to master list if final line
		if ssidDict != None:
			if i+1 < len(ssidLines):
				if ssidLines[i+1].startswith("          Cell"):
					allHosts += [ssidDict]
			elif i+1 == len(ssidLines):
				allHosts += [ssidDict]

		# Cell marks beginning of interface
		if line.startswith("          Cell"):
			ssidDict = {}
			ssidDict["ADDRESS"] = line.split("Address:")[1].strip()
		else:
			try:
				key, value = [s.strip() for s in line.split(":")]
				ssidDict[key] = value
				ssidDict[key] = float(value)
			except:
				pass
			
	print(json.dumps(allHosts, indent = 4))
	allHosts = [hostDict for hostDict in allHosts if hostDict.get("ESSID").replace("\"","").strip() != "" ] # remove empty string elements
	allHosts = sorted(allHosts, key = lambda i: i['ESSID'])
	#rint(json.dumps(allHosts, indent = 4))
	return allHosts
	
