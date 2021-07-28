cmdDict = dict()

cmdDict["cmd_ENVELOPE_MIDnEND" ] = 1  
cmdDict["cmd_ENVELOPE_ENV_SPEED"] = 3  
cmdDict["cmd_PBEND_MIDnEND"    ] = 16 
cmdDict["cmd_PBEND_ENV_SPEED"  ] = 18 
cmdDict["cmd_HWIDTH_3TARGETS"  ] = 32 
cmdDict["cmd_HWIDTH_ENV_SPEED" ] = 34 
cmdDict["cmd_NFILTER_3TARGETS" ] = 48 
cmdDict["cmd_NFILTER_ENV_SPEED"] = 50 
cmdDict["cmd_GFILTER_3TARGETS" ] = 64 
cmdDict["cmd_GFILTER_ENV_SPEED"] = 67 
cmdDict["cmd_fmdepth"          ] = 68 
cmdDict["cmd_fmmod_selector"   ] = 69 
cmdDict["cmd_ammod_selector"   ] = 71 
cmdDict["cmd_HARMONIC_WIDTH"   ] = 80 
cmdDict["cmd_HARMONIC_WIDTH_INV"] = 81 
cmdDict["cmd_HARMONIC_BASENOTE"] = 82 
cmdDict["cmd_HARMONIC_ENABLE"  ] = 83 
cmdDict["cmd_pitchshiftdepth"  ] = 87 
cmdDict["cmd_centsinc"         ] = 88 
cmdDict["cmd_gain"             ] = 90
cmdDict["cmd_gain_porta"       ] = 91
cmdDict["cmd_increment"        ] = 92
cmdDict["cmd_increment_porta"  ] = 93
cmdDict["cmd_mastergain_right" ] = 95
cmdDict["cmd_mastergain_left"  ] = 96
cmdDict["cmd_incexp"           ] = 97
cmdDict["cmd_gainexp"] = 98
cmdDict["cmd_env_clkdiv"] = 99
cmdDict["cmd_flushspi"] = 120
cmdDict["cmd_passthrough"] = 121
cmdDict["cmd_shift"] = 122

maxSpiSpeed = 20000000
POLYPHONYCOUNT = 512
OPERATORCOUNT  = 8

def format_command_real(mm_paramno = 0, noteno = 0,  payload = 0):
	payload = payload*(2**16)
	payload = struct.pack(">I", int(payload))
	payload = [mm_paramno, 0, 0, noteno] + [int(i) for i in payload]
	#print([hex(p) for p in payload])
	return payload
	
def format_command_int(mm_paramno = 0, mm_opno = 0,  noteno = 0,  payload = 0):
	payload = struct.pack(">I", int(payload))
	payload = [mm_paramno, mm_opno, 0, noteno] + [int(i) for i in payload]
	print([hex(p) for p in payload])
	return payload
	
def format_command_3bezier_targets(mm_paramno = 0, noteno = 0,  bt0 = 0, bt1 = 0, bt2 = 0):
	payload = struct.pack(">I", (int(bt0*(2**28)) & 0x3FF00000) + (int(bt1*(2**18)) & 0x000FFC00) + (int(bt2*(2**8)) & 0x000003FF))
	payload = [mm_paramno, 0, 0, noteno] + [int(p) for p in payload]
	#print([hex(p) for p in payload])
	return payload
	