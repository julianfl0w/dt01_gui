from dt01 import *
import sys

fpga_interface_inst = dt01()

def init():
	for voice in range(32):
		#paramName, mm_opno,  voiceno,  payload
		fpga_interface_inst.send("cmd_static"       , 0b11000000, voice, 0)
		fpga_interface_inst.send("cmd_baseincrement", 2**8, voice, 0)
		fpga_interface_inst.send("cmd_sounding"     , 0b00000001, voice, 0)
		fpga_interface_inst.send("cmd_fm_algo"      , 0, voice, 0o77777777)
		fpga_interface_inst.send("cmd_am_algo"      , 0, voice, 0o00000000)
		fpga_interface_inst.send("cmd_fbgain"       , 0, voice, 0)
		fpga_interface_inst.send("cmd_fbsrc"        , 0, voice, 0)
		for channel in range(2):
			fpga_interface_inst.send("cmd_channelgain", voice, channel, 2**16)
		for operator in range(8):
			fpga_interface_inst.send("cmd_env"            , voice, operator, 0)
			fpga_interface_inst.send("cmd_env_porta"      , voice, operator, 2**10)
			fpga_interface_inst.send("cmd_envexp"         , voice, operator, 0x01)
			
			if operator < 6:
				fpga_interface_inst.send("cmd_increment"      , 2**16 * self.paramName2Real["increment"]) # * self.paramName2Real["increment"]
			else:
				fpga_interface_inst.send("cmd_increment"      , 2**3 * self.paramName2Real["increment"]) # * self.paramName2Real["increment"]
					
			fpga_interface_inst.send("cmd_increment_porta", voice, operator, 2**16)
			fpga_interface_inst.send("cmd_incexp"         , voice, operator, 2**16)
			
	fpga_interface_inst.send("cmd_flushspi"       ]  = 120
	fpga_interface_inst.send("cmd_passthrough"    ]  = 121
	fpga_interface_inst.send("cmd_shift"          ]  = 122
	fpga_interface_inst.send("cmd_env_clkdiv"     ]  = 123 # turn this back to 123

if sys.argv[1] == vibrado:
	fpga_interface_inst.send(paramName, mm_opno,  voiceno,  payload):