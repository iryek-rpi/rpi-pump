# https://m.blog.naver.com/PostView.naver?isHttpsRedirect=true&blogId=specialist0&logNo=221052983910

import spidev, time

spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz = 1000000

def analog_read(channel):
    r = spi.xfer2([1, (0x08+channel)<<4, 0])

    adc_out = ((r[1]&0x03)<<8) + r[2]
    return adc_out
 

while True:
    adc = analog_read(1)
    voltage = adc*3.3/1023
    print("ADC = %s(%d)  Voltage = %.3fV" % (hex(adc), adc, voltage))
    time.sleep(0.5)
