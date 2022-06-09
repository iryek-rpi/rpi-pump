# Based on Arduino code from https://medium.com/electronza/arduino-4-20ma-current-loop-revisited-a-simpler-calibration-procedure-5b6f6be4dc80

import spidev
import lgpio
import time

spi_t = spidev.SpiDev()
spi_t.open(0, 0)
#spi_t.max_speed_hz = 1000000 #1MHz
spi_t.max_speed_hz = 4800 #1MHz
spi_t.mode = 0b00
spi_t.lsbfirst = False
spi_t.no_cs = True

''' Resetting MCP3201
 * From MCP3201 datasheet: If the device was powered up with the CS pin low, 
 * it must be brought high and back low to initiate communication.
 * The device will begin to sample the analog input on the first rising edge 
 * after CS goes low. 
'''
# pinMode (ADC_CS, OUTPUT);
# digitalWrite(ADC_CS, 0);
# delay(100);
# digitalWrite(ADC_CS, 1);

CE_T = 20

c = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(c, CE_T, 1)
time.sleep(0.1)

'''
spi_r = spidev.SpiDev()
spi_r.open(0, 1)
spi_r.max_speed_hz = 1000000 #1MHz
spi_r.mode = 0b01
spi_r.lsbfirst = False
'''

#spi_r.cshigh = False
#time.sleep(0.1)
#spi_r.cshigh = True
#time.sleep(0.1)

L = 801
H = 4030

def set_DAC(v):
    msb = (v >> 8) & 0x0F
    msb = msb | 0x30
    lsb = v & 0xFF

    lgpio.gpio_write(c, CE_T, 0)
    time.sleep(0.1)
    r = spi_t.xfer([msb, lsb])
    time.sleep(0.1)
    lgpio.gpio_write(c, CE_T, 1)
    print("set_DAC(",v,") returns:", r)

def get_ADC():
    #msb = spi_r.xfer([0])
    #lsb = spi_r.xfer([0])
    msb = spi_r.readbytes(1)
    lsb = spi_r.readbytes(1)

    #result = ((msb & 0x1F) << 8) | lsb
    #return result >> 1
    return msb, lsb


def map420(v, flow, fhigh, tlow, thigh):
    if v < flow:
        return False, v
    if v > fhigh:
        return False, v
     
    return True, int((v - flow)*(thigh-tlow) / (fhigh-flow)+tlow)

# https://www.theamplituhedron.com/articles/How-to-replicate-the-Arduino-map-function-in-Python-for-Raspberry-Pi/
#  Prominent Arduino map function :)
def _map(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)
	
# TEST
y = _map(25, 1, 50, 50, 1)
#print(y)

while True:
    n=int(input("Enter(0~4095):"))
    set_DAC(n)
    time.sleep(0.25)
    #m,l=get_ADC()
    #print("msb:",m, " lsb:",l)
    #time.sleep(0.25)
