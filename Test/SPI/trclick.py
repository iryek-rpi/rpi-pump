# Based on Arduino code from https://medium.com/electronza/arduino-4-20ma-current-loop-revisited-a-simpler-calibration-procedure-5b6f6be4dc80

import spidev
import lgpio
import time

CS_T = 20
CS_R = 21

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
chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(chip, CS_T, 1)
lgpio.gpio_claim_output(chip, CS_R, 0)
time.sleep(0.1)
lgpio.gpio_write(chip, CS_R, 1)

sd = spidev.SpiDev()
sd.open(0,0)
sd.max_speed_hz = 1000000
sd.mode = 0b00
sd.lsbfirst = False
sd.no_cs = True

def mcp3201_reset(c):
    lgpio.gpio_write(c, CS_R, 0)
    time.sleep(0.1)
    lgpio.gpio_write(c, CS_R, 1)
    time.sleep(0.1)

def cs(c, g, v):
    lgpio.gpio_write(c, g, v)
    time.sleep(0.1)
    #lgpio.gpio_write(c, g, 1)
    #time.sleep(0.1)

L = 801
H = 4030

def set_DAC(v):
    msb = (v >> 8) & 0x0F
    msb = msb | 0x30
    lsb = v & 0xFF
    
    cs(chip, CS_T,0)
    r = sd.xfer([msb, lsb])
    cs(chip, CS_T,1)
    print("set_DAC(",v,") returns:", r)

def get_ADC():
    mcp3201_reset(chip)
    cs(chip, CS_R, 0)
    #msb = spi_r.xfer([0])
    #lsb = spi_r.xfer([0])
    msb = sd.readbytes(4)
    #lsb = spi_r.readbytes(1)
    cs(chip, CS_R, 1)

    #result = ((msb & 0x1F) << 8) | lsb
    #return result >> 1
    #print("msb:", msb, " lsb:", lsb)
    print("msb:", msb)

def readADC_MSB():
    """
    Reads 2 bytes (byte_0 and byte_1) and converts the output code from the MSB-mode:
    byte_0 holds two ?? bits, the null bit, and the 5 MSB bits (B11-B07),
    byte_1 holds the remaning 7 MBS bits (B06-B00) and B01 from the LSB-mode, which has to be removed.
    """
    cs(chip, CS_R, 0)

    #bytes_received = self._spi.xfer2([0x00, 0x00])
    #bytes_received = sd.readbytes(2)
    bytes_received = sd.xfer2([0x00, 0x00])

    cs(chip, CS_R, 1)

    MSB_1 = bytes_received[1]
    MSB_1 = MSB_1 >> 1  # shift right 1 bit to remove B01 from the LSB mode
    MSB_0 = bytes_received[0] & 0b00011111  # mask the 2 unknown bits and the null bit
    MSB_0 = MSB_0 << 7  # shift left 7 bits (i.e. the first MSB 5 bits of 12 bits)
    return MSB_0 + MSB_1

def readADC_LSB():
    """
    Reads 4 bytes (byte_0 - byte_3) and converts the output code from LSB format mode:
    byte 1 holds B00 (shared by MSB- and LSB-modes) and B01,
    byte_2 holds the next 8 LSB bits (B03-B09), and
    byte 3, holds the remaining 2 LSB bits (B10-B11).
    """
    cs(chip, CS_R, 0)

    bytes_received = sd.xfer2([0x00, 0x00, 0x00, 0x00])

    cs(chip, CS_R, 1)

    LSB_0 = bytes_received[1] & 0b00000011  # mask the first 6 bits from the MSB mode
    LSB_0 = bin(LSB_0)[2:].zfill(2)  # converts to binary, cuts the "0b", include leading 0s
    LSB_1 = bytes_received[2]
    LSB_1 = bin(LSB_1)[2:].zfill(8)  # see above, include leading 0s (8 digits!)
    LSB_2 = bytes_received[3]
    LSB_2 = bin(LSB_2)[2:].zfill(8)
    LSB_2 = LSB_2[0:2]  # keep the first two digits
    LSB = LSB_0 + LSB_1 + LSB_2  # concatenate the three parts to the 12-digits string
    LSB = LSB[::-1]  # invert the resulting string
    return int(LSB, base=2)


def convert_to_voltage(adc_output, VREF=3.3):
    """
    Calculates analogue voltage from the digital output code (ranging from 0-4095)
    VREF could be adjusted here (standard uses the 3V3 rail from the Rpi)
    """
    return adc_output * (VREF / (2 ** 12 - 1))

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
    for i in range(8, 43):
        #n=int(input("Enter(0~4095):"))
        n = i*100
        set_DAC(n)
        time.sleep(0.1)
        #get_ADC()

        ADC_output_code = readADC_MSB()
        ADC_voltage = convert_to_voltage(ADC_output_code)
        print("MCP3201 output code (MSB-mode): %d" % ADC_output_code)
        print("MCP3201 voltage: %0.2f V" % ADC_voltage)   
        time.sleep(0.5)
'''
        ADC_output_code = readADC_LSB()
        ADC_voltage = convert_to_voltage(ADC_output_code)
        print("MCP3201 output code (LSB-mode): %d" % ADC_output_code)
        print("MCP3201 voltage: %0.2f V" % ADC_voltage)
        print()
        time.sleep(0.5)
'''
