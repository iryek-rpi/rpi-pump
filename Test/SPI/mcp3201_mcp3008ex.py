#!/usr/bin/python3.4
# -*- coding: utf-8 -*-
# from https://github.com/flohwie/raspi-MCP3201

import spidev
from time import sleep

import lgpio
CE_3008 = 21
CE_T = 20
CE_R = 16

chip = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(chip,CE_T,1)
lgpio.gpio_claim_output(chip,CE_3008,1)
lgpio.gpio_claim_output(chip,CE_R,1)
sleep(0.1)
lgpio.gpio_write(chip,CE_R,0)
sleep(0.1)
lgpio.gpio_write(chip,CE_R,1)
sleep(0.1)

def writeDAC(v):
    msb = (v >> 8) & 0x0F
    msb = msb | 0x30
    lsb = v & 0xFF
    
    lgpio.gpio_write(chip, CE_T, 0)
    spi.xfer2([msb, lsb])
    lgpio.gpio_write(chip, CE_T, 1)
    #lgpio.gpio_claim_output(chip, CE_T, 1)
    print("\nset_DAC({}=[{},{}])".format(v, msb, lsb))

def read_3008(channel, ce):
    lgpio.gpio_write(chip, ce, 0)
    r = spi.xfer2([1, (0x08+channel)<<4, 0])
    lgpio.gpio_write(chip, ce, 1)

    adc_out = ((r[1]&0x03)<<8) + r[2]
    return adc_out

def readADC_MSB(ce):
    """
    Reads 2 bytes (byte_0 and byte_1) and converts the output code from the MSB-mode:
    byte_0 holds two ?? bits, the null bit, and the 5 MSB bits (B11-B07),
    byte_1 holds the remaning 7 MBS bits (B06-B00) and B01 from the LSB-mode, which has to be removed.
    """
    lgpio.gpio_write(chip, ce, 0)
    bytes_received = spi.xfer2([0x00, 0x00])
    lgpio.gpio_write(chip, ce, 1)
    sleep(0.1)
    print("\nMCP3201 output:{}".format(bytes_received))

    MSB_1 = bytes_received[1]
    MSB_1 = MSB_1 >> 1  # shift right 1 bit to remove B01 from the LSB mode
    MSB_0 = bytes_received[0] & 0b00011111  # mask the 2 unknown bits and the null bit
    MSB_0 = MSB_0 << 7  # shift left 7 bits (i.e. the first MSB 5 bits of 12 bits)
    return MSB_0 + MSB_1

def convert_to_voltage(adc_output, VREF=3.3):
    """
    Calculates analogue voltage from the digital output code (ranging from 0-4095)
    VREF could be adjusted here (standard uses the 3V3 rail from the Rpi)
    """
    return adc_output * (VREF / (2 ** 12 - 1))

if __name__ == '__main__':
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 976000
    spi.no_cs = True    
        
    try:
        while True:
            for i in range(9,43):

                #adc = read_3008(1,CE_3008)
                #voltage = adc*3.3/1023
                #print("\n================")
                #print("MCP3008 = {}({}) Voltage = {:.3f}V".format(hex(adc), adc, voltage))

                #sleep(2)

                ADC_output_code = readADC_MSB(CE_R)
                ADC_voltage = convert_to_voltage(ADC_output_code)
                print("MCP3201 output code (MSB-mode): {} Voltage: {:0.2f}V".format(ADC_output_code, ADC_voltage))
            
                sleep(2)  # wait minimum of 100 ms between ADC measurements

                #writeDAC(i*100)
                #sleep(2)


    except (KeyboardInterrupt):
        print('\n', "Exit on Ctrl-C: Good bye!")

    except:
        print("Other error or exception occurred!")
        raise

    finally:
        print()
