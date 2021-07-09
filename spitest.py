import spidev
spi = spidev.SpiDev()

spi.open(1, 0)
to_send = [0x01, 0x02, 0x03]
while(1):
	spi.xfer(to_send)
	spi.readbytes(100)
