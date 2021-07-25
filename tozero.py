ENVELOPE_MIDnEND   = 1
ENVELOPE_ENV_SPEED = 3
                        
PBEND_MIDnEND      = 16
PBEND_ENV_SPEED    = 18
                        
HWIDTH_3TARGETS    = 32
HWIDTH_ENV_SPEED   = 34
                         
NFILTER_3TARGETS   = 48
NFILTER_ENV_SPEED  = 50
                                         
GFILTER_3TARGETS   = 64
GFILTER_ENV_SPEED  = 67
    
HARMONIC_WIDTH     = 80
HARMONIC_WIDTH_INV = 81
HARMONIC_BASENOTE  = 82
HARMONIC_ENABLE    = 83
fmfactor        = 85
fmdepth         = 86
pitchshiftdepth = 87
centsinc        = 88
gain            = 89

HWIDTH = 1 

import struct

def format_command(mm_noteno = 0, mm_paramno = 0, mm_additional0 = 0, mm_additional1 = 0, payload = 0):
    payload = payload*(2**16)
    payload = struct.pack(">I", int(payload))
    payload = [mm_noteno, mm_paramno, mm_additional0, mm_additional1] + [int(i) for i in payload]
    print([hex(p) for p in payload])
    return payload
    
def format_command_int(mm_noteno = 0, mm_paramno = 0, mm_additional0 = 0, mm_additional1 = 0, payload = 0):
    payload = struct.pack(">I", int(payload))
    payload = [mm_noteno, mm_paramno, mm_additional0, mm_additional1] + [int(i) for i in payload]
    print([hex(p) for p in payload])
    return payload
    
def format_command_3bezier_targets(mm_noteno = 0, mm_paramno = 0, mm_additional0 = 0, mm_additional1 = 0, bt0 = 0, bt1 = 0, bt2 = 0):
    payload = struct.pack(">I", (int(bt0*(2**28)) & 0x3FF00000) + (int(bt1*(2**18)) & 0x000FFC00) + (int(bt2*(2**8)) & 0x000003FF))
    payload = [mm_noteno, mm_paramno, mm_additional0, mm_additional1] + [int(p) for p in payload]
    print([hex(p) for p in payload])
    return payload
    
import spidev
spi = spidev.SpiDev()

spi.open(1, 0)

speed = 2000000
spi.max_speed_hz=speed

while(1):

    mm_noteno = 0
    #for i in range(25):
    #    #payload = [0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55]
    #    payload = [0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00]
    #    print([hex(p) for p in payload])
    #    spi.xfer2(payload) 
    #die

    # GFILTER!
    # passthrough control options
    # write patchage speed at 0
    spi.xfer2( format_command(mm_noteno, GFILTER_ENV_SPEED, 0, 0, 0)) 
    spi.xfer2( format_command_3bezier_targets(mm_noteno, GFILTER_3TARGETS, 0, 0, 0.0, 0.0, 0.0)) 

    # PITCH BEND         
    # set bezier triple
    # write patchage speed at 0
    #spi.xfer2( format_command(mm_noteno, PBEND_ENV_SPEED, 0, 0, 0.5 / 32)) 
    #spi.xfer2( format_command_bezier_MIDnEND(mm_noteno, PBEND_MIDnEND, 0, 0, 0.5, 1.0))   

    # Harmonic width effect!
    # write patchage speed at 0
    spi.xfer2( format_command(mm_noteno, HWIDTH_ENV_SPEED, 0, 0, 0))
    spi.xfer2( format_command_3bezier_targets(mm_noteno, HWIDTH_3TARGETS, 0, 0, 0.0, 0.0, 0.0))  

    # NFILTER!
    # write patchage speed at 0
    spi.xfer2( format_command(mm_noteno, NFILTER_ENV_SPEED, 0, 0, 0)) 
    spi.xfer2( format_command_3bezier_targets(mm_noteno, NFILTER_3TARGETS, 0, 0, 0.0, 0.0, 0.0)) 
            
    # harmonic parameters
    spi.xfer2( format_command_int(mm_noteno, HARMONIC_WIDTH,    0, 0, 0)) 
    spi.xfer2( format_command    (mm_noteno, HARMONIC_WIDTH_INV,0, 0, 0)) 
    spi.xfer2( format_command_int(mm_noteno, HARMONIC_BASENOTE, 0, 0, 0))
    #spi.xfer2( format_command_int(mm_noteno, HARMONIC_ENABLE,   0, 0, 0)) 
    spi.xfer2( format_command_int(mm_noteno, centsinc, 0, 0, 0))
    spi.xfer2( format_command    (mm_noteno, HARMONIC_WIDTH_INV,0, 0, 0)) 
	
    spi.xfer2( format_command_int(0, gain,0, 0, 1)) 
    spi.xfer2( format_command_int(1, gain,1, 1, 1)) 
      
    #spi.readbytes(100)
    
    break