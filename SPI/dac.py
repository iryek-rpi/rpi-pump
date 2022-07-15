#!/usr/bin/python3.4
# -*- coding: utf-8 -*-
# from https://github.com/flohwie/raspi-MCP3201

import lgpio
import spidev
from time import sleep

CE_R = 7
CE_T = 8

CSW0 = 26
CSW1 = 19
CSW2 = 13

CFLOW_PASS = 0
CFLOW_CPU = 1

#def set_current_flow(chip, cflow):
#  if cflow == CFLOW_PASS:
#    lgpio.gpio_write(chip, CSW0, 0)
#    lgpio.gpio_write(chip, CSW1, 0)
#    lgpio.gpio_write(chip, CSW2, 0)
#  else:
#    lgpio.gpio_write(chip, CSW0, 1)
#    lgpio.gpio_write(chip, CSW1, 1)
#    lgpio.gpio_write(chip, CSW2, 1)


def init_spi_rw(chip, speed=4800):
  #set_current_flow(chip=chip, cflow=CFLOW_CPU)

  lgpio.gpio_claim_output(chip, CE_T, 1)
  lgpio.gpio_claim_output(chip, CE_R, 1)
  sleep(0.1)

  spi = spidev.SpiDev()
  spi.open(bus=0, device=0)
  spi.max_speed_hz = speed
  spi.mode = 0
  spi.no_cs = True

  return spi


def writeDAC(chip, spi, v):
  msb = (v >> 8) & 0x0F
  msb = msb | 0x30
  lsb = v & 0xFF

  lgpio.gpio_write(chip, CE_T, 0)
  spi.xfer2([msb, lsb])
  lgpio.gpio_write(chip, CE_T, 1)
  print("set_DAC(", v, ")")


def readADC_MSB(chip, spi):
  """
    Reads 2 bytes (byte_0 and byte_1) and converts the output code from the MSB-mode:
    byte_0 holds two ?? bits, the null bit, and the 5 MSB bits (B11-B07),
    byte_1 holds the remaning 7 MBS bits (B06-B00) and B01 from the LSB-mode, which has to be removed.
    """
  lgpio.gpio_write(chip, CE_R, 0)
  bytes_received = spi.xfer2([0x00, 0x00])
  lgpio.gpio_write(chip, CE_R, 1)

  print("bytes_received:", bytes_received)
  print("Read:{} {}".format(bytes_received[0], bytes_received[1]))
  print("Read:{0:b} {1:b}".format(bytes_received[0], bytes_received[1]))

  MSB_1 = bytes_received[1]
  MSB_1 = MSB_1 >> 1  # shift right 1 bit to remove B01 from the LSB mode
  # mask the 2 unknown bits and the null bit
  MSB_0 = bytes_received[0] & 0b00011111
  # shift left 7 bits (i.e. the first MSB 5 bits of 12 bits)
  MSB_0 = MSB_0 << 7
  return MSB_0 + MSB_1


def readADC_LSB(chip, spi):
  """
    Reads 4 bytes (byte_0 - byte_3) and converts the output code from LSB format mode:
    byte 1 holds B00 (shared by MSB- and LSB-modes) and B01,
    byte_2 holds the next 8 LSB bits (B03-B09), and
    byte 3, holds the remaining 2 LSB bits (B10-B11).
    """
  lgpio.gpio_write(chip, CE_R, 0)
  bytes_received = spi.xfer2([0x00, 0x00, 0x00, 0x00])
  lgpio.gpio_write(chip, CE_R, 1)

  # mask the first 6 bits from the MSB mode
  LSB_0 = bytes_received[1] & 0b00000011
  # converts to binary, cuts the "0b", include leading 0s
  LSB_0 = bin(LSB_0)[2:].zfill(2)
  LSB_1 = bytes_received[2]
  # see above, include leading 0s (8 digits!)
  LSB_1 = bin(LSB_1)[2:].zfill(8)
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
  return adc_output * (VREF / (2**12 - 1))


if __name__ == '__main__':
  chip = lgpio.gpiochip_open(0)
  spi = init_spi_rw(chip, 4800)

  try:
    while True:
      for i in range(9, 43):

        ADC_output_code = readADC_MSB(chip, spi)
        ADC_voltage = convert_to_voltage(ADC_output_code)
        print("MCP3201 output code (MSB-mode): %d" % ADC_output_code)
        print("MCP3201 voltage: %0.2f V" % ADC_voltage)
        print("")
        sleep(0.1)  # wait minimum of 100 ms between ADC measurements

        writeDAC(chip, spi, i * 100)
        sleep(1)

  except (KeyboardInterrupt):
    print('\n', "Exit on Ctrl-C: Good bye!")

  except:
    print("Other error or exception occurred!")
    raise

  finally:
    print()
