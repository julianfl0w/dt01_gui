import RPi.GPIO as GPIO
import time 

SCLK1 = 21
MOSI = 20

GPIO.setmode(GPIO.BCM)
GPIO.setup(SCLK1, GPIO.OUT)
GPIO.setup(MOSI, GPIO.OUT)
try:
	while(1):
		#print("setting 1")
		GPIO.output(SCLK1, 1)
		GPIO.output(MOSI, 1)
		time.sleep(.01)
		#print("setting 0")
		GPIO.output(SCLK1, 0)
		GPIO.output(MOSI, 0)
		time.sleep(.01)


except:
	GPIO.cleanup()
