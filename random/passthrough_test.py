cmd_ENVELOPE_MIDnEND   = 1
cmd_ENVELOPE_ENV_SPEED = 3

cmd_PBEND_MIDnEND	  = 16
cmd_PBEND_ENV_SPEED	= 18

cmd_HWIDTH_3TARGETS	= 32
cmd_HWIDTH_ENV_SPEED   = 34

cmd_NFILTER_3TARGETS   = 48
cmd_NFILTER_ENV_SPEED  = 50
			 
cmd_GFILTER_3TARGETS   = 64
cmd_GFILTER_ENV_SPEED  = 67

cmd_HARMONIC_WIDTH	 = 80
cmd_HARMONIC_WIDTH_INV = 81
cmd_HARMONIC_BASENOTE  = 82
cmd_HARMONIC_ENABLE	= 83
cmd_fmfactor		   = 85
cmd_fmdepth			= 86
cmd_pitchshiftdepth	= 87
cmd_centsinc		   = 88
cmd_master_gain		= 89
cmd_gain			   = 90
cmd_gain_porta		 = 91
cmd_increment		  = 92
cmd_increment_porta	= 93
cmd_increment_adj   = 94
cmd_mod_atten	   = 95
cmd_mod_selector	= 96
cmd_flushspi    = 120
cmd_passthrough = 121

HWIDTH = 1 

import struct
import sys

def format_command_real(mm_paramno = 0, mm_noteno = 0,  payload = 0):
	payload = payload*(2**16)
	payload = struct.pack(">I", int(payload))
	payload = [mm_paramno, 0, 0, mm_noteno] + [int(i) for i in payload]
	print([hex(p) for p in payload])
	return payload
	
def format_command_int(mm_paramno = 0, mm_opno = 0, mm_noteno = 0,  payload = 0):
	payload = struct.pack(">I", int(payload))
	payload = [mm_paramno, 0, mm_opno, mm_noteno] + [int(i) for i in payload]
	print([hex(p) for p in payload])
	return payload
	
def format_command_int_op(mm_paramno = 0, mm_opno = 0,  mm_noteno = 0,  payload = 0):
	payload = struct.pack(">I", int(payload))
	payload = [mm_paramno, mm_opno, 0, mm_noteno] + [int(i) for i in payload]
	print([hex(p) for p in payload])
	return payload
	
def format_command_3bezier_targets(mm_paramno = 0, mm_noteno = 0,  bt0 = 0, bt1 = 0, bt2 = 0):
	payload = struct.pack(">I", (int(bt0*(2**28)) & 0x3FF00000) + (int(bt1*(2**18)) & 0x000FFC00) + (int(bt2*(2**8)) & 0x000003FF))
	payload = [mm_paramno, 0, 0, mm_noteno] + [int(p) for p in payload]
	print([hex(p) for p in payload])
	return payload
	
import spidev
spi = spidev.SpiDev()

spi.open(1, 0)

speed = 2000000
spi.max_speed_hz=speed
mm_noteno = 0

spi.xfer2(format_command_int(cmd_master_gain, 0, 0, 0)) # 0 for passthrough
spi.xfer2(format_command_int(cmd_master_gain, 0, 1, 1)) # 1 for passthrough

# Gain
spi.xfer2(format_command_int(cmd_gain_porta, 0, mm_noteno, 2**16)) 
spi.xfer2(format_command_int(cmd_gain      , 0, mm_noteno, 2**16)) 

# Frequency
spi.xfer2(format_command_int(cmd_increment_porta, 0, mm_noteno, 2**30)) 
spi.xfer2(format_command_int(cmd_increment      , 0, mm_noteno, 1)) # 32 bit incrementer 

 
# turn off flush
spi.xfer2(format_command_int(cmd_flushspi, 0, 0, 0)) 
spi.xfer2(format_command_int(cmd_passthrough, 0, 0, 1)) 

#while(1):
#	spi.xfer2(format_command_int(cmd_flushspi, 0, 0, 1)) 
	