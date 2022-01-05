import zmq
import time
import rtmidi
import mido

midiout = rtmidi.MidiOut()
available_ports = midiout.get_ports()

if available_ports:
    midiout.open_port(0)
else:
    midiout.open_virtual_port("My virtual output")

with midiout:
    note_on = [0x90, 60, 112] # channel 1, middle C, velocity 112
    note_off = [0x80, 60, 0]
    midiout.send_message(note_on)
    time.sleep(0.5)
    midiout.send_message(note_off)
    time.sleep(0.1)


context = zmq.Context()
self.socket = context.socket(zmq.PUB)
self.socket.bind("tcp://*:5556")

from pynput.keyboard import Key, Listener

def on_press(key):
	sendString = '{0} pressed'.format(key)
	print(sendString)
	instance.app_inst.socket.send_string(sendString)

def on_release(key):
	sendString = '{0} release'.format(key)
	print(sendString)
	instance.app_inst.socket.send_string(sendString)
	#if key == Key.esc:
	#	# Stop listener
	#	return False

# Collect events until released
with Listener(
		on_press=on_press,
		on_release=on_release) as listener:
	listener.join()
	
del midiout