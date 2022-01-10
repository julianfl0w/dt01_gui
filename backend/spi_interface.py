import spidev
#maxSpiSpeed = 120000000
maxSpiSpeed = 100000000
maxSpiSpeed = 45000000
spi = spidev.SpiDev()
spi.open(1, 0)
spi.max_speed_hz=maxSpiSpeed

def send(payload):
	retval = spi.xfer2(payload)
	return retval