import spidev
spi = spidev.SpiDev()

spi.open(1, 1)

speed = 2000000
spi.max_speed_hz=speed

for i in range(1024):
	spi.xfer2([0xFF, 0x00, 0xFF, 0x00]) 
spi.close()
