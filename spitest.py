import spidev
spi = spidev.SpiDev()

spi.open(1, 0)

speed = 20000000
spi.max_speed_hz=speed

while(1):
    to_send = [0x01, 0x02, 0x03]
    spi.xfer2(to_send)
    #spi.readbytes(100)
