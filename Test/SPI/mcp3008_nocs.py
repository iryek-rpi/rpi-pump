# https://m.blog.naver.com/PostView.naver?isHttpsRedirect=true&blogId=specialist0&logNo=221052983910

import spidev, time
import lgpio

spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz = 1000000

CE = 21
chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(chip, CE, 1)
spi.no_cs = True

def analog_read(channel):
    lgpio.gpio_write(chip, CE, 0)
    r = spi.xfer2([1, (0x08+channel)<<4, 0])
    time.sleep(1.5)
    lgpio.gpio_write(chip, CE, 1)

    adc_out = ((r[1]&0x03)<<8) + r[2]
    return adc_out
 

while True:
    adc = analog_read(1)
    voltage = adc*3.3/1023
    print("\nADC = %s(%d)  Voltage = %.3fV" % (hex(adc), adc, voltage))
    print("SpiDev.mode:{}".format(spi.mode))
    time.sleep(0.5)
